# -*- coding: utf-8 -*-
"""
Conectividad de la red de ciclovias: ¿es una red o son fragmentos sueltos?

Construye el grafo de la red EXISTENTE uniendo los extremos de los tramos que
caen a menos de una tolerancia, identifica las componentes conexas y mide cuanto
de la red vive en la componente principal de cada ciudad. Una red muy
fragmentada puede tener muchos kilometros y aun asi no permitir un viaje
completo, que es justamente lo que un indicador de kilometraje no muestra.

La tolerancia de union es el parametro sensible: con 1 m casi nada se conecta
porque la digitalizacion no cierra exacto, y con 50 m se conectan tramos que en
la calle estan separados por una avenida. Por eso el script NO fija un valor:
recorre varias tolerancias y muestra como cambia el resultado, para elegir con
el dato a la vista.

Tambien cruza los establecimientos educacionales contra la componente a la que
quedan asociados, que es la pregunta util: no si hay ciclovia cerca del colegio,
sino si esa ciclovia forma parte de la red principal o de un fragmento aislado.

Salidas:
  data/analisis/conectividad_sensibilidad.parquet   metrica por tolerancia
  data/analisis/componentes.parquet                 componentes a la tolerancia elegida
  data/analisis/conectividad_comuna.parquet         resumen por comuna

Uso:  python -X utf8 scripts/analisis_conectividad.py
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.strtree import STRtree

RAIZ = Path(__file__).resolve().parent.parent
DIR_PQ = RAIZ / "data" / "parquet"
DIR_OUT = RAIZ / "data" / "analisis"
METRICO = 32719

TOLERANCIAS = [1, 5, 10, 20, 35, 50]
TOL_ELEGIDA = 20        # ver justificacion en CLAUDE.md, seccion conectividad


class UnionFind:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def une(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def componentes(gdf, tol):
    """Etiqueta cada tramo con su componente conexa.

    Une dos tramos cuando sus GEOMETRIAS estan a menos de `tol`, no cuando
    coinciden sus extremos. La diferencia no es menor: medido sobre la red
    existente, el 37,0 % de los extremos coincide con el extremo de otro tramo,
    pero otro 11,9 % cae sobre el INTERIOR de otro tramo — son empalmes en T,
    una ciclovia que llega a media cuadra de otra. Un grafo que solo mira
    extremos los pierde y reporta la red como mas fragmentada de lo que es.

    El precio de esta decision es que dos ciclovias que se cruzan quedan unidas
    aunque el cruce no este habilitado. Se asume que en un cruce se puede virar;
    es el supuesto optimista, de modo que la fragmentacion que se reporte es una
    COTA INFERIOR de la real.
    """
    geoms = list(gdf.geometry.values)
    tree = STRtree(geoms)
    uf = UnionFind()
    for i, g in enumerate(geoms):
        uf.find(i)
        for j in tree.query(g.buffer(tol)):
            if j > i and g.distance(geoms[j]) <= tol:
                uf.une(i, j)
    return [uf.find(i) for i in range(len(geoms))]


def main():
    DIR_OUT.mkdir(parents=True, exist_ok=True)
    p = gpd.read_parquet(DIR_PQ / "catastro_panel.parquet")
    red = p[(p.corte == "2026-07") & p.existente].to_crs(METRICO).copy()
    red = red[red.geometry.notna() & (red.geometry.length > 0)].copy()
    red["km_m"] = red.geometry.length / 1000
    print(f"red existente: {len(red):,} tramos | {red.km_m.sum():,.1f} km")

    # --- sensibilidad a la tolerancia ------------------------------------- #
    filas = []
    for tol in TOLERANCIAS:
        red[f"comp_{tol}"] = componentes(red, tol)
        g = red.groupby(f"comp_{tol}").km_m.sum().sort_values(ascending=False)
        filas.append({
            "tolerancia_m": tol,
            "n_componentes": len(g),
            "km_mayor": g.iloc[0],
            "pct_km_mayor": 100 * g.iloc[0] / red.km_m.sum(),
            "km_mediana_componente": g.median(),
            "pct_componentes_de_un_tramo":
                100 * (red.groupby(f"comp_{tol}").size() == 1).mean(),
        })
    sens = pd.DataFrame(filas)
    sens.to_parquet(DIR_OUT / "conectividad_sensibilidad.parquet", index=False)
    print("\nSENSIBILIDAD A LA TOLERANCIA DE UNION")
    print(sens.round(1).to_string(index=False))

    # --- a la tolerancia elegida ------------------------------------------ #
    col = f"comp_{TOL_ELEGIDA}"
    comp = (red.groupby(col)
               .agg(km=("km_m", "sum"), tramos=("identifica", "size"),
                    comunas=("cut_com", "nunique"),
                    comuna_principal=("cut_com",
                                      lambda s: s.value_counts().index[0]))
               .reset_index().rename(columns={col: "componente"})
               .sort_values("km", ascending=False))
    comp.to_parquet(DIR_OUT / "componentes.parquet", index=False)

    porcom = (red.groupby("cut_com")
                 .agg(km=("km_m", "sum"), tramos=("identifica", "size"),
                      n_componentes=(col, "nunique")).reset_index())
    kmax = (red.groupby(["cut_com", col]).km_m.sum()
               .groupby("cut_com").max().rename("km_componente_mayor"))
    porcom = porcom.merge(kmax, on="cut_com")
    porcom["pct_km_componente_mayor"] = 100 * porcom.km_componente_mayor / porcom.km
    porcom["km_por_componente"] = porcom.km / porcom.n_componentes
    porcom.to_parquet(DIR_OUT / "conectividad_comuna.parquet", index=False)

    print(f"\nA TOLERANCIA {TOL_ELEGIDA} m")
    print(f"  {len(comp):,} componentes en {red.km_m.sum():,.0f} km")
    print(f"  la mayor tiene {comp.km.iloc[0]:,.1f} km "
          f"({100*comp.km.iloc[0]/red.km_m.sum():.1f} % de la red) "
          f"y cruza {comp.comunas.iloc[0]} comunas")
    print(f"  la mitad de las componentes no pasa de "
          f"{comp.km.median():.2f} km")

    print("\n  diez comunas con mas km de ciclovia y su fragmentacion:")
    top = porcom.sort_values("km", ascending=False).head(10)
    nom = (red.drop_duplicates("cut_com").set_index("cut_com").comuna_txt)
    top = top.assign(comuna=top.cut_com.map(nom))
    print(top[["comuna", "km", "n_componentes", "km_componente_mayor",
               "pct_km_componente_mayor"]].round(1).to_string(index=False))

    # --- colegios sobre la componente principal --------------------------- #
    fe = DIR_OUT / "equipamiento_cobertura.parquet"
    if fe.exists():
        eq = pd.read_parquet(fe)
        eq = eq[eq.dist_existente_m <= 300]
        print(f"\n  establecimientos a menos de 300 m de la red: {len(eq):,}")
        print("  (la asociacion de cada uno a su componente se hace en el visor,"
              " sobre la capa componentes.parquet)")


if __name__ == "__main__":
    main()
