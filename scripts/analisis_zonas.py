# -*- coding: utf-8 -*-
"""
Agrega la demanda y la cobertura a ZONA CENSAL, la unidad del analisis espacial.

Por que zona censal y no manzana. El analisis de cobertura vive a nivel de
manzana porque ahi la distancia a la ciclovia se mide bien, pero llevar 197.168
poligonos a un visor web no es viable: el archivo se vuelve inmanejable y el
navegador no dibuja esa densidad a escala nacional. La zona censal —5.216
unidades— conserva el detalle intraurbano que interesa (que barrio genera viajes
en bicicleta y cual no) con dos ordenes de magnitud menos de geometria. Ademas es
la unidad en la que ya esta calculado el NSE, de modo que no hay que reimputarlo.

Salidas:
  data/analisis/zona_demanda.parquet   una fila por zona censal, con geometria

Uso:  python -X utf8 scripts/analisis_zonas.py
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from shapely import wkb

RAIZ = Path(__file__).resolve().parent.parent
AN = RAIZ / "data" / "analisis"
RMG = Path(r"C:\Users\Rodrigo\Análisis RMG")
GIS = RMG / "GIS Gran Concepción" / "Analisis uso de suelo Gran Concepción"
P_ZONAL = GIS / "Censo" / "2024" / "Cartografia_censo2024_Pais" / \
    "Cartografia_censo2024_Pais_Zonal.parquet"
P_NSE = GIS / "analysis_ready" / "analysis_zona.parquet"

MODOS = ["n_transporte_auto", "n_transporte_publico", "n_transporte_camina",
         "n_transporte_bicicleta", "n_transporte_motocicleta",
         "n_transporte_otros"]


def main():
    AN.mkdir(parents=True, exist_ok=True)

    # --- lo que ya se calculo por manzana, agregado a su zona --------------- #
    m = pd.read_parquet(AN / "manzana_cobertura.parquet")
    m["zona"] = m["zona"].astype(str)
    agg = m.groupby("zona").apply(lambda d: pd.Series({
        "cut_com": d.cut_com.iloc[0],
        "comuna": d.COMUNA.iloc[0],
        "region": d.REGION.iloc[0],
        "pob": d.n_per.sum(),
        "bici": d.n_transporte_bicicleta.sum(),
        "viajes_modo": d[MODOS].sum().sum(),
        "manzanas": len(d),
        # la distancia de la zona es la de sus manzanas ponderada por poblacion:
        # el promedio simple daria el mismo peso a una manzana vacia que a una
        # con mil habitantes
        "dist_m": (np.average(d.dist_existente_m, weights=d.n_per)
                   if d.n_per.sum() > 0 else d.dist_existente_m.mean()),
        "pob_cub_300": d.loc[d.dist_existente_m <= 300, "n_per"].sum(),
        "bici_cub_300": d.loc[d.dist_existente_m <= 300,
                              "n_transporte_bicicleta"].sum(),
        "escolares": d.n_asistencia_basica.sum() + d.n_asistencia_media.sum(),
        "superior": d.n_asistencia_superior.sum(),
        "escolaridad": (np.average(d.prom_escolaridad18.fillna(0), weights=d.n_per)
                        if d.n_per.sum() > 0 else np.nan),
    }), include_groups=False).reset_index()

    agg["bici_pct"] = 100 * agg.bici / agg.viajes_modo.replace(0, np.nan)
    agg["cob_pct"] = 100 * agg.pob_cub_300 / agg.pob.replace(0, np.nan)

    # --- NSE por zona (ya existe, no se recalcula) -------------------------- #
    nse = pq.read_table(P_NSE, columns=["zona", "nse_score", "nse_nivel",
                                        "dens_hab_ha", "valor_suelo"]).to_pandas()
    nse["zona"] = nse.zona.astype(str).str.strip()
    agg = agg.merge(nse, on="zona", how="left")

    # --- geometria ---------------------------------------------------------- #
    z = pq.read_table(P_ZONAL).to_pandas()
    col_id = next((c for c in ["ID_ZONA", "id_zona", "ZONA", "COD_ZONA"]
                   if c in z.columns), None)
    col_geo = next((c for c in ["SHAPE", "geometry", "geom"] if c in z.columns), None)
    if col_id is None or col_geo is None:
        raise SystemExit(f"no encuentro id/geometria en el zonal: {list(z.columns)[:25]}")

    z["zona"] = pd.to_numeric(z[col_id], errors="coerce").astype("Int64").astype(str)
    geom = [wkb.loads(b) if isinstance(b, (bytes, bytearray)) else None
            for b in z[col_geo]]
    gz = gpd.GeoDataFrame(z[["zona"]], geometry=geom, crs="EPSG:4326")
    gz = gz[gz.geometry.notna()].drop_duplicates("zona")

    out = gz.merge(agg, on="zona", how="inner")
    out = gpd.GeoDataFrame(out, geometry="geometry", crs="EPSG:4326")
    for c in out.columns:
        if c != "geometry" and out[c].dtype == object:
            out[c] = out[c].astype("string")
    out.to_parquet(AN / "zona_demanda.parquet", index=False)

    sin_geom = len(agg) - len(out)
    print(f"zonas censales con dato y geometria: {len(out):,} "
          f"(de {len(agg):,} con dato; {sin_geom:,} sin geometria)")
    print(f"poblacion cubierta: {out.pob.sum():,.0f} | "
          f"ciclistas: {out.bici.sum():,.0f}")
    print(f"NSE resuelto en {out.nse_score.notna().mean():.1%} de las zonas")
    print("\ndiez zonas con mayor participacion de la bicicleta "
          "(minimo 500 habitantes):")
    t = out[out.pob >= 500].nlargest(10, "bici_pct")
    print(t[["zona", "comuna", "pob", "bici", "bici_pct", "dist_m", "nse_score"]]
          .to_string(index=False, float_format=lambda x: f"{x:.1f}"))


if __name__ == "__main__":
    main()
