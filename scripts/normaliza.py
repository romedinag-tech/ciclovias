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
  4. CUT_COM INVALIDO (reportado por el Hub Multidato el 2026-09-15 y medido
     aca). SECTRA entrega CUT_COM = 0 o 1 en 26 tramos y nulo en otros 2, y
     `zfill(5)` convertia el 0 en '00000': una llave con forma valida que no
     es ninguna comuna, sin fallar. El CUT que no esta entre las 345 comunas
     INE se resuelve por NOMBRE normalizado; `cut_com_origen` dice como se
     obtuvo. Si no resuelve queda NULL, nunca '00000'. Y el script FALLA si
     algun cut_com no nulo queda fuera de las 345.
  5. ESPACIO DURO. `comuna_txt` trae U+00A0 en 46 filas ('Viña del Mar' con
     espacio duro) y `nombre_proyecto` en 54. Un cruce por nombre exacto no
     los encuentra. Todo campo de texto pasa por `limpia_texto`.
  6. LLAVE QUE LA GEOMETRIA CONTRADICE. Se mide la distancia de cada tramo a
     la comuna de su llave (`dist_comuna_llave_m`). Un tramo que corre por el
     limite comunal cae con su punto medio en la comuna vecina sin que eso sea
     un error: de 362 tramos cuyo punto representativo cae en otra comuna, 236
     tocan la suya y 53 estan a menos de 50 m. Lo que si es conflicto son 43
     tramos a mas de 500 m, todos en cortes historicos y ninguno en el vigente,
     varios con el CUT corrido en una unidad (Renca 13128 cae en 13127). Se
     marcan en `cut_com_discrepa_geo` y NO se corrigen: en unos acierta el
     nombre y en otros el CUT, de modo que no hay regla segura que aplicar.

Advertencia de uso: el catastro incluye las cuatro etapas del ciclo de vida
(existentes, ejecucion, diseño, planificadas). Reportar "km de ciclovias de
Chile" sobre el total INFLA la red a mas del doble. Filtrar por
`etapa == 'existentes'`.

Uso:  python -X utf8 scripts/normaliza.py
"""
import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_PQ = RAIZ / "data" / "parquet"

# Capa comunal INE de referencia, en solo lectura. Es la del Hub Multidato y no
# la del proyecto `elecciones`, que tiene 129 pares de comunas solapadas y
# duplica filas en un punto-en-poligono.
P_COMUNAS_INE = (Path(r"C:\Users\Rodrigo\Análisis RMG") / "Hub Multidato" /
                 "datos_oro" / "uso_suelo" / "comuna.geojson")

# Nombres de SECTRA que no calzan con el INE aunque se normalicen. Solo se usan
# para resolver un CUT invalido; nunca pisan un CUT valido.
ALIAS_COMUNA = {"LACALERA": "CALERA", "LLAYLLAY": "LLAILLAY",
                "PUERTOAYSEN": "AYSEN"}


def limpia_texto(serie):
    """Espacio duro a espacio comun, espacios repetidos a uno, sin bordes."""
    s = serie.astype("string")
    s = s.str.replace("\u00a0", " ", regex=False)
    s = s.str.replace(r"\s+", " ", regex=True).str.strip()
    return s.mask(s == "")


def clave_nombre(x):
    if x is None or x is pd.NA or (isinstance(x, float) and pd.isna(x)):
        return None
    t = unicodedata.normalize("NFD", str(x).replace("\u00a0", " "))
    t = re.sub(r"[^A-Z0-9]", "", t.encode("ascii", "ignore").decode().upper())
    return ALIAS_COMUNA.get(t, t) or None


_INE = None

# Mas alla de esta distancia a su propia comuna, un tramo no es de borde.
UMBRAL_CONFLICTO_M = 500


def comunas_ine():
    global _INE
    if _INE is None:
        g = gpd.read_file(P_COMUNAS_INE)[["cut", "comuna", "geometry"]]
        g["cut"] = g["cut"].astype(str).str.zfill(5)
        g["k"] = g.comuna.map(clave_nombre)
        assert len(g) == 345 and g.cut.is_unique and g.k.is_unique, \
            "la capa INE de referencia no tiene 345 comunas con CUT y nombre unicos"
        _INE = g.to_crs(4326)
    return _INE

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

    for c in out.columns:
        if c in ("geometry", "corte", "km", "cut_com_crudo"):
            continue
        if out[c].dtype == object or str(out[c].dtype).startswith(("string", "str")):
            out[c] = limpia_texto(out[c])

    # --- llave territorial ------------------------------------------------ #
    ine = comunas_ine()
    cut = out["cut_com_crudo"].astype("string").str.strip()
    cut = cut.str.replace(r"\.0$", "", regex=True)          # llega como float en algunos cortes
    cut = cut.str.zfill(5)
    valido = cut.isin(set(ine.cut)).fillna(False).astype(bool)
    por_nombre = out["comuna_txt"].map(clave_nombre).map(dict(zip(ine.k, ine.cut)))
    out["cut_com"] = cut.where(valido, por_nombre.astype("string"))
    origen = pd.Series("declarado", index=out.index, dtype="string")
    origen[~valido & por_nombre.notna()] = "nombre"
    origen[~valido & por_nombre.isna()] = "sin_resolver"
    out["cut_com_origen"] = origen

    # La geometria como arbitro: ni el nombre ni el CUT declarado son
    # confiables por si solos. Se mide y se marca, no se corrige.
    met = out.to_crs(32719).geometry
    pt = met.representative_point().to_crs(4326)
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=pt, crs=4326), ine[["cut", "geometry"]],
                  how="left", predicate="within")
    j = j[~j.index.duplicated()]
    out["cut_com_geo"] = j["cut"].astype("string")       # comuna del punto medio
    pol = ine.to_crs(32719).set_index("cut").geometry
    llave = gpd.GeoSeries(out["cut_com"].map(pol), index=out.index, crs=32719)
    tiene = llave.notna() & met.notna()
    dist = pd.Series(float("nan"), index=out.index)
    dist[tiene] = met[tiene].distance(llave[tiene], align=False)
    out["dist_comuna_llave_m"] = dist.round(1)
    out["cut_com_discrepa_geo"] = (dist > UMBRAL_CONFLICTO_M).fillna(False).astype(bool)
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

    # --- control: ninguna llave fuera de las 345 comunas INE ---------------- #
    # Va ANTES de escribir. Un cut_com invalido no pierde el registro: lo deja
    # asignado a una comuna que no existe, y eso no falla en ningun cruce.
    ine = set(comunas_ine().cut)
    malos = (panel.cut_com.notna() & ~panel.cut_com.isin(ine)).fillna(False).astype(bool)
    if malos.any():
        raise SystemExit(
            f"CONTROL FALLIDO: {int(malos.sum())} tramos con cut_com fuera de las 345 "
            f"comunas INE: {panel.loc[malos, 'cut_com'].value_counts().to_dict()}")

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

    print("\nllave comunal: como se obtuvo")
    print(panel.groupby(["corte", "cut_com_origen"]).size().unstack(fill_value=0).to_string())
    print(f"  control: 0 tramos fuera de las 345 comunas INE | "
          f"{int(panel.cut_com.isna().sum())} sin resolver (NULL)")
    d = panel[panel.cut_com_discrepa_geo]
    print(f"  {len(d)} tramos a mas de {UMBRAL_CONFLICTO_M} m de la comuna de su llave "
          f"(cut_com_discrepa_geo, marcados y no corregidos); en el corte vigente: "
          f"{int((d.corte == CORTES[-1][0]).sum())}")

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
