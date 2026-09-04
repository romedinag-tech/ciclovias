# -*- coding: utf-8 -*-
"""
Demanda de bicicleta: Censo 2024, Encuestas Origen-Destino y contadores de flujo.

--------------------------------------------------------------------------
El problema de la EOD, y como se resuelve
--------------------------------------------------------------------------
La base EOD homologada del repo declara el modo en `modo_agregado_h`, y ahi la
bicicleta aparece SOLO en Talca 2022. En las demas ciudades queda absorbida en
"No Motorizado" junto con la caminata. Dar eso por bueno seria concluir que
diecisiete EOD no midieron bicicleta, lo que es falso: cada una la mide, pero el
codigo de modo es propio de cada estudio y la homologacion lo colapso.

El dato SI esta, un nivel mas abajo. Dentro del grupo no motorizado, el campo
`modo_agregado` conserva el codigo original del estudio, y en 16 de 18 ciudades
ese grupo se parte en exactamente DOS codigos: uno masivo y uno menor. Gran
Concepcion lo dice casi con todas sus letras, porque sus etiquetas son
"1.Caminata" y "2.No Caminata". La reconstruccion consiste en asignar el codigo
dominante a la caminata y el resto a la bicicleta.

--------------------------------------------------------------------------
Validacion contra la cifra oficial
--------------------------------------------------------------------------
No se publica sin contrastar. `EODs/indice_eod.csv` trae, tomadas de los informes
de cada estudio, las columnas `v_caminata` y `v_no_motorizado` por separado. En
las ciudades donde ese indice es internamente consistente —es decir, donde
`v_caminata + v_no_motorizado` reproduce la participacion no motorizada que da el
propio microdato— la reconstruccion coincide con la cifra oficial con una
diferencia de decimas de punto.

Donde NO coincide, el problema esta en el indice y queda demostrado midiendolo:
Coquimbo-La Serena trae `v_caminata = 0` y mete los 329.575 viajes no motorizados
enteros en `v_no_motorizado`; Puerto Montt declara 45,5 % de caminata cuando el
microdato entrega 18,7 % de no motorizados en total, que es aritmeticamente
imposible. Esas ciudades se marcan `indice_inconsistente` y su cifra oficial no
se usa como referencia, pero la reconstruccion propia se conserva.

Salidas:
  data/analisis/demanda_eod_ciudad.parquet    particion modal y validacion
  data/analisis/demanda_eod_perfil.parquet    bici por proposito, periodo, hora,
                                              quintil, sexo y grupo etario
  data/analisis/demanda_eod_zona.parquet      viajes de bici por zona EOD (O y D)
  data/analisis/demanda_comuna.parquet        Censo 2024 por comuna
  data/analisis/siniestros_bici.parquet       siniestros con ciclista (CONASET)

Uso:  python -X utf8 scripts/analisis_demanda.py
"""
import glob
import os
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parent.parent
AN = RAIZ / "data" / "analisis"
RMG = Path(r"C:\Users\Rodrigo\Análisis RMG")
GIS = RMG / "GIS Gran Concepción" / "Analisis uso de suelo Gran Concepción"
P_MANZ = GIS / "Censo" / "2024" / "Cartografia_censo2024_Pais" / \
    "Cartografia_censo2024_Pais_Manzanas.parquet"
EODP = RMG / "EODs" / "EOD_PARQUET"
P_IDX = RMG / "EODs" / "indice_eod.csv"
P_BICI = RMG / "dashboard accidentes" / "data" / "parquet" / "bicicletas.parquet"

MODOS = ["n_transporte_auto", "n_transporte_publico", "n_transporte_camina",
         "n_transporte_bicicleta", "n_transporte_motocicleta",
         "n_transporte_cab_lan_bote", "n_transporte_otros"]

# Ciudad EOD -> comunas que cubre. Se declara explicitamente porque el universo
# de una EOD metropolitana no es una comuna: Gran Santiago son decenas y Gran
# Concepcion son diez, mientras Talca o Valdivia son una sola. Compararlas
# contra el Censo sin este mapeo mezclaria universos distintos.
# Se resuelve por NOMBRE contra la cartografia censal; los nombres que no
# resuelvan quedan reportados, no silenciados.
CIUDAD_COMUNAS = {
    "Arica": ["Arica"],
    "Iquique - Alto Hospicio": ["Iquique", "Alto Hospicio"],
    "Antofagasta": ["Antofagasta"],
    "Copiapó": ["Copiapó"],
    "Coquimbo - La Serena": ["La Serena", "Coquimbo"],
    "Gran Valparaíso": ["Valparaíso", "Viña del Mar", "Concón", "Quilpué",
                        "Villa Alemana"],
    "San Antonio": ["San Antonio"],
    "Rancagua - Machalí": ["Rancagua", "Machalí"],
    "Talca": ["Talca"],
    "Curicó": ["Curicó"],
    "Linares": ["Linares"],
    "Chillán": ["Chillán", "Chillán Viejo"],
    "Gran Concepción": ["Concepción", "Talcahuano", "Hualpén",
                        "San Pedro de la Paz", "Chiguayante", "Penco", "Tomé",
                        "Coronel", "Lota", "Hualqui"],
    "Temuco - Padre las Casas": ["Temuco", "Padre las Casas"],
    "Valdivia": ["Valdivia"],
    "Osorno": ["Osorno"],
    "Puerto Montt": ["Puerto Montt"],
    "Punta Arenas": ["Punta Arenas"],
    # Gran Santiago se resuelve leyendo las comunas del propio archivo de
    # hogares, que si las trae por nombre; son 45 y listarlas a mano solo
    # agregaria una oportunidad de equivocarse.
}

TOL_CONSISTENCIA = 2.0     # puntos porcentuales


def hora_del_viaje(serie):
    """Hora de inicio 0-23 a partir de `hora_inicio`, que llega en TRES formatos
    distintos segun la ciudad y ninguno esta declarado:

      1. fecha centinela de Access/Excel — "1899-12-30 13:20:00": solo la parte
         horaria significa algo, la fecha es relleno;
      2. fraccion de dia de Excel — "0.54166666667" es 13:00;
      3. la hora pelada — "17" o "7.0".

    Leerla como numero sin distinguir formatos devuelve nanosegundos para el
    primer caso y cero para el segundo, y la curva horaria sale vacia sin que
    nada falle: asi estuvo el grafico de la seccion Demanda hasta detectarlo.
    """
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie.dt.hour.astype("Float64")
    dt = pd.to_datetime(serie, errors="coerce", format="mixed")
    h = dt.dt.hour.astype("Float64")
    num = pd.to_numeric(serie, errors="coerce")
    frac = num.where((num >= 0) & (num < 1))
    h = h.fillna((frac * 24).round().astype("Float64"))
    entera = num.where((num >= 0) & (num <= 23))
    h = h.fillna(entera.round().astype("Float64"))
    return h.where((h >= 0) & (h <= 23))


def norm(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def clave(s):
    return "".join(ch for ch in norm(s) if ch.isalnum())


# --------------------------------------------------------------------------- #
def censo_por_comuna():
    d = pq.read_table(P_MANZ, columns=["CUT", "COMUNA", "REGION"] + MODOS).to_pandas()
    d["cut_com"] = d.CUT.astype(int).astype(str).str.zfill(5)
    g = d.groupby(["cut_com", "COMUNA", "REGION"])[MODOS].sum().reset_index()
    g["viajes_modo"] = g[MODOS].sum(axis=1)
    g["bici_pct"] = 100 * g.n_transporte_bicicleta / g.viajes_modo.replace(0, np.nan)
    g["k"] = g.COMUNA.map(norm)
    return g


def reconstruye_eod():
    """Bicicleta por ciudad, separandola del grupo no motorizado."""
    filas, perfil, zonas = [], [], []
    for dd in sorted(glob.glob(str(EODP / "*" / "viaje.parquet"))):
        carpeta = os.path.basename(os.path.dirname(dd))
        pf = pq.ParquetFile(dd)
        names = pf.schema_arrow.names
        if "modo_agregado_desc" not in names:
            continue
        # La hora viene en `hora_inicio` (float 0-23) en todas las ciudades; no
        # existe una columna `hora` en los archivos por ciudad, y pedirla dejaba
        # la dimension horaria vacia sin que nada fallara.
        quiero = ["modo_agregado", "modo_agregado_desc", "factor", "proposito_agregado_h",
                  "periodo", "hora_inicio", "zona_origen", "zona_destino"]
        cols = [c for c in quiero if c in names]
        d = pq.read_table(dd, columns=cols).to_pandas()
        d["f"] = pd.to_numeric(d.get("factor"), errors="coerce").fillna(0)

        dsc = d.modo_agregado_desc.astype(str)
        nomot = dsc.str.contains("No Motor|No Caminata|BICICLETA|CAMINATA|Caminata",
                                 case=False, na=False)
        tot = d.f.sum()
        if not nomot.any() or tot <= 0:
            filas.append(dict(carpeta=carpeta, separable=False))
            continue

        sub = d.loc[nomot].groupby(d.modo_agregado.astype(str)).f.sum() \
                          .sort_values(ascending=False)
        if len(sub) < 2:
            filas.append(dict(carpeta=carpeta, separable=False,
                              nomot_pct=100 * d.loc[nomot, "f"].sum() / tot))
            continue

        cod_caminata = sub.index[0]
        cods_bici = list(sub.index[1:])
        es_bici = nomot & d.modo_agregado.astype(str).isin(cods_bici)

        ciudad = carpeta.split("__")[1].rsplit("_", 1)[0].replace("_", " ")
        anio = int(carpeta.rsplit("_", 1)[1])
        filas.append(dict(
            carpeta=carpeta, ciudad=ciudad, anio=anio, separable=True,
            viajes_exp=tot,
            bici_exp=d.loc[es_bici, "f"].sum(),
            caminata_exp=d.loc[nomot & ~es_bici, "f"].sum(),
            nomot_pct=100 * d.loc[nomot, "f"].sum() / tot,
            bici_pct=100 * d.loc[es_bici, "f"].sum() / tot,
            n_registros_bici=int(es_bici.sum()),
            cod_caminata=cod_caminata, cod_bici=", ".join(cods_bici),
        ))

        b = d[es_bici]
        for dim, col in [("proposito", "proposito_agregado_h"),
                         ("periodo", "periodo")]:
            if col in b.columns:
                s = b.groupby(b[col].astype(str)).f.sum()
                for k, v in s.items():
                    perfil.append(dict(ciudad=ciudad, anio=anio, dim=dim,
                                       valor=k, viajes=v))
        if "hora_inicio" in b.columns:
            hh = hora_del_viaje(b["hora_inicio"])
            s = b.assign(_h=hh).dropna(subset=["_h"]).groupby("_h").f.sum()
            for k, v in s.items():
                perfil.append(dict(ciudad=ciudad, anio=anio, dim="hora",
                                   valor=str(int(k)), viajes=v))
        for lado, col in [("origen", "zona_origen"), ("destino", "zona_destino")]:
            if col in b.columns:
                s = b.groupby(b[col].astype(str)).f.sum()
                for k, v in s.items():
                    zonas.append(dict(ciudad=ciudad, anio=anio, lado=lado,
                                      zona=k, viajes=v))
    return (pd.DataFrame(filas), pd.DataFrame(perfil), pd.DataFrame(zonas))


def valida(t):
    """Contrasta la reconstruccion con la cifra oficial de indice_eod.csv."""
    idx = pd.read_csv(P_IDX, encoding="utf-8")
    idx["k"] = idx.ciudad.map(clave)
    idx["ofi_bici_pct"] = 100 * idx.v_no_motorizado / idx.viajes_diarios
    idx["ofi_cam_pct"] = 100 * idx.v_caminata / idx.viajes_diarios
    idx["ofi_nomot_pct"] = idx.ofi_bici_pct + idx.ofi_cam_pct

    t = t.copy()
    t["k"] = t.ciudad.map(lambda x: clave(x) if isinstance(x, str) else "")
    t = t.merge(idx[["k", "ofi_bici_pct", "ofi_cam_pct", "ofi_nomot_pct",
                     "v_no_motorizado", "v_caminata"]], on="k", how="left")

    # El indice es utilizable solo si pasa DOS pruebas. La primera es que su
    # total no motorizado reproduzca el del microdato. La segunda es que declare
    # caminata y que esa caminata supere a la bicicleta: sin ella, Coquimbo-La
    # Serena pasaria por consistente con `v_caminata = 0` —porque su
    # `v_no_motorizado` de 329.575 viajes es en realidad el grupo completo— y
    # arrastraria una "cifra oficial" de 35,5 % de bicicleta que nadie midio.
    cuadra = (t.ofi_nomot_pct - t.nomot_pct).abs() <= TOL_CONSISTENCIA
    camina = t.v_caminata.fillna(0) > 0
    domina = t.v_caminata.fillna(0) > t.v_no_motorizado.fillna(0)
    t["indice_consistente"] = cuadra & camina & domina
    t["dif_pp"] = t.bici_pct - t.ofi_bici_pct
    return t


def main():
    AN.mkdir(parents=True, exist_ok=True)

    # ---------------- Censo ------------------------------------------------ #
    cen = censo_por_comuna()
    cen.drop(columns="k").to_parquet(AN / "demanda_comuna.parquet", index=False)
    print(f"Censo 2024: {len(cen)} comunas | "
          f"{cen.n_transporte_bicicleta.sum():,.0f} personas en bicicleta "
          f"({100*cen.n_transporte_bicicleta.sum()/cen.viajes_modo.sum():.2f} % "
          f"de quienes declaran modo)")

    # ---------------- EOD -------------------------------------------------- #
    t, perfil, zonas = reconstruye_eod()
    t = valida(t)

    # comunas de cada ciudad, para poder comparar con el Censo
    idx_cen = cen.set_index("k")
    mapa = dict(CIUDAD_COMUNAS)
    stgo = EODP / "Metropolitana__Gran_Santiago_2012" / "hogar.parquet"
    if stgo.exists():
        h = pq.read_table(stgo).to_pandas()
        cn = [c for c in h.columns if c.lower() == "comuna"]
        if cn:
            mapa["Gran Santiago"] = sorted(h[cn[0]].dropna().astype(str).unique())

    # Las carpetas de EOD_PARQUET no llevan tilde ("Curico", "Chillan"), de modo
    # que el nombre de la ciudad no empareja literalmente con las claves del
    # mapeo. Se indexa por clave alfanumerica sin acentos.
    mapa_k = {clave(k): v for k, v in mapa.items()}

    sin_resolver = []
    censo_pct, n_com = [], []
    for _, r in t.iterrows():
        nombres = mapa_k.get(clave(r.get("ciudad") or ""), [])
        ks = [norm(x) for x in nombres]
        ok = [k for k in ks if k in idx_cen.index]
        sin_resolver += [(r.get("ciudad"), k) for k in ks if k not in idx_cen.index]
        if ok:
            s = idx_cen.loc[ok]
            censo_pct.append(100 * s.n_transporte_bicicleta.sum() / s.viajes_modo.sum())
            n_com.append(len(ok))
        else:
            censo_pct.append(np.nan)
            n_com.append(0)
    t["censo_bici_pct"] = censo_pct
    t["censo_comunas"] = n_com

    t.drop(columns=[c for c in ["k"] if c in t.columns]) \
     .to_parquet(AN / "demanda_eod_ciudad.parquet", index=False)
    perfil.to_parquet(AN / "demanda_eod_perfil.parquet", index=False)
    zonas.to_parquet(AN / "demanda_eod_zona.parquet", index=False)

    v = t[t.separable == True]                                   # noqa: E712
    print(f"\nEOD: {len(v)} ciudades con bicicleta reconstruida "
          f"({t.separable.eq(False).sum()} no separables)")

    cons = v[v.indice_consistente == True]                       # noqa: E712
    inc = v[v.indice_consistente == False]                       # noqa: E712
    print(f"\nVALIDACION contra la cifra oficial de los informes EOD")
    print(f"  ciudades con indice oficial consistente: {len(cons)}")
    if len(cons):
        print(f"    correlacion r = {cons.bici_pct.corr(cons.ofi_bici_pct):.4f}")
        print(f"    diferencia absoluta media = {cons.dif_pp.abs().mean():.3f} pp "
              f"| maxima = {cons.dif_pp.abs().max():.3f} pp")
    if len(inc):
        print(f"  ciudades cuyo indice oficial es internamente inconsistente "
              f"y NO sirve de referencia: {len(inc)}")
        for _, r in inc.iterrows():
            print(f"    {r.ciudad}: el indice declara {r.ofi_nomot_pct:.1f} % no "
                  f"motorizado y el microdato da {r.nomot_pct:.1f} %")

    print("\nBICICLETA POR CIUDAD")
    cols = ["ciudad", "anio", "bici_pct", "ofi_bici_pct", "indice_consistente",
            "censo_bici_pct", "censo_comunas"]
    print(v[cols].sort_values("bici_pct", ascending=False)
           .to_string(index=False, float_format=lambda x: f"{x:.2f}"))

    w = v.dropna(subset=["censo_bici_pct"])
    if len(w) > 2:
        print(f"\nContraste con el Censo 2024 sobre las mismas comunas "
              f"(n={len(w)}): r = {w.bici_pct.corr(w.censo_bici_pct):.3f} | "
              f"Spearman = {w.bici_pct.corr(w.censo_bici_pct, method='spearman'):.3f}")
    if sin_resolver:
        print(f"\ncomunas declaradas que no resolvieron contra el Censo: "
              f"{sorted(set(sin_resolver))[:10]}")

    # ---------------- Siniestros con ciclista ------------------------------ #
    if P_BICI.exists():
        b = pq.read_table(P_BICI, columns=[
            "id_accidente", "anio", "mes", "hora", "dia_semana", "comuna",
            "cut_com", "cut_reg", "zona", "tipo_final", "causa_final",
            "fallecidos", "graves", "menos_graves", "leves", "lat", "lon",
        ]).to_pandas()
        b["cut_com"] = pd.to_numeric(b.cut_com, errors="coerce").astype("Int64") \
                         .astype(str).str.zfill(5)
        b = b[b.lat.between(-56, -17) & b.lon.between(-76, -66)]
        b.to_parquet(AN / "siniestros_bici.parquet", index=False)
        print(f"\nSiniestros con ciclista: {len(b):,} georreferenciados | "
              f"{b.anio.min():.0f}-{b.anio.max():.0f} | "
              f"{b.fallecidos.sum():,.0f} fallecidos, {b.graves.sum():,.0f} graves")


if __name__ == "__main__":
    main()
