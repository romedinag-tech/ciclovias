# -*- coding: utf-8 -*-
"""
Capa de normalizacion: de las descargas crudas a tablas listas para analisis.

Produce dos salidas en data/parquet/:

  catastro_panel.parquet   panel de los cuatro cortes del Catastro Nacional con
                           nombres de campo homogeneos y llave territorial
                           normalizada. Permite medir crecimiento de red, no
                           solo fotografiarla.
  catastro_comuna.parquet  resumen por comuna y corte: km y tramos por etapa.

Correcciones que aplica, todas verificadas contra el dato (ver CLAUDE.md):

  1. CUT_COM viene SIN relleno de ceros en las regiones 1 a 9 (2.496 de 4.850
     registros del corte 2026-07 traen 4 digitos). Se normaliza a 5 con zfill.
  2. CUT_REG es POCO FIABLE: hay registros donde no corresponde a la comuna
     (Colina declarada region 6, tramos de Negrete y Los Angeles declarados
     region 9 siendo del Biobio). La region se DERIVA de los dos primeros
     digitos del CUT_COM normalizado, y la discrepancia queda marcada en la
     columna `cut_reg_declarado_discrepa` en vez de corregirse en silencio.
  3. Los nombres de campo cambian entre cortes (EMPLAZA_TEX/EMPLAZA_TE,
     NOM_PROYECTO/NOMBRE_PRO, FECHA_EJECUCION/YEAR_EJECU/YEAR_EJECUCION,
     REGION/REGIÓN). Se mapean explicitamente; lo que no exista queda NULL.

Advertencia de uso: el catastro incluye las cuatro etapas del ciclo de vida
(existentes, ejecucion, diseño, planificadas). Reportar "km de ciclovias de
Chile" sobre el total INFLA la red a mas del doble. Filtrar por
`etapa == 'existentes'`.

Uso:  python -X utf8 scripts/normaliza.py
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_PQ = RAIZ / "data" / "parquet"

CORTES = [
    ("2024-09", "sectra_ciclovias_nac_2024_09"),
    ("2024-11", "sectra_ciclovias_nac_2024_11"),
    ("2025-07", "sectra_ciclovias_nac_2025_07"),
    ("2026-07", "sectra_ciclovias_nac_2026_07"),
]

# destino -> posibles nombres de origen, en orden de preferencia
MAPA = {
    "identifica": ["IDENTIFICA"],
    "region_txt": ["REGIÓN", "REGION"],
    "comuna_txt": ["COMUNA"],
    "eje_via": ["EJE_VIA"],
    "inicio": ["INICIO"],
    "fin": ["FIN"],
    "km": ["KM"],
    "tipo": ["TIPO"],
    "carac_func": ["CARAC_FUNC"],
    "emplaza_txt": ["EMPLAZA_TEX", "EMPLAZA_TE"],
    "emplaza_n": ["EMPLAZA_N"],
    "urbana": ["URBANA"],
    "etapa": ["ETAPA"],
    "etapa_det": ["Etapa_det", "ETAPA_DET"],
    "cartera": ["CARTERA"],
    "bip_pmu": ["BIP_o_PMU", "BIP_PMU"],
    "nombre_proyecto": ["NOMBRE_PROYECTO_BIP_o_PMU", "NOM_PROYECTO", "NOMBRE_PRO"],
    "normativa": ["NORMATIVA"],
    "resolucion": ["RESOLUCION"],
    "comentario": ["COMENTARIO"],
    "cut_reg_declarado": ["CUT_REG"],
    "cut_com_crudo": ["CUT_COM"],
    "year_ejecucion": ["YEAR_EJECUCION", "YEAR_EJECU", "FECHA_EJECUCION", "FECHA_EJE_tex"],
    "fuente_actualiza": ["FUENTE_ACTUALIZA", "FUENTE_UPDATE", "FUENTE_ACT", "FUENTE_UPD"],
}


def _toma(g, candidatos):
    for c in candidatos:
        if c in g.columns:
            return g[c]
    return pd.Series([pd.NA] * len(g), index=g.index)


def normaliza_corte(corte, slug):
    g = gpd.read_parquet(DIR_PQ / f"{slug}.parquet")
    out = gpd.GeoDataFrame(
        {dest: _toma(g, orig) for dest, orig in MAPA.items()},
        geometry=g.geometry, crs=g.crs,
    )
    out.insert(0, "corte", corte)

    # --- llave territorial ------------------------------------------------ #
    cut = out["cut_com_crudo"].astype("string").str.strip()
    cut = cut.str.replace(r"\.0$", "", regex=True)          # llega como float en algunos cortes
    out["cut_com"] = cut.str.zfill(5)
    out["cut_reg"] = out["cut_com"].str[:2]

    dec = pd.to_numeric(out["cut_reg_declarado"], errors="coerce").astype("Int64")
    out["cut_reg_declarado_discrepa"] = (
        dec.notna() & (dec != pd.to_numeric(out["cut_reg"], errors="coerce"))
    )

    # --- etapa normalizada ------------------------------------------------ #
    out["etapa"] = out["etapa"].astype("string").str.strip().str.lower()
    out["existente"] = out["etapa"].eq("existentes")

    # --- largo medido sobre la geometria ---------------------------------- #
    # No reemplaza al KM declarado: se guarda al lado para poder auditarlo.
    out["km_geom"] = out.to_crs(32719).geometry.length / 1000.0
    out["km"] = pd.to_numeric(out["km"], errors="coerce")

    return out


def main():
    partes = [normaliza_corte(c, s) for c, s in CORTES]
    panel = pd.concat(partes, ignore_index=True)
    panel = gpd.GeoDataFrame(panel, geometry="geometry", crs="EPSG:4326")

    # Un mismo campo llega con tipo distinto segun el corte (CUT_COM viene como
    # texto en unos y como numero en otros), lo que deja columnas `object` que
    # Parquet no sabe escribir. Se fija el tipo explicitamente.
    for c in panel.columns:
        if c != "geometry" and panel[c].dtype == object:
            panel[c] = panel[c].astype("string")

    p = DIR_PQ / "catastro_panel.parquet"
    panel.to_parquet(p, index=False)

    resumen = (panel.groupby(["corte", "cut_com", "etapa"], dropna=False)
                    .agg(km=("km", "sum"), km_geom=("km_geom", "sum"),
                         tramos=("identifica", "size"))
                    .reset_index())
    resumen.to_parquet(DIR_PQ / "catastro_comuna.parquet", index=False)

    # --- reporte ---------------------------------------------------------- #
    print(f"panel: {len(panel):,} filas -> {p.name} "
          f"({p.stat().st_size/1e6:.1f} MB)")
    print(f"resumen comunal: {len(resumen):,} filas\n")

    print("evolucion de la red EXISTENTE")
    ex = panel[panel.existente]
    t = ex.groupby("corte").agg(km=("km", "sum"), tramos=("identifica", "size"),
                                comunas=("cut_com", "nunique"))
    t["delta_km"] = t.km.diff()
    print(t.round(1).to_string())

    print("\nregistros con CUT_REG declarado que no calza con la comuna:")
    d = panel[panel.cut_reg_declarado_discrepa]
    print(f"  {len(d)} de {len(panel):,} "
          f"({len(d)/len(panel)*100:.2f} %) — se usa el derivado del CUT_COM")

    print("\nkm declarado vs km medido sobre la geometria (corte mas reciente):")
    u = panel[panel.corte == CORTES[-1][0]]
    print(f"  declarado {u.km.sum():,.1f} km | geometrico {u.km_geom.sum():,.1f} km"
          f" | diferencia {abs(u.km.sum()-u.km_geom.sum())/u.km.sum()*100:.2f} %")


if __name__ == "__main__":
    main()
