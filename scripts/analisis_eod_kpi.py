# -*- coding: utf-8 -*-
"""
KPI de la EOD por ciudad, para la ficha del territorio del visor.

Toma los indicadores que ya publica el tablero de movilidad del repositorio
(`EODs/EOD-Chile/data/eod/index.json`) y les agrega los que ese indice no
resuelve o no distingue por modo:

  tiempo_med_min        tiempo MEDIANO de viaje, todos los modos
  tiempo_med_bici_min   tiempo mediano del viaje en bicicleta
  dist_med_bici_km      distancia mediana del viaje en bicicleta

Por que se calcula el tiempo y no se copia. El indice trae `tiempo_medio_min`
solo en 8 de 18 ciudades, mientras que el campo `tiempo_viaje` del microdato
esta completo al 99,9 % en las dieciocho. Y se usa la MEDIANA y no el promedio
porque el campo llega con valores de hasta 1.435 minutos —casi un dia— que son
errores de registro y arrastran cualquier media.

El valor por modo es el que interesa aca: comparar cuanto dura un viaje en
bicicleta contra el de la ciudad entera dice si la bicicleta esta compitiendo o
solo cubriendo lo que nadie mas cubre.

Salida:
  data/analisis/eod_kpi.parquet   una fila por ciudad

Uso:  python -X utf8 scripts/analisis_eod_kpi.py
"""
import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parent.parent
AN = RAIZ / "data" / "analisis"
EODS = Path(r"C:\Users\Rodrigo\Análisis RMG") / "EODs"
P_INDEX = EODS / "EOD-Chile" / "data" / "eod" / "index.json"
P_VIAJES = EODS / "EOD_PARQUET" / "viajes_analiticos.parquet"

TOPE_MIN = 300      # un viaje urbano de mas de 5 horas es error de registro


def clave(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    return "".join(c for c in s.upper() if c.isalnum())


def mediana_pond(v, w):
    """Mediana ponderada por el factor de expansion: sin ponderar, la mediana
    describe la muestra y no la ciudad."""
    m = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not m.any():
        return np.nan
    v, w = np.asarray(v)[m], np.asarray(w)[m]
    o = np.argsort(v)
    v, w = v[o], w[o]
    acum = np.cumsum(w)
    return float(v[np.searchsorted(acum, acum[-1] / 2.0)])


def main():
    AN.mkdir(parents=True, exist_ok=True)

    d = json.loads(P_INDEX.read_text(encoding="utf-8"))
    lst = d["ciudades"] if isinstance(d, dict) and "ciudades" in d else d
    idx = pd.DataFrame(lst)
    idx["k"] = idx.ciudad.map(clave)
    print(f"indice del tablero de movilidad: {len(idx)} ciudades")

    v = pq.read_table(P_VIAJES, columns=[
        "ciudad", "anio", "tiempo_viaje", "factor",
        "modo_agregado", "modo_agregado_desc"]).to_pandas()
    v["f"] = pd.to_numeric(v.factor, errors="coerce").fillna(0)
    v["t"] = pd.to_numeric(v.tiempo_viaje, errors="coerce")
    v.loc[(v.t <= 0) | (v.t > TOPE_MIN), "t"] = np.nan

    dsc = v.modo_agregado_desc.astype(str)
    nomot = dsc.str.contains("No Motor|No Caminata|BICICLETA|CAMINATA|Caminata",
                             case=False, na=False)

    filas = []
    for (ciu, anio), g in v.groupby(["ciudad", "anio"]):
        gm = nomot.loc[g.index]
        bici = pd.Series(False, index=g.index)
        if gm.any():
            sub = (g[gm].groupby(g.loc[gm, "modo_agregado"].astype(str)).f.sum()
                        .sort_values(ascending=False))
            if len(sub) >= 2:
                bici = gm & g.modo_agregado.astype(str).isin(set(sub.index[1:]))
        b = g[bici]
        filas.append(dict(
            k=clave(ciu), ciudad=str(ciu), anio=int(anio),
            tiempo_med_min=mediana_pond(g.t.values, g.f.values),
            tiempo_med_bici_min=(mediana_pond(b.t.values, b.f.values)
                                 if len(b) else np.nan),
            n_bici=int(bici.sum()),
        ))
    calc = pd.DataFrame(filas)

    # Distancia de la bicicleta, tomada del resumen SIN binear: la mediana
    # calculada sobre tramos de 1 km solo puede caer en x,5 y no distingue una
    # ciudad de otra.
    fd = AN / "eod_distancias_resumen.parquet"
    if fd.exists():
        dd = pd.read_parquet(fd)
        b = dd[dd.modo == "bicicleta"].copy()
        b["k"] = b.ciudad.map(clave)
        b = b.rename(columns={"dist_media_km": "dist_media_bici_km",
                              "dist_mediana_km": "dist_med_bici_km"})
        calc = calc.merge(b[["k", "dist_media_bici_km", "dist_med_bici_km"]],
                          on="k", how="left")
        a = dd[dd.modo == "todos"].copy()
        a["k"] = a.ciudad.map(clave)
        calc = calc.merge(a[["k", "dist_media_km"]].rename(
            columns={"dist_media_km": "dist_media_todos_km"}), on="k", how="left")
    else:
        for c in ["dist_media_bici_km", "dist_med_bici_km", "dist_media_todos_km"]:
            calc[c] = np.nan

    t = idx.merge(calc.drop(columns=["ciudad", "anio"]), on="k", how="outer")
    t.to_parquet(AN / "eod_kpi.parquet", index=False)

    print(f"-> eod_kpi.parquet | {len(t)} ciudades")
    faltan = t.tiempo_medio_min.isna().sum() if "tiempo_medio_min" in t else 0
    print(f"   el indice traia el tiempo en {len(t)-faltan} de {len(t)} ciudades; "
          f"calculado aca en {t.tiempo_med_min.notna().sum()}")
    cols = ["ciudad", "anio", "n_zonas", "viajes", "viajes_persona",
            "pct_trabajo", "pct_estudio", "pct_publico", "pct_privado",
            "tiempo_med_min", "tiempo_med_bici_min",
            "dist_media_todos_km", "dist_media_bici_km"]
    cols = [c for c in cols if c in t.columns]
    print()
    print(t[cols].sort_values("viajes", ascending=False)
           .to_string(index=False, float_format=lambda x: f"{x:,.2f}"))


if __name__ == "__main__":
    main()
