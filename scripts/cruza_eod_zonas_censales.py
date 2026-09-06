# -*- coding: utf-8 -*-
"""
Lleva los viajes en bicicleta de la EOD a la zonificacion censal del visor.

--------------------------------------------------------------------------
Por que hace falta un cruce, y por que a nivel de zona
--------------------------------------------------------------------------
La EOD publica sus resultados en su propia zonificacion, distinta de la censal.
Mostrar ambas en el mismo mapa sin traducirlas seria mezclar dos particiones del
territorio como si fueran una.

En la base homologada del repositorio el hogar NO trae coordenada: la geografia
mas fina disponible es la zona EOD. Aunque la trajera, desagregar por debajo de
la zona daria precision falsa, porque los factores de expansion de una EOD estan
calibrados justamente a nivel de zona. De modo que la zona es el piso
metodologico, no una limitacion del archivo.

--------------------------------------------------------------------------
Como se reparte
--------------------------------------------------------------------------
Se intersectan los poligonos de zona EOD con los de zona censal y los viajes se
reparten en proporcion a la POBLACION de cada trozo, no a su superficie. Repartir
por area supondria que la gente se distribuye pareja dentro de la zona, y en una
zona EOD que mezcla un barrio denso con un paño agricola eso manda viajes al
potrero. La poblacion por zona censal ya esta calculada en `zona_demanda`.

--------------------------------------------------------------------------
Por que viaja tambien el tamaño de la muestra
--------------------------------------------------------------------------
Los viajes que reparte este cruce son cifras EXPANDIDAS. En el Gran Concepcion
2015 hay 800 viajes en bicicleta encuestados repartidos en 359 zonas de origen
—mediana de 2 por zona— y el factor medio de expansion es 42,8. A ese grano un
solo encuestado pinta una zona entera, y el mapa termina mostrando donde cayo
la muestra en vez de donde se pedalea.

La prueba: la razon entre viajes EOD y ciclistas del Censo deberia ser mas o
menos constante entre zonas, porque mide viajes por ciclista. En el agregado
del Gran Concepcion da 4,25, que es plausible; por zona va de 0,56 (p10) a
12,9 (p90), con maximo 57,5. Esa dispersion es ruido de muestreo, no
comportamiento.

Por eso se arrastra `n`, el numero de viajes ENCUESTADOS, hasta la zona
censal: sin el no hay forma de saber que parte del mapa se puede pintar.

Salida: agrega a `data/analisis/zona_demanda.parquet` las columnas
  eod_bici_gen   viajes en bicicleta generados (origen) en la zona censal
  eod_bici_atr   viajes en bicicleta atraidos (destino)
  eod_n_gen      viajes ENCUESTADOS detras de `eod_bici_gen` (valor esperado)
  eod_n_atr      idem para los atraidos
  eod_ciudad     que EOD la cubre, para poder citarla con su año

Uso:  python -X utf8 scripts/cruza_eod_zonas_censales.py
"""
import glob
import os
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
AN = RAIZ / "data" / "analisis"
GEOJSON = Path(r"C:\Users\Rodrigo\Análisis RMG") / "EODs" / "EOD-Chile" / "data" / "geojson"
METRICO = 32719


def clave(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    return "".join(c for c in s.upper() if c.isalnum())


def main():
    zc = gpd.read_parquet(AN / "zona_demanda.parquet")
    zc = zc.drop(columns=[c for c in ["eod_bici_gen", "eod_bici_atr", "eod_n_gen",
                                      "eod_n_atr", "eod_ciudad"]
                          if c in zc.columns])
    ez = pd.read_parquet(AN / "demanda_eod_zona.parquet")
    ez["zona"] = ez.zona.astype(str).str.replace(r"\.0$", "", regex=True)

    archivos = {clave(os.path.splitext(os.path.basename(f))[0]): f
                for f in glob.glob(str(GEOJSON / "*.geojson"))}
    print(f"zonificaciones EOD disponibles: {len(archivos)}")

    piezas = []
    sin_geom = []
    for ciudad, g in ez.groupby("ciudad"):
        f = archivos.get(clave(ciudad))
        if not f:
            sin_geom.append(ciudad)
            continue
        ge = gpd.read_file(f)
        col = next((c for c in ["zona", "ZONA", "Zona"] if c in ge.columns), None)
        if col is None:
            sin_geom.append(ciudad)
            continue
        ge["zona"] = ge[col].astype(str).str.replace(r"\.0$", "", regex=True)
        ge = ge[["zona", "geometry"]].dropna(subset=["geometry"]).to_crs(METRICO)
        # Varias zonificaciones EOD traen poligonos invalidos (anillos que se
        # cruzan) y cualquier operacion de conjunto revienta con
        # TopologyException. `make_valid` los repara sin alterar su extension.
        ge["geometry"] = ge.geometry.make_valid()
        ge = ge[~ge.geometry.is_empty]

        gen = g[g.lado == "origen"].groupby("zona").agg(
            gen=("viajes", "sum"), ngen=("n", "sum"))
        atr = g[g.lado == "destino"].groupby("zona").agg(
            atr=("viajes", "sum"), natr=("n", "sum"))
        ge = ge.merge(gen, on="zona", how="left").merge(atr, on="zona", how="left")
        cols4 = ["gen", "atr", "ngen", "natr"]
        ge[cols4] = ge[cols4].fillna(0)
        if ge[["gen", "atr"]].to_numpy().sum() <= 0:
            continue

        # zonas censales que caen dentro del area de esa EOD
        sub = zc[zc.geometry.notna()].to_crs(METRICO).copy()
        sub["geometry"] = sub.geometry.make_valid()
        sub = sub[~sub.geometry.is_empty]
        caja = ge.total_bounds
        sub = sub.cx[caja[0]:caja[2], caja[1]:caja[3]]
        if sub.empty:
            continue
        inter = gpd.overlay(sub[["zona", "pob", "geometry"]].rename(
            columns={"zona": "zona_cen"}), ge, how="intersection",
            keep_geom_type=True)
        if inter.empty:
            continue

        # reparto proporcional a la POBLACION del trozo, aproximada por la
        # poblacion de la zona censal escalada por la fraccion de area suya que
        # cae dentro de la zona EOD
        area_cen = sub.set_index("zona").geometry.area
        inter["frac"] = inter.geometry.area / inter.zona_cen.map(area_cen).replace(0, np.nan)
        inter["peso"] = inter.pob.fillna(0) * inter.frac.fillna(0)
        tot = inter.groupby("zona").peso.transform("sum").replace(0, np.nan)
        inter["w"] = (inter.peso / tot).fillna(0)
        inter["eod_bici_gen"] = inter.gen * inter.w
        inter["eod_bici_atr"] = inter.atr * inter.w
        # El respaldo muestral se reparte con el mismo peso que los viajes: si
        # la mitad de la poblacion de una zona EOD de 10 encuestados cae en
        # esta zona censal, hay 5 encuestados detras de su cifra. Es el valor
        # esperado, no un conteo entero, y por eso queda con decimal.
        inter["eod_n_gen"] = inter.ngen * inter.w
        inter["eod_n_atr"] = inter.natr * inter.w

        r = inter.groupby("zona_cen")[["eod_bici_gen", "eod_bici_atr",
                                       "eod_n_gen", "eod_n_atr"]].sum().reset_index()
        r["eod_ciudad"] = f"{ciudad} {int(g.anio.iloc[0])}"
        piezas.append(r.rename(columns={"zona_cen": "zona"}))
        print(f"  {ciudad[:28]:28} {len(ge):4d} zonas EOD -> {len(r):5d} zonas censales")

    if sin_geom:
        print(f"sin zonificacion disponible, quedan fuera: {sin_geom}")

    if piezas:
        t = pd.concat(piezas, ignore_index=True)
        t = t.groupby("zona").agg(eod_bici_gen=("eod_bici_gen", "sum"),
                                  eod_bici_atr=("eod_bici_atr", "sum"),
                                  eod_n_gen=("eod_n_gen", "sum"),
                                  eod_n_atr=("eod_n_atr", "sum"),
                                  eod_ciudad=("eod_ciudad", "first")).reset_index()
        zc = zc.merge(t, on="zona", how="left")
    else:
        zc["eod_bici_gen"] = np.nan
        zc["eod_bici_atr"] = np.nan
        zc["eod_n_gen"] = np.nan
        zc["eod_n_atr"] = np.nan
        zc["eod_ciudad"] = None

    for c in zc.columns:
        if c != "geometry" and zc[c].dtype == object:
            zc[c] = zc[c].astype("string")
    zc.to_parquet(AN / "zona_demanda.parquet", index=False)

    con = zc.eod_bici_gen.notna().sum()
    print(f"\nzonas censales con viajes EOD asignados: {con:,} de {len(zc):,}")
    print(f"viajes en bicicleta repartidos: {zc.eod_bici_gen.sum():,.0f} generados / "
          f"{zc.eod_bici_atr.sum():,.0f} atraidos")
    ctrl = pd.read_parquet(AN / "demanda_eod_zona.parquet")
    ctrl = ctrl[ctrl.lado == "origen"].viajes.sum()
    print(f"control: la EOD reporta {ctrl:,.0f} viajes generados en las ciudades "
          f"con zonificacion disponible")
    if con:
        u = zc[zc.eod_bici_gen.notna()]
        print("\nrespaldo muestral por ciudad (zonas censales con n >= 5 "
              "viajes en bicicleta encuestados):")
        for ciu, g in u.groupby(u.eod_ciudad.astype(str)):
            ok = int((g.eod_n_gen >= 5).sum())
            print(f"  {ciu[:28]:28} {ok:4d} de {len(g):4d} ({100*ok/len(g):5.1f} %)")

        print("\ndiez zonas censales que mas viajes en bicicleta generan:")
        t = zc.nlargest(10, "eod_bici_gen")
        print(t[["zona", "comuna", "pob", "bici", "eod_bici_gen", "eod_ciudad"]]
              .to_string(index=False, float_format=lambda x: f"{x:,.0f}"))


if __name__ == "__main__":
    main()
