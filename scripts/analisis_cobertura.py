# -*- coding: utf-8 -*-
"""
Cobertura de la red de ciclovias sobre poblacion y equipamiento.

En vez de fijar un radio y contar lo que cae adentro, calcula para cada manzana
censal y cada establecimiento la DISTANCIA al tramo de ciclovia mas cercano. Asi
cualquier umbral (300 m del ICC de SECTRA, 694 m del estudio MINVU 2018, o el que
pida el analisis) se deriva despues sin recalcular, y se puede mostrar la curva
de cobertura completa en vez de un solo numero que depende del radio elegido.

Se calculan DOS distancias por unidad:
  dist_existente_m  al tramo en etapa 'existentes' (la red construida)
  dist_total_m      a cualquier tramo del catastro, incluida la cartera en
                    diseño y planificada (el escenario si todo se ejecuta)

Insumos en SOLO LECTURA (activos de otros proyectos del repo):
  Censo 2024 manzanas    GIS Gran Concepcion/.../Cartografia_censo2024_Pais_Manzanas.parquet
  NSE por zona censal    GIS Gran Concepcion/.../analysis_ready/analysis_zona.parquet
  MINEDUC escolar        SERVEL/anclas/mineduc_escolar.parquet
  MINEDUC superior       SERVEL/anclas/mineduc_superior.parquet

Salidas, todas dentro de este proyecto:
  data/analisis/manzana_cobertura.parquet
  data/analisis/cobertura_comuna.parquet
  data/analisis/equipamiento_cobertura.parquet

Nota de proyeccion: las distancias se miden en EPSG:32719. En el extremo
occidental del pais (Chiloe, ~75,7 O) esa zona introduce un error de escala del
orden de 0,3 %, es decir menos de un metro sobre un umbral de 300 m. Es
irrelevante para este uso y se declara para que no haya que redescubrirlo.

Uso:  python -X utf8 scripts/analisis_cobertura.py
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from shapely import wkb
from shapely.strtree import STRtree

RAIZ = Path(__file__).resolve().parent.parent
DIR_PQ = RAIZ / "data" / "parquet"
DIR_OUT = RAIZ / "data" / "analisis"

RMG = Path(r"C:\Users\Rodrigo\Análisis RMG")
GIS = RMG / "GIS Gran Concepción" / "Analisis uso de suelo Gran Concepción"
P_MANZ = GIS / "Censo" / "2024" / "Cartografia_censo2024_Pais" / \
    "Cartografia_censo2024_Pais_Manzanas.parquet"
P_ZONA = GIS / "analysis_ready" / "analysis_zona.parquet"
P_ESCOLAR = RMG / "SERVEL" / "anclas" / "mineduc_escolar.parquet"
P_SUPERIOR = RMG / "SERVEL" / "anclas" / "mineduc_superior.parquet"

METRICO = 32719
UMBRALES = [150, 300, 500, 694, 1000]      # 300 = ICC SECTRA · 694 = MINVU 2018

# Columnas censales que interesan para caracterizar a la poblacion cubierta.
COLS_CENSO = [
    "CUT", "COMUNA", "REGION", "MANZENT", "ID_ZONA", "AREA_C",
    "n_per", "n_hombres", "n_mujeres",
    "n_edad_0_5", "n_edad_6_13", "n_edad_14_17", "n_edad_18_24",
    "n_edad_25_44", "n_edad_45_59", "n_edad_60_mas",
    "prom_escolaridad18", "n_viv_hacinadas", "n_vp",
    "n_asistencia_basica", "n_asistencia_media", "n_asistencia_superior",
    "n_ocupado",
    "n_transporte_auto", "n_transporte_publico", "n_transporte_camina",
    "n_transporte_bicicleta", "n_transporte_motocicleta", "n_transporte_otros",
    "SHAPE",
]


# --------------------------------------------------------------------------- #
def carga_red():
    p = gpd.read_parquet(DIR_PQ / "catastro_panel.parquet")
    u = p[p.corte == "2026-07"].copy()
    ex = u[u.existente]
    print(f"red 2026-07: {len(u):,} tramos ({u.km.sum():,.1f} km) | "
          f"existentes {len(ex):,} ({ex.km.sum():,.1f} km)")
    return (ex.to_crs(METRICO).geometry.values,
            u.to_crs(METRICO).geometry.values,
            sorted(ex.cut_com.dropna().unique()))


def distancia_a(geoms_ref, puntos):
    """Distancia de cada punto a la geometria de referencia mas cercana."""
    tree = STRtree(geoms_ref)
    idx = tree.nearest(puntos)
    return np.array([puntos[i].distance(geoms_ref[j])
                     for i, j in enumerate(idx)])


# --------------------------------------------------------------------------- #
def manzanas(cuts_con_red):
    """Manzanas de las comunas que tienen al menos un tramo existente.

    Las comunas sin red no se leen: su cobertura es cero por definicion y se
    incorporan despues desde el agregado comunal, sin pagar el costo de la
    geometria.
    """
    cuts = [int(c) for c in cuts_con_red]
    t = pq.read_table(P_MANZ, columns=COLS_CENSO,
                      filters=[("CUT", "in", cuts)])
    df = t.to_pandas()
    geom = [wkb.loads(b) if b else None for b in df.pop("SHAPE")]
    g = gpd.GeoDataFrame(df, geometry=geom, crs="EPSG:4326")
    g = g[g.geometry.notna()].copy()
    print(f"manzanas leidas: {len(g):,} en {g.CUT.nunique()} comunas con red")
    return g


def nse_por_zona():
    z = pq.read_table(P_ZONA, columns=["zona", "nse_score", "nse_nivel",
                                       "valor_suelo", "mv_bici"]).to_pandas()
    z["zona"] = z["zona"].astype(str).str.strip()
    return z


# --------------------------------------------------------------------------- #
def main():
    DIR_OUT.mkdir(parents=True, exist_ok=True)
    g_ex, g_tot, cuts = carga_red()

    g = manzanas(cuts)
    # El centroide representa a la manzana. En trama urbana la manzana mide
    # decenas de metros, muy por debajo del umbral de 300 m, asi que el sesgo es
    # menor que el error de la propia digitalizacion de la ciclovia.
    cen = g.to_crs(METRICO).geometry.centroid.values

    print("midiendo distancia a la red...")
    g["dist_existente_m"] = distancia_a(g_ex, cen)
    g["dist_total_m"] = distancia_a(g_tot, cen)

    # --- NSE por zona censal --------------------------------------------- #
    g["zona"] = g["ID_ZONA"].astype("Float64").astype("Int64").astype(str)
    g = g.merge(nse_por_zona(), on="zona", how="left")
    res = g.nse_score.notna().mean()
    print(f"NSE resuelto a nivel de zona censal en {res:.1%} de las manzanas; "
          f"el resto queda NULL y se declara como tal")

    g["cut_com"] = g["CUT"].astype(int).astype(str).str.zfill(5)
    for u in UMBRALES:
        g[f"cub_{u}"] = g["dist_existente_m"] <= u

    salida = g.drop(columns="geometry")
    salida.to_parquet(DIR_OUT / "manzana_cobertura.parquet", index=False)
    print(f"-> manzana_cobertura.parquet ({len(salida):,} filas)")

    # --- agregado comunal ------------------------------------------------- #
    def agg(d):
        r = {"pob": d.n_per.sum(), "manzanas": len(d),
             "bici": d.n_transporte_bicicleta.sum(),
             "escolares": d.n_asistencia_basica.sum() + d.n_asistencia_media.sum(),
             "nse_score_pob": np.average(d.nse_score, weights=d.n_per)
             if d.nse_score.notna().any() and d.n_per.sum() > 0 else np.nan}
        for u in UMBRALES:
            m = d[f"cub_{u}"]
            r[f"pob_cub_{u}"] = d.loc[m, "n_per"].sum()
            r[f"bici_cub_{u}"] = d.loc[m, "n_transporte_bicicleta"].sum()
        return pd.Series(r)

    com = g.groupby(["cut_com", "COMUNA", "REGION"]).apply(
        agg, include_groups=False).reset_index()
    for u in UMBRALES:
        com[f"pct_pob_{u}"] = 100 * com[f"pob_cub_{u}"] / com["pob"].replace(0, np.nan)
        com[f"pct_bici_{u}"] = 100 * com[f"bici_cub_{u}"] / com["bici"].replace(0, np.nan)
    com.to_parquet(DIR_OUT / "cobertura_comuna.parquet", index=False)
    print(f"-> cobertura_comuna.parquet ({len(com):,} comunas)")

    # --- equipamiento educacional ----------------------------------------- #
    eq = []
    esc = pq.read_table(P_ESCOLAR, columns=["RBD", "NOM_RBD", "NOM_COM_RB",
                                            "COD_COM_RB", "MAT_TOTAL",
                                            "TIPO_DEPEN", "lat", "lon"]).to_pandas()
    esc = esc.rename(columns={"RBD": "id", "NOM_RBD": "nombre",
                              "NOM_COM_RB": "comuna", "COD_COM_RB": "cut",
                              "MAT_TOTAL": "matricula", "TIPO_DEPEN": "dependencia"})
    esc["clase"] = "escolar"
    sup = pq.read_table(P_SUPERIOR, columns=["COD_INST", "NOMBRE_INS", "COMUNA",
                                             "COD_COMUNA", "TIPO_INST",
                                             "lat", "lon"]).to_pandas()
    sup = sup.rename(columns={"COD_INST": "id", "NOMBRE_INS": "nombre",
                              "COMUNA": "comuna", "COD_COMUNA": "cut",
                              "TIPO_INST": "dependencia"})
    sup["matricula"] = np.nan
    sup["clase"] = "superior"
    eq = pd.concat([esc, sup], ignore_index=True)
    # `dependencia` llega como codigo numerico en la base escolar y como texto
    # en la de educacion superior; se homogeneiza a texto.
    for c in ["nombre", "comuna", "dependencia", "clase"]:
        eq[c] = eq[c].astype("string")
    eq = eq[eq.lat.between(-56, -17) & eq.lon.between(-76, -66)].copy()

    pe = gpd.GeoSeries(gpd.points_from_xy(eq.lon, eq.lat),
                       crs="EPSG:4326").to_crs(METRICO).values
    eq["dist_existente_m"] = distancia_a(g_ex, pe)
    eq["dist_total_m"] = distancia_a(g_tot, pe)
    eq["cut_com"] = pd.to_numeric(eq["cut"], errors="coerce").astype("Int64") \
                      .astype(str).str.zfill(5)
    eq.to_parquet(DIR_OUT / "equipamiento_cobertura.parquet", index=False)
    print(f"-> equipamiento_cobertura.parquet ({len(eq):,} establecimientos)")

    # --- reporte ---------------------------------------------------------- #
    print("\n" + "=" * 66)
    print("COBERTURA DE POBLACION — comunas CON red existente")
    tot_p, tot_b = g.n_per.sum(), g.n_transporte_bicicleta.sum()
    print(f"universo: {tot_p:,.0f} habitantes y {tot_b:,.0f} personas que "
          f"declaran la bicicleta como modo principal")
    print(f"{'umbral':>8} {'pob cubierta':>14} {'%':>6} {'ciclistas':>11} {'%':>6}")
    for u in UMBRALES:
        m = g[f"cub_{u}"]
        p_, b_ = g.loc[m, "n_per"].sum(), g.loc[m, "n_transporte_bicicleta"].sum()
        print(f"{u:>6} m {p_:>14,.0f} {100*p_/tot_p:>5.1f}% "
              f"{b_:>11,.0f} {100*b_/tot_b:>5.1f}%")

    print("\nCOBERTURA POR NIVEL SOCIOECONOMICO (umbral 300 m)")
    gg = g[g.nse_score.notna()].copy()
    gg["q"] = pd.qcut(gg.nse_score, 5, labels=["Q1 mas bajo", "Q2", "Q3", "Q4",
                                               "Q5 mas alto"])
    t = gg.groupby("q", observed=True).apply(
        lambda d: pd.Series({
            "pob": d.n_per.sum(),
            "pct_cubierta": 100 * d.loc[d.cub_300, "n_per"].sum() / d.n_per.sum(),
            "pct_bici_modo": 100 * d.n_transporte_bicicleta.sum() /
            d[["n_transporte_auto", "n_transporte_publico", "n_transporte_camina",
               "n_transporte_bicicleta", "n_transporte_motocicleta",
               "n_transporte_otros"]].sum().sum(),
        }), include_groups=False)
    print(t.round(1).to_string())

    print("\nACCESIBILIDAD DEL EQUIPAMIENTO EDUCACIONAL (dentro de comunas con red)")
    e = eq[eq.cut_com.isin(set(g.cut_com))]
    for clase in ["escolar", "superior"]:
        d = e[e.clase == clase]
        if not len(d):
            continue
        print(f"  {clase}: {len(d):,} establecimientos | "
              + " · ".join(f"<{u} m: {100*(d.dist_existente_m<=u).mean():.0f}%"
                           for u in [300, 694, 1000]))


if __name__ == "__main__":
    main()
