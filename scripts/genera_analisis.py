# -*- coding: utf-8 -*-
"""
Genera ANALISIS.md leyendo las salidas de data/analisis/ y data/parquet/.

Misma regla que genera_catalogo.py: ninguna cifra del documento se escribe a
mano. Si el analisis cambia, se vuelve a correr y el texto queda al dia.

Uso:  python -X utf8 scripts/genera_analisis.py
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PQ = RAIZ / "data" / "parquet"
AN = RAIZ / "data" / "analisis"
SALIDA = RAIZ / "ANALISIS.md"

MODOS = ["n_transporte_auto", "n_transporte_publico", "n_transporte_camina",
         "n_transporte_bicicleta", "n_transporte_motocicleta",
         "n_transporte_otros"]


def n(x, d=0):
    """Formato numerico chileno: punto para miles, coma para decimales."""
    s = f"{x:,.{d}f}"
    return s.replace(",", "·").replace(".", ",").replace("·", ".")


def p(x, d=1):
    """Porcentaje con coma decimal."""
    return f"{x:.{d}f}".replace(".", ",") + " %"


def main():
    m = pd.read_parquet(AN / "manzana_cobertura.parquet")
    com = pd.read_parquet(AN / "cobertura_comuna.parquet")
    eq = pd.read_parquet(AN / "equipamiento_cobertura.parquet")
    sens = pd.read_parquet(AN / "conectividad_sensibilidad.parquet")
    comp = pd.read_parquet(AN / "componentes.parquet")
    ccom = pd.read_parquet(AN / "conectividad_comuna.parquet")
    panel = gpd.read_parquet(PQ / "catastro_panel.parquet")

    u = panel[panel.corte == "2026-07"]
    ex = u[u.existente]
    L = []
    A = L.append

    A("# Hallazgos — red de ciclovías, población y territorio\n")
    A("> Archivo **generado**. No editar a mano: correr\n"
      "> `python -X utf8 scripts/genera_analisis.py`.\n")
    A("Todas las cifras salen de leer `data/analisis/` y `data/parquet/` en el "
      "momento de generar el documento.\n")

    # ------------------------------------------------------------------ #
    A("## 1. Qué red se está midiendo\n")
    A(f"El catastro nacional vigente (corte 2026-07) tiene **{n(len(u))} tramos "
      f"y {n(u.km.sum(),1)} km**, pero sólo **{n(len(ex))} tramos y "
      f"{n(ex.km.sum(),1)} km están en etapa `existentes`**. Todo lo que sigue "
      f"mide la red construida; la cartera en diseño y planificada se usa sólo "
      f"como escenario de comparación.\n")
    et = u.groupby("etapa").km.sum().sort_values(ascending=False)
    A("| Etapa | km | tramos |")
    A("|---|---:|---:|")
    for e, km in et.items():
        A(f"| {e} | {n(km,1)} | {n((u.etapa==e).sum())} |")
    A("")

    # ------------------------------------------------------------------ #
    A("## 2. A quién alcanza la red\n")
    tot_p = m.n_per.sum()
    tot_b = m.n_transporte_bicicleta.sum()
    A(f"El universo son las **{n(com.shape[0])} comunas que tienen al menos un "
      f"tramo existente**, con {n(tot_p)} habitantes. De ellos, {n(tot_b)} "
      f"personas declaran en el Censo 2024 la bicicleta como modo principal de "
      f"transporte al trabajo o al estudio.\n")
    A("En vez de fijar un radio, se midió para cada manzana censal la distancia "
      "al tramo existente más cercano, de modo que la cobertura pueda leerse a "
      "cualquier umbral. Los dos umbrales con respaldo institucional son los "
      "300 m que usa el propio índice de ciclo-inclusión de SECTRA y los 694 m "
      "que el estudio MINVU 2018 midió por la red vial.\n")
    A("| Umbral | Población cubierta | % | Ciclistas cubiertos | % |")
    A("|---:|---:|---:|---:|---:|")
    for k in [150, 300, 500, 694, 1000]:
        c = m[f"cub_{k}"]
        p_ = m.loc[c, "n_per"].sum()
        b_ = m.loc[c, "n_transporte_bicicleta"].sum()
        A(f"| {n(k)} m | {n(p_)} | {p(p_/tot_p*100)} | {n(b_)} | {p(b_/tot_b*100)} |")
    A("")
    c3 = m["cub_300"]
    A(f"La red está mejor alineada con la demanda que con la población en "
      f"general: a 300 m vive el **{p(m.loc[c3,'n_per'].sum()/tot_p*100)}** de "
      f"la población pero el **{p(m.loc[c3,'n_transporte_bicicleta'].sum()/tot_b*100)}** "
      f"de quienes ya andan en bicicleta. La dirección de esa relación no puede "
      f"establecerse con este dato: la ciclovía puede haber atraído a los "
      f"ciclistas o haberse construido donde ya pedaleaban.\n")

    # ------------------------------------------------------------------ #
    A("## 3. La cobertura es socialmente regresiva\n")
    d = m[m.nse_score.notna() & (m.n_per > 0) & (m.AREA_C == "URBANO")].copy()
    d["q"] = pd.qcut(d.nse_score, 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
    t = d.groupby("q", observed=True).apply(lambda x: pd.Series({
        "pob": x.n_per.sum(),
        "cub": 100 * x.loc[x.dist_existente_m <= 300, "n_per"].sum() / x.n_per.sum(),
        "bici": 100 * x.n_transporte_bicicleta.sum() / x[MODOS].sum().sum(),
    }), include_groups=False)
    A(f"Sobre las {n(len(d))} manzanas urbanas con nivel socioeconómico "
      f"resuelto, la cobertura sube de forma monótona con el NSE mientras el "
      f"uso de la bicicleta baja. Es decir, **la infraestructura está donde "
      f"menos se pedalea**.\n")
    A("| Quintil de NSE | Población | Cubierta a 300 m | Bicicleta como modo |")
    A("|---|---:|---:|---:|")
    etq = {"Q1": "Q1 (más bajo)", "Q5": "Q5 (más alto)"}
    for q, r in t.iterrows():
        A(f"| {etq.get(q,q)} | {n(r.pob)} | {p(r.cub)} | {p(r.bici)} |")
    A("")
    A(f"La brecha entre el quintil más bajo y el más alto es de "
      f"**{n(t.cub.iloc[-1]-t.cub.iloc[0],1)} puntos porcentuales** de cobertura, "
      f"mientras el uso de la bicicleta corre en sentido contrario: "
      f"{p(t.bici.iloc[0])} en el quintil bajo contra {p(t.bici.iloc[-1])} "
      f"en el alto.\n")

    # control dentro de comuna
    d["qi"] = d.groupby("cut_com").nse_score.transform(
        lambda s: pd.qcut(s, 5, labels=False, duplicates="drop")
        if s.nunique() >= 5 else np.nan)
    v = d[d.qi.notna()]
    ti = v.groupby("qi").apply(lambda x: pd.Series({
        "cub": 100 * x.loc[x.dist_existente_m <= 300, "n_per"].sum() / x.n_per.sum()
    }), include_groups=False)
    A("**El resultado no es un artefacto de qué comunas tienen red.** Una "
      "objeción razonable es que las comunas de mayor ingreso simplemente "
      "tengan más kilómetros, y que el gradiente sea eso y no una desigualdad "
      "interna. Para descartarlo se recalculó el quintil de NSE **dentro de cada "
      f"comuna**, sobre las {n(v.cut_com.nunique())} comunas con suficiente "
      "variación interna. El gradiente se atenúa pero no desaparece: la "
      f"cobertura pasa de **{p(ti.cub.iloc[0])}** en el quintil más bajo de "
      f"la comuna a **{p(ti.cub.iloc[-1])}** en el más alto, "
      f"**{n(ti.cub.iloc[-1]-ti.cub.iloc[0],1)} puntos** de diferencia entre "
      "vecinos de un mismo municipio.\n")

    # ------------------------------------------------------------------ #
    A("## 4. La red sirve a la universidad, no al colegio\n")
    e = eq[eq.cut_com.isin(set(m.cut_com))]
    A("| Tipo | Establecimientos | < 300 m | < 694 m | < 1.000 m |")
    A("|---|---:|---:|---:|---:|")
    for clase, lab in [("escolar", "Escolares"),
                       ("superior", "Educación superior")]:
        s = e[e.clase == clase]
        A(f"| {lab} | {n(len(s))} | "
          + " | ".join(p(100*(s.dist_existente_m<=k).mean(), 0)
                       for k in [300, 694, 1000]) + " |")
    A("")
    esc = e[e.clase == "escolar"]
    sup = e[e.clase == "superior"]
    A(f"La diferencia es grande y va en la dirección menos deseable. Dentro de "
      f"las mismas comunas, **{p(100*(sup.dist_existente_m<=300).mean(),0)} de "
      f"las sedes de educación superior** tiene una ciclovía a menos de 300 m, "
      f"contra apenas **{p(100*(esc.dist_existente_m<=300).mean(),0)} de los "
      f"establecimientos escolares**. La red acompaña la geografía del centro "
      f"urbano y de los campus, no la de los colegios, que es donde se "
      f"distribuye la población en edad escolar. Si el objetivo declarado "
      f"incluye el viaje al estudio, ese es el déficit más nítido que muestran "
      f"estos datos.\n")
    if len(esc):
        mat = esc.dropna(subset=["matricula"])
        if len(mat):
            cub = mat.dist_existente_m <= 300
            A(f"Ponderando por matrícula, los {n(len(mat))} establecimientos "
              f"escolares con matrícula declarada suman {n(mat.matricula.sum())} "
              f"estudiantes, de los cuales **{n(mat.loc[cub,'matricula'].sum())} "
              f"({p(100*mat.loc[cub,'matricula'].sum()/mat.matricula.sum(),0)})** "
              f"estudian a menos de 300 m de una ciclovía.\n")

    # ------------------------------------------------------------------ #
    A("## 5. Kilómetros no son red: la fragmentación\n")
    A("Un indicador de kilometraje no distingue entre una red que permite "
      "cruzar la ciudad y un conjunto de tramos sueltos. Para separarlos se "
      "construyó el grafo de la red existente uniendo tramos cuyas geometrías "
      "quedan a menos de una tolerancia, y se contaron las componentes conexas.\n")
    A("La tolerancia importa, así que se recorrió un rango en vez de fijarla:\n")
    A("| Tolerancia | Componentes | km de la mayor | % de la red | "
      "% componentes de un solo tramo |")
    A("|---:|---:|---:|---:|---:|")
    for _, r in sens.iterrows():
        A(f"| {r.tolerancia_m:.0f} m | {n(r.n_componentes)} | {n(r.km_mayor,1)} | "
          f"{p(r.pct_km_mayor)} | {p(r.pct_componentes_de_un_tramo)} |")
    A("")
    r20 = sens[sens.tolerancia_m == 20].iloc[0]
    A(f"Se adopta **20 m**, que es donde la curva se aplana: pasar de 20 a 50 m "
      f"apenas mueve la componente mayor, de modo que lo que queda separado a "
      f"20 m lo está por distancia real y no por imprecisión del trazado.\n")
    A(f"A esa tolerancia la red existente se parte en **{n(r20.n_componentes)} "
      f"componentes**. La mayor reúne {n(r20.km_mayor,1)} km, apenas el "
      f"**{p(r20.pct_km_mayor)} de la red**, y la mitad de las componentes no "
      f"pasa de **{n(comp.km.median(),2)} km** — menos que la distancia de un "
      f"viaje urbano corriente. El "
      f"**{p(r20.pct_componentes_de_un_tramo,0)}** de las componentes es un "
      f"tramo único que no empalma con nada.\n")
    A("Conviene subrayar que esto es una **cota inferior de la fragmentación**: "
      "el grafo une dos ciclovías que se cruzan aunque el cruce no esté "
      "habilitado para el viraje, de modo que la red real está al menos tan "
      "partida como aquí se reporta.\n")
    top = ccom.sort_values("km", ascending=False).head(12)
    nom = ex.drop_duplicates("cut_com").set_index("cut_com").comuna_txt
    top = top.assign(comuna=top.cut_com.map(nom))
    A("Las doce comunas con más kilómetros, y qué tan integrada está esa red:\n")
    A("| Comuna | km | Componentes | km de la mayor | % en la mayor |")
    A("|---|---:|---:|---:|---:|")
    for _, r in top.iterrows():
        A(f"| {r.comuna} | {n(r.km,1)} | {r.n_componentes:.0f} | "
          f"{n(r.km_componente_mayor,1)} | {p(r.pct_km_componente_mayor,0)} |")
    A("")
    A("La lectura no es que unas comunas estén bien y otras mal, sino que **el "
      "kilometraje y la integración son dos cosas distintas**: hay comunas con "
      "red comparable donde una concentra casi todo en un solo eje continuo y "
      "otra reparte lo mismo en decenas de fragmentos.\n")

    # ------------------------------------------------------------------ #
    A("## 6. Qué NO se puede afirmar con esto\n")
    A("- **No hay causalidad.** La asociación entre cercanía a la ciclovía y "
      "uso de la bicicleta admite las dos direcciones, y este dato no permite "
      "separarlas. Todo lo anterior son asociaciones observadas.\n")
    A("- **La cobertura es euclidiana, no de red.** La distancia se mide en "
      "línea recta desde el centroide de la manzana, no caminando o pedaleando "
      "por la vialidad. En trama urbana regular el sesgo es modesto, pero donde "
      "hay barreras —un río, una línea férrea, una autopista— la cercanía "
      "aparente sobrestima el acceso real.\n")
    A("- **El NSE es del territorio, no de la persona.** Es un índice de área "
      "pequeña por zona censal; atribuirlo a un individuo sería una falacia "
      "ecológica.\n")
    A("- **El modo de transporte del Censo es el principal**, declarado al "
      "trabajo o al estudio, no el total de viajes. No es comparable sin más "
      "con la partición modal de una encuesta origen–destino.\n")

    SALIDA.write_text("\n".join(L), encoding="utf-8")
    print(f"ANALISIS.md escrito ({len(L)} bloques)")


if __name__ == "__main__":
    main()
