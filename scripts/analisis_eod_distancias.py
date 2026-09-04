# -*- coding: utf-8 -*-
"""
Distribucion de distancias del viaje en bicicleta, por ciudad.

El metodo NO se inventa aqui: es el mismo de `EODs/geo_distancias.py`, que ya
resuelve el problema —haversine entre los centroides de la zona de origen y la
de destino, y para el viaje intrazonal una estimacion por el radio equivalente
de la zona (0,7 R)—. Ese script escribe `distancia_km` de vuelta dentro de
`EODs`, que es solo lectura desde este proyecto y ademas se regenera aguas
arriba perdiendo la columna. Por eso se replica el calculo y la salida se
materializa aca.

El tratamiento del viaje intrazonal importa mas de lo que parece justamente
para la bicicleta: es el modo de los viajes cortos, de modo que si el intrazonal
se dejara en cero la moda de la distribucion caeria artificialmente en el primer
tramo. Con el radio equivalente, una zona de 1 km2 aporta unos 400 m.

Los tramos llegan hasta 8 km y luego agrupan, porque a esa altura ya esta
practicamente todo el viaje en bicicleta y estirar la escala solo agrega
categorias vacias.

Salida:
  data/analisis/eod_distancias.parquet   ciudad x modo x tramo, con viajes
                                         expandidos y participacion

Uso:  python -X utf8 scripts/analisis_eod_distancias.py
"""
import glob
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
AN = RAIZ / "data" / "analisis"
EODS = Path(r"C:\Users\Rodrigo\Análisis RMG") / "EODs"
P_VIAJES = EODS / "EOD_PARQUET" / "viajes_analiticos.parquet"
P_CENT = EODS / "EOD_PARQUET" / "zonas_centroides.parquet"
DIRS_GEOJSON = [EODS / "GEO" / "geojson", EODS / "EOD-Chile" / "data" / "geojson"]

BINS = [0, 1, 2, 3, 4, 5, 6, 7, 8, np.inf]
ETIQ = ["0-1", "1-2", "2-3", "3-4", "4-5", "5-6", "6-7", "7-8", "8+"]


def haversine(lo1, la1, lo2, la2):
    R = 6371.0
    p1, p2 = np.radians(la1), np.radians(la2)
    dphi = np.radians(la2 - la1)
    dlmb = np.radians(lo2 - lo1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def norm(s):
    return s.astype("string").str.replace(r"\.0$", "", regex=True)


def radios():
    """Radio equivalente de cada zona, para estimar el viaje intrazonal."""
    filas = []
    for d in DIRS_GEOJSON:
        for gj in glob.glob(str(d / "*.geojson")):
            ciudad = os.path.splitext(os.path.basename(gj))[0]
            try:
                g = gpd.read_file(gj)
            except Exception as e:                            # noqa: BLE001
                print(f"  aviso: no se pudo leer {ciudad}: {e}")
                continue
            col = next((c for c in ["zona", "ZONA", "Zona"] if c in g.columns), None)
            if col is None:
                continue
            area = g.to_crs(32719).geometry.area / 1e6
            for z, a in zip(g[col].astype(str), area):
                if a > 0:
                    filas.append({"ciudad": ciudad, "zona": z,
                                  "radio_km": float(np.sqrt(a / np.pi))})
        if filas:
            break                      # con un directorio basta
    return pd.DataFrame(filas).drop_duplicates(["ciudad", "zona"])


def main():
    AN.mkdir(parents=True, exist_ok=True)

    cent = pd.read_parquet(P_CENT)
    cent["zona"] = norm(cent["zona"])
    rad = radios()
    if not rad.empty:
        rad["zona"] = norm(rad["zona"])
        cent = cent.merge(rad, on=["ciudad", "zona"], how="left")
    else:
        cent["radio_km"] = np.nan
        print("aviso: sin geometrias de zona, el intrazonal usa el valor por defecto")

    V = pd.read_parquet(P_VIAJES, columns=[
        "ciudad", "anio", "zona_origen", "zona_destino", "factor",
        "modo_agregado", "modo_agregado_desc"])
    V["_zo"] = norm(V.zona_origen)
    V["_zd"] = norm(V.zona_destino)
    V["_c"] = V.ciudad.astype("string")
    V["f"] = pd.to_numeric(V.factor, errors="coerce").fillna(0)

    co = cent.rename(columns={"ciudad": "_c", "zona": "_zo", "lon": "lon_o",
                              "lat": "lat_o", "radio_km": "rad_o"})
    cd = cent.rename(columns={"ciudad": "_c", "zona": "_zd", "lon": "lon_d",
                              "lat": "lat_d", "radio_km": "rad_d"})
    V = V.merge(co[["_c", "_zo", "lon_o", "lat_o", "rad_o"]], on=["_c", "_zo"], how="left")
    V = V.merge(cd[["_c", "_zd", "lon_d", "lat_d", "rad_d"]], on=["_c", "_zd"], how="left")

    V["dist_km"] = haversine(V.lon_o, V.lat_o, V.lon_d, V.lat_d)
    intra = V._zo == V._zd
    V.loc[intra, "dist_km"] = (0.7 * V.loc[intra, "rad_o"]).fillna(0.5)

    cob = 100 * V.dist_km.notna().mean()
    print(f"distancia resuelta en el {cob:.1f} % de los viajes "
          f"({int(intra.sum()):,} intrazonales estimados por radio)")

    # --- bicicleta, con la misma reconstruccion validada -------------------- #
    dsc = V.modo_agregado_desc.astype(str)
    nomot = dsc.str.contains("No Motor|No Caminata|BICICLETA|CAMINATA|Caminata",
                             case=False, na=False)
    V["_bici"] = False
    for (ciu, _), g in V.groupby(["ciudad", "anio"]):
        gm = nomot.loc[g.index]
        if not gm.any():
            continue
        sub = (g[gm].groupby(g.loc[gm, "modo_agregado"].astype(str)).f.sum()
                    .sort_values(ascending=False))
        if len(sub) < 2:
            continue
        V.loc[g.index[gm & g.modo_agregado.astype(str).isin(set(sub.index[1:]))],
              "_bici"] = True

    V["tramo"] = pd.cut(V.dist_km, bins=BINS, labels=ETIQ, right=False)
    d = V.dropna(subset=["tramo"])

    filas = []
    for (ciu, anio), g in d.groupby(["ciudad", "anio"]):
        for modo, sel in [("bicicleta", g[g._bici]), ("todos", g)]:
            tot = sel.f.sum()
            if tot <= 0:
                continue
            s = sel.groupby("tramo", observed=True).f.sum()
            for tr in ETIQ:
                filas.append(dict(ciudad=str(ciu), anio=int(anio), modo=modo,
                                  tramo=tr, viajes=round(float(s.get(tr, 0.0)), 1),
                                  part=round(100 * float(s.get(tr, 0.0)) / tot, 3)))
    t = pd.DataFrame(filas)
    t.to_parquet(AN / "eod_distancias.parquet", index=False)

    # Resumen por ciudad con la distancia SIN binear. La mediana calculada
    # sobre los tramos de 1 km solo puede caer en x,5 y no sirve para comparar
    # ciudades entre si; esta se calcula sobre la distancia continua.
    res = []
    for (ciu, anio), g in d.groupby(["ciudad", "anio"]):
        for modo, sel in [("bicicleta", g[g._bici]), ("todos", g)]:
            if sel.f.sum() <= 0:
                continue
            v = sel.dist_km.to_numpy()
            w = sel.f.to_numpy()
            m = np.isfinite(v) & np.isfinite(w) & (w > 0)
            if not m.any():
                continue
            vv, ww = v[m], w[m]
            o = np.argsort(vv)
            vv, ww = vv[o], ww[o]
            ac = np.cumsum(ww)
            res.append(dict(ciudad=str(ciu), anio=int(anio), modo=modo,
                            dist_media_km=round(float(np.average(vv, weights=ww)), 3),
                            dist_mediana_km=round(float(vv[np.searchsorted(ac, ac[-1] / 2)]), 3),
                            viajes=round(float(ww.sum()), 1)))
    r = pd.DataFrame(res)
    r.to_parquet(AN / "eod_distancias_resumen.parquet", index=False)
    print(f"-> eod_distancias_resumen.parquet | {len(r)} filas")
    print(f"-> eod_distancias.parquet | {len(t):,} filas | "
          f"{t.ciudad.nunique()} ciudades")

    # --- reporte ----------------------------------------------------------- #
    for modo in ["bicicleta", "todos"]:
        s = t[t.modo == modo].groupby("tramo").viajes.sum()
        s = s.reindex(ETIQ).fillna(0)
        tot = s.sum()
        if tot <= 0:
            continue
        med = d[d._bici] if modo == "bicicleta" else d
        mediana = np.average(med.dist_km, weights=med.f) if med.f.sum() else np.nan
        print(f"\nDISTRIBUCION DE DISTANCIAS — {modo.upper()} "
              f"(promedio ponderado {mediana:.2f} km)")
        acum = 0
        for tr in ETIQ:
            p = 100 * s[tr] / tot
            acum += p
            print(f"  {tr:>4} km {'#' * int(round(p)):32s} {p:5.1f} %   "
                  f"acumulado {acum:5.1f} %")


if __name__ == "__main__":
    main()
