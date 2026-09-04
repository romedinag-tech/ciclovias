# -*- coding: utf-8 -*-
"""
Cruces de la EOD: quien anda en bicicleta, por edad, sexo, ingreso y proposito.

Parte de la misma reconstruccion validada en `analisis_demanda.py` —separar el
grupo no motorizado en sus dos codigos originales— pero la aplica sobre
`viajes_analiticos.parquet`, que es el unico archivo que trae los atributos de
la persona (grupo etario, sexo, quintil de ingreso) pegados al viaje.

Antes de usarlo se comprobo que reproduce exactamente la reconstruccion hecha
sobre los archivos por ciudad: r = 1,00000 y diferencia media de 0,0000 puntos
porcentuales en las 15 ciudades. Si esa igualdad se rompiera en el futuro, es
señal de que el dataset analitico cambio de criterio y hay que revisarlo antes
de seguir publicando estos cruces.

Lo que se calcula NO es solo cuantos viajes en bicicleta hace cada grupo, sino
**que proporcion de los viajes de ese grupo son en bicicleta**. Es la unica
forma de comparar grupos de tamaño distinto: los hombres hacen mas viajes que
las mujeres en casi toda ciudad, de modo que el volumen bruto de viajes en
bicicleta diria mas del tamaño del grupo que de su propension a pedalear.

Salida:
  data/analisis/eod_cruces.parquet   ciudad x dimension x valor, con viajes en
                                     bicicleta, viajes totales y participacion

Uso:  python -X utf8 scripts/analisis_eod_cruces.py
"""
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parent.parent
AN = RAIZ / "data" / "analisis"
P_VIAJES = Path(r"C:\Users\Rodrigo\Análisis RMG") / "EODs" / "EOD_PARQUET" / \
    "viajes_analiticos.parquet"

# dimension -> columna del dataset analitico
DIMS = {
    "edad": "grupo_etario",
    "sexo": "sexo_h",
    "quintil": "quintil_ingreso",
    "proposito": "proposito_agregado_h",
    "periodo": "periodo_dia",
    "hora": "hora",
}

COLS = ["ciudad", "anio", "modo_agregado", "modo_agregado_desc", "factor"] + \
    list(DIMS.values())


def hora_valida(serie):
    """La hora ya viene normalizada 0-23 en el dataset analitico; se acota por
    si algun registro trae basura, en vez de dejarla entrar al grafico."""
    h = pd.to_numeric(serie, errors="coerce")
    return h.where((h >= 0) & (h <= 23)).round()


def main():
    AN.mkdir(parents=True, exist_ok=True)
    pf = pq.ParquetFile(P_VIAJES)
    disp = [c for c in COLS if c in pf.schema_arrow.names]
    faltan = [c for c in COLS if c not in disp]
    if faltan:
        print(f"columnas ausentes, sus cruces se omiten: {faltan}")
    d = pq.read_table(P_VIAJES, columns=disp).to_pandas()
    d["f"] = pd.to_numeric(d.factor, errors="coerce").fillna(0)

    dsc = d.modo_agregado_desc.astype(str)
    nomot = dsc.str.contains("No Motor|No Caminata|BICICLETA|CAMINATA|Caminata",
                             case=False, na=False)

    filas = []
    for (ciu, anio), g in d.groupby(["ciudad", "anio"]):
        gm = nomot.loc[g.index]
        if not gm.any() or g.f.sum() <= 0:
            continue
        sub = (g[gm].groupby(g.loc[gm, "modo_agregado"].astype(str)).f.sum()
                    .sort_values(ascending=False))
        if len(sub) < 2:
            continue
        # el codigo dominante del grupo no motorizado es la caminata
        cods_bici = set(sub.index[1:])
        es_bici = gm & g.modo_agregado.astype(str).isin(cods_bici)

        for dim, col in DIMS.items():
            if col not in g.columns:
                continue
            vals = hora_valida(g[col]) if dim == "hora" else g[col]
            gg = g.assign(_v=vals, _b=es_bici).dropna(subset=["_v"])
            if gg.empty:
                continue
            tot = gg.groupby("_v").f.sum()
            bic = gg[gg._b].groupby("_v").f.sum()
            for v in tot.index:
                b = float(bic.get(v, 0.0))
                t = float(tot[v])
                filas.append(dict(
                    ciudad=str(ciu), anio=int(anio), dim=dim,
                    valor=(str(int(float(v))) if dim == "hora" else str(v)),
                    bici=round(b, 1), total=round(t, 1),
                    part=round(100 * b / t, 3) if t > 0 else None,
                ))

    t = pd.DataFrame(filas)
    t.to_parquet(AN / "eod_cruces.parquet", index=False)
    print(f"-> eod_cruces.parquet | {len(t):,} filas | "
          f"{t.ciudad.nunique()} ciudades | dims {sorted(t.dim.unique())}")

    # --- reporte nacional: participacion de la bicicleta por grupo ---------- #
    for dim, titulo in [("sexo", "SEXO"), ("edad", "GRUPO ETARIO"),
                        ("quintil", "QUINTIL DE INGRESO"),
                        ("proposito", "PROPOSITO")]:
        s = t[t.dim == dim]
        if s.empty:
            continue
        r = s.groupby("valor").agg(bici=("bici", "sum"), total=("total", "sum"))
        r["part"] = 100 * r.bici / r.total
        r = r[r.total > 0].sort_values("part", ascending=False)
        print(f"\n{titulo} — participacion de la bicicleta")
        for v, x in r.iterrows():
            print(f"  {str(v)[:26]:26} {x.part:5.2f} %   "
                  f"({x.bici:,.0f} de {x.total:,.0f} viajes)")


if __name__ == "__main__":
    main()
