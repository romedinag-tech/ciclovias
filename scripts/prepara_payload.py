# -*- coding: utf-8 -*-
"""
Arma el payload de datos del visor y lo deja en _work/payload.json.

Se separa del generador de HTML a proposito: el payload tarda minutos en
construirse porque lee toda la cadena de analisis, mientras que la maqueta se
itera decenas de veces. Teniendolos juntos, cada ajuste de diseño obligaba a
recalcular todo.

Uso:  python -X utf8 scripts/prepara_payload.py
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PQ = RAIZ / "data" / "parquet"
AN = RAIZ / "data" / "analisis"
OUT = RAIZ / "_work" / "payload.json"

RMG = Path(r"C:\Users\Rodrigo\Análisis RMG")
GIS = RMG / "GIS Gran Concepción" / "Analisis uso de suelo Gran Concepción"
P_COMUNAS = GIS / "proyecto_nacional" / "data" / "comunas.geojson"
P_METROS = GIS / "proyecto_nacional" / "data" / "metro_areas.json"

DEC = 5
TOL_RED = 0.00012        # ~13 m
TOL_ZONA = 0.00025       # ~28 m: la zona censal se ve a escala de ciudad
ETAPAS = ["existentes", "ejecución", "diseño", "planificadas"]


def nn(v, d=2):
    """Numero listo para JSON: None si no hay dato, redondeado si lo hay."""
    if v is None or (isinstance(v, float) and not np.isfinite(v)) or pd.isna(v):
        return None
    return round(float(v), d)


def coords_linea(g):
    if g is None or g.is_empty:
        return []
    partes = g.geoms if g.geom_type == "MultiLineString" else [g]
    return [[[round(y, DEC), round(x, DEC)] for x, y in p.coords]
            for p in partes if len(p.coords) >= 2]


def coords_poli(g, dec=4):
    """Poligono -> anillos [lat,lon] para Leaflet, solo el exterior."""
    if g is None or g.is_empty:
        return []
    partes = g.geoms if g.geom_type == "MultiPolygon" else [g]
    out = []
    for p in partes:
        c = [[round(y, dec), round(x, dec)] for x, y in p.exterior.coords]
        if len(c) >= 4:
            out.append(c)
    return out


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    D = {}

    # ------------------------------------------------------------------ #
    # 1. INFRAESTRUCTURA
    # ------------------------------------------------------------------ #
    panel = gpd.read_parquet(PQ / "catastro_panel.parquet")
    u = panel[panel.corte == "2026-07"].copy()

    # evolucion entre cortes: solo la red existente, que es la unica comparable
    ev = (panel[panel.existente].groupby("corte")
          .agg(km=("km", "sum"), tramos=("identifica", "size"),
               comunas=("cut_com", "nunique")).reset_index())
    D["evolucion"] = [{"corte": r.corte, "km": nn(r.km, 1), "tramos": int(r.tramos),
                       "comunas": int(r.comunas)} for r in ev.itertuples()]

    # km existentes por año declarado de ejecucion
    ex = u[u.existente].copy()
    ex["anio"] = pd.to_numeric(ex.year_ejecucion.astype(str).str.extract(r"(\d{4})")[0],
                               errors="coerce")
    ay = ex.dropna(subset=["anio"]).groupby("anio").agg(
        km=("km", "sum"), tramos=("identifica", "size")).reset_index()
    D["por_anio"] = [{"anio": int(r.anio), "km": nn(r.km, 1), "tramos": int(r.tramos)}
                     for r in ay.itertuples() if 1990 <= r.anio <= 2030]

    D["por_etapa"] = [{"etapa": e, "km": nn(u.loc[u.etapa == e, "km"].sum(), 1),
                       "tramos": int((u.etapa == e).sum())} for e in ETAPAS]

    tip = (u.groupby([u.tipo.fillna("sin dato"), u.existente]).km.sum()
             .unstack(fill_value=0).reset_index())
    tip.columns = ["tipo", "km_otras", "km_existentes"][:len(tip.columns)]
    tip["km_total"] = tip.iloc[:, 1:].sum(axis=1)
    D["por_tipo"] = [{"tipo": r.tipo, "km_existentes": nn(getattr(r, "km_existentes", 0), 1),
                      "km_total": nn(r.km_total, 1)}
                     for r in tip.sort_values("km_total", ascending=False).itertuples()][:12]

    emp = u[u.existente].groupby(u.emplaza_txt.fillna("sin dato")).km.sum() \
                        .sort_values(ascending=False)
    D["por_emplazamiento"] = [{"emplaza": k, "km": nn(v, 1)}
                              for k, v in emp.items()][:10]

    # ------------------------------------------------------------------ #
    # 2. INDICADORES POR COMUNA (alimenta mapa y fichas)
    # ------------------------------------------------------------------ #
    cob = pd.read_parquet(AN / "cobertura_comuna.parquet")
    ccom = pd.read_parquet(AN / "conectividad_comuna.parquet")
    cen = pd.read_parquet(AN / "demanda_comuna.parquet")
    km_et = (u.groupby(["cut_com", "etapa"]).km.sum().unstack(fill_value=0)
               .rename(columns=lambda c: f"km_{c}").reset_index())

    sb = pd.read_parquet(AN / "siniestros_bici.parquet")
    sin_com = sb.groupby("cut_com").agg(
        sin_bici=("id_accidente", "size"), sin_fall=("fallecidos", "sum"),
        sin_grav=("graves", "sum")).reset_index()

    ind = (cen[["cut_com", "COMUNA", "REGION", "n_transporte_bicicleta",
                "viajes_modo", "bici_pct"]]
           .rename(columns={"COMUNA": "nom", "REGION": "reg",
                            "n_transporte_bicicleta": "bici"})
           # `bici` existe en las dos tablas y un merge sin resolverla la parte en
           # bici_x/bici_y, dejando el KPI nacional en cero sin lanzar ningun
           # error. Se conserva la del Censo, que cubre las 334 comunas, y se
           # descarta la de cobertura, que solo cubre las que tienen red.
           .merge(cob.drop(columns=[c for c in ["COMUNA", "REGION", "bici",
                                                "escolares"]
                                    if c in cob.columns]),
                  on="cut_com", how="left")
           .merge(ccom, on="cut_com", how="left")
           .merge(km_et, on="cut_com", how="left")
           .merge(sin_com, on="cut_com", how="left"))

    # brecha de cobertura por NSE dentro de la comuna
    mz = pd.read_parquet(AN / "manzana_cobertura.parquet",
                         columns=["cut_com", "nse_score", "n_per", "AREA_C",
                                  "dist_existente_m"])
    mz = mz[(mz.AREA_C == "URBANO") & mz.nse_score.notna() & (mz.n_per > 0)]

    def brecha(d):
        if d.nse_score.nunique() < 5:
            return np.nan
        q = pd.qcut(d.nse_score, 5, labels=False, duplicates="drop")
        a, b = d[q == q.max()], d[q == 0]
        if not len(a) or not len(b) or not a.n_per.sum() or not b.n_per.sum():
            return np.nan
        f = lambda x: 100 * x.loc[x.dist_existente_m <= 300, "n_per"].sum() / x.n_per.sum()
        return f(a) - f(b)

    ind = ind.merge(mz.groupby("cut_com").apply(brecha, include_groups=False)
                      .rename("brecha_nse"), on="cut_com", how="left")

    campos = {"nom": "nom", "reg": "reg", "pob": "pob", "bici": "bici",
              # denominador de la participacion modal: sin el, el KPI agregado
              # no se puede calcular y cae en "s/d"
              "viajes_modo": "viajes_modo",
              "bici_pct": "bici_pct", "pct_pob_300": "cob", "pct_bici_300": "cobb",
              "km_existentes": "kme", "km_diseño": "kmd", "km_planificadas": "kmp",
              "km_ejecución": "kmj", "n_componentes": "ncomp",
              "pct_km_componente_mayor": "pmayor", "brecha_nse": "brecha",
              "nse_score_pob": "nse", "sin_bici": "sini", "sin_fall": "sinf",
              "sin_grav": "sing"}
    for c in campos:
        if c not in ind.columns:
            ind[c] = np.nan
    ind["cut_com"] = ind.cut_com.astype(str).str.zfill(5)

    D["comunas"] = {}
    for r in ind.itertuples():
        d = {}
        for src, dst in campos.items():
            v = getattr(r, src, None)
            d[dst] = v if src in ("nom", "reg") and isinstance(v, str) else nn(v)
        D["comunas"][r.cut_com] = d

    # ------------------------------------------------------------------ #
    # 3. DEMANDA
    # ------------------------------------------------------------------ #
    eod = pd.read_parquet(AN / "demanda_eod_ciudad.parquet")
    eod = eod[eod.separable == True]                                  # noqa: E712
    D["eod"] = [{
        "ciudad": r.ciudad, "anio": int(r.anio),
        "bici_pct": nn(r.bici_pct), "viajes": nn(r.viajes_exp, 0),
        "bici_viajes": nn(r.bici_exp, 0),
        "ofi": nn(r.ofi_bici_pct), "ok": bool(r.indice_consistente),
        "censo": nn(r.censo_bici_pct), "ncom": int(r.censo_comunas or 0),
    } for r in eod.sort_values("bici_pct", ascending=False).itertuples()]

    # Perfil horario POR CIUDAD: el contador no publica su curva horaria, asi
    # que en su ficha se muestra la de la EOD de esa ciudad, declarada como
    # fuente distinta y como patron urbano, no como medicion del punto.
    perf = pd.read_parquet(AN / "demanda_eod_perfil.parquet")
    ph = perf[perf.dim == "hora"]
    D["eod_hora_ciudad"] = {}
    for ciu, g in ph.groupby("ciudad"):
        v = [0.0] * 24
        for _, r in g.iterrows():
            try:
                h = int(float(r.valor))
            except (TypeError, ValueError):
                continue
            if 0 <= h < 24:
                v[h] += float(r.viajes or 0)
        if sum(v):
            D["eod_hora_ciudad"][str(ciu)] = [round(x, 1) for x in v]
    D["eod_perfil"] = {}
    for dim in perf.dim.unique():
        s = perf[perf.dim == dim].groupby("valor").viajes.sum().sort_values(ascending=False)
        D["eod_perfil"][dim] = [{"v": str(k), "n": nn(x, 0)} for k, x in s.items()][:30]


    # Cruces de la EOD: participacion de la bicicleta por edad, sexo, quintil,
    # proposito, periodo y hora, por ciudad. Lo que se publica es la
    # PARTICIPACION dentro de cada grupo, no el volumen: los grupos tienen
    # tamaños muy distintos y el volumen bruto hablaria del tamaño, no de la
    # propension a pedalear.
    fx = AN / "eod_cruces.parquet"
    if fx.exists():
        cx = pd.read_parquet(fx)
        D["cruces"] = {}
        for (ciu, dim), g in cx.groupby(["ciudad", "dim"]):
            D["cruces"].setdefault(str(ciu), {})[str(dim)] = [
                {"v": str(r.valor), "b": nn(r.bici, 0), "t": nn(r.total, 0),
                 "p": nn(r.part)} for r in g.itertuples()]
        nac = cx.groupby(["dim", "valor"]).agg(
            bici=("bici", "sum"), total=("total", "sum")).reset_index()
        nac["part"] = 100 * nac.bici / nac.total.replace(0, np.nan)
        D["cruces_nac"] = {}
        for dim, g in nac.groupby("dim"):
            D["cruces_nac"][str(dim)] = [
                {"v": str(r.valor), "b": nn(r.bici, 0), "t": nn(r.total, 0),
                 "p": nn(r.part)} for r in g.itertuples()]

    ct = gpd.read_parquet(PQ / "minvu_contadores.parquet")
    D["contadores"] = [{
        "n": (str(r.NOMBRE_CONTADOR) if pd.notna(r.NOMBRE_CONTADOR) else "")[:50],
        "c": str(r.CUT_COM or "").zfill(5),
        "m": nn(r.Media_diaria, 1), "x": nn(r.Max_diaria, 0),
        "hab": nn(r.Promedio_dia_de_semana, 1), "fds": nn(r.Promedio_fin_de_semana, 1),
        "sem": nn(r.Media_semanal, 0), "prov": str(r.PROVEEDOR or "")[:20],
        "d0": str(r.Primera_fecha_iso)[:10] if pd.notna(r.Primera_fecha_iso) else None,
        "d1": str(r.Ultima_fecha_iso)[:10] if pd.notna(r.Ultima_fecha_iso) else None,
        "ll": [round(r.geometry.y, DEC), round(r.geometry.x, DEC)],
    } for r in ct.itertuples() if r.geometry is not None]

    # Mediciones SECTRA por punto de control. Es la unica fuente con reparto
    # DENTRO del dia asociado a un punto concreto: fuera de punta, punta mañana
    # y punta tarde. Los contadores MINVU solo publican agregados diarios.
    med = gpd.read_parquet(PQ / "sectra_mediciones_antofagasta_talca.parquet")
    D["mediciones"] = [{
        "pc": int(r.PC) if pd.notna(r.PC) else None,
        "com": str(r.Comuna or ""),
        "fp": nn(r.FP, 0), "pm": nn(r.PM, 0), "pt": nn(r.PT, 0),
        "tot": nn(r.Tot_cicl, 0),
        "exp": nn(r.expan_ciclos, 0), "expv": nn(r.expan_veh, 0),
        "prop": nn(r.propor_, 3),
        "ll": [round(r.geometry.y, DEC), round(r.geometry.x, DEC)],
    } for r in med.itertuples() if r.geometry is not None]

    # ------------------------------------------------------------------ #
    # 4. ESPACIAL
    # ------------------------------------------------------------------ #
    red = u.copy()
    red["geometry"] = red.geometry.simplify(TOL_RED, preserve_topology=False)
    D["red"] = [{
        "e": ETAPAS.index(r.etapa) if r.etapa in ETAPAS else 3,
        "c": (str(r.cut_com) if pd.notna(r.cut_com) else "")[:5],
        "n": (str(r.eje_via) if pd.notna(r.eje_via) else "")[:55],
        "k": nn(r.km), "t": (str(r.tipo) if pd.notna(r.tipo) else "")[:30],
        "a": (str(r.year_ejecucion) if pd.notna(r.year_ejecucion) else "")[:4],
        "em": (str(r.emplaza_txt) if pd.notna(r.emplaza_txt) else "")[:18],
        "g": coords_linea(r.geometry),
    } for r in red.itertuples()]
    D["red"] = [t for t in D["red"] if t["g"]]

    gz = gpd.read_parquet(AN / "zona_demanda.parquet")
    gz["geometry"] = gz.geometry.simplify(TOL_ZONA, preserve_topology=False)
    D["zonas"] = [{
        "z": r.zona, "c": str(r.cut_com or "").zfill(5),
        "nom": (str(r.comuna) if pd.notna(r.comuna) else "")[:28],
        "pob": nn(r.pob, 0), "bici": nn(r.bici, 0), "bp": nn(r.bici_pct),
        "cob": nn(r.cob_pct), "d": nn(r.dist_m, 0), "nse": nn(r.nse_score),
        "esc": nn(r.escolares, 0),
        "sini": nn(getattr(r, "sin_bici", None), 0),
        "sinf": nn(getattr(r, "sin_fall", None), 0),
        "g": coords_poli(r.geometry),
    } for r in gz.itertuples()]
    D["zonas"] = [z for z in D["zonas"] if z["g"]]

    D["siniestros"] = [{
        "a": int(r.anio) if pd.notna(r.anio) else None,
        "h": int(r.hora) if pd.notna(r.hora) else None,
        "c": str(r.cut_com or ""),
        "f": int(r.fallecidos or 0), "gr": int(r.graves or 0),
        "t": (str(r.tipo_final) if pd.notna(r.tipo_final) else "")[:26],
        "ll": [round(float(r.lat), DEC), round(float(r.lon), DEC)],
    } for r in sb.itertuples()]

    # siniestros por año y por hora, para los graficos
    D["sin_anio"] = [{"anio": int(a), "n": int(n)}
                     for a, n in sb.groupby("anio").size().items()]
    D["sin_hora"] = [{"hora": int(h), "n": int(n)}
                     for h, n in sb.dropna(subset=["hora"]).groupby("hora").size().items()]
    D["sin_tipo"] = [{"tipo": str(t)[:30], "n": int(n)} for t, n in
                     sb.tipo_final.value_counts().head(10).items()]

    eq = pd.read_parquet(AN / "equipamiento_cobertura.parquet")
    D["equip"] = [{
        "n": (str(r.nombre) if pd.notna(r.nombre) else "")[:46],
        "c": str(r.cut_com or ""), "k": 0 if r.clase == "escolar" else 1,
        "d": nn(r.dist_existente_m, 0),
        "m": int(r.matricula) if pd.notna(r.matricula) else None,
        "ll": [round(float(r.lat), DEC), round(float(r.lon), DEC)],
    } for r in eq.itertuples()]


    D["etiquetas"] = {
        "tipo": {
            "ciclovía": "Ciclovía",
            "smp": "Senda multipropósito (MOP)",
            "s_i": "Sin información",
            "zona30": "Zona 30",
            "cicloparque": "Cicloparque",
            "ciclovía temporal/piloto": "Ciclovía temporal o piloto",
            "via verde": "Vía verde",
            "zona30/contraflujo": "Zona 30 con contraflujo",
            "ciclovía (rediseño cruce)": "Ciclovía con rediseño de cruce",
        },
        "emplaza": {"s_i": "Sin información"},
        "nota_smp": ("«Senda multipropósito» es la infraestructura del MOP en la "
                     "berma de una ruta rural, compartida por peatones y "
                     "ciclistas. No está declarada como tal en el servicio: se "
                     "dedujo del propio catastro, donde los nombres de proyecto "
                     "de esos tramos dicen «construcción de sendas "
                     "multipropósito en red vial» y el 88 % de ellos son "
                     "cartera MOP en camino rural."),
    }

    # ------------------------------------------------------------------ #
    # 5. GEOMETRIA COMUNAL Y METROS (activos en solo lectura)
    # ------------------------------------------------------------------ #
    gj = json.loads(P_COMUNAS.read_text(encoding="utf-8"))
    feats = []
    for f in gj["features"]:
        pr = f.get("properties", {})
        cut = str(pr.get("cut") or pr.get("CUT") or "").split(".")[0].zfill(5)
        if cut not in D["comunas"]:
            continue

        def red_(o):
            if isinstance(o, float):
                return round(o, 4)
            if isinstance(o, list):
                return [red_(x) for x in o]
            return o
        f["properties"] = {"cut": cut,
                           "nom": pr.get("comuna") or pr.get("Comuna") or ""}
        f["geometry"]["coordinates"] = red_(f["geometry"]["coordinates"])
        feats.append(f)
    D["comunasGeo"] = {"type": "FeatureCollection", "features": feats}

    # Componente -> comunas que toca. Permite contar fragmentos DISTINTOS en un
    # territorio filtrado; sumar los conteos comunales sobrecuenta, porque la
    # componente mayor cruza 19 comunas y se contaria 19 veces.
    tc = pd.read_parquet(AN / "tramo_componente.parquet")
    tc["cut_com"] = tc.cut_com.astype(str).str.zfill(5)
    D["compComunas"] = {str(k): sorted(set(v))
                        for k, v in tc.groupby("componente").cut_com.apply(list).items()}
    D["compKm"] = {str(k): nn(v, 2)
                   for k, v in tc.groupby("componente").km_m.sum().items()}

    D["metros"] = {}
    if P_METROS.exists():
        try:
            D["metros"] = json.loads(P_METROS.read_text(encoding="utf-8")).get("metros", {})
        except Exception:                                   # noqa: BLE001
            pass


    # Ciudad EOD -> comunas, para que al filtrar por comuna o area metropolitana
    # el visor sepa que ciudad de la EOD corresponde resaltar.
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from analisis_demanda import CIUDAD_COMUNAS, norm as _norm
        idx = {}
        for c, d in D["comunas"].items():
            idx.setdefault(_norm(d.get("nom") or ""), []).append(c)
        D["eod_comunas"] = {}
        for ciu, nombres in CIUDAD_COMUNAS.items():
            cuts = [c for n in nombres for c in idx.get(_norm(n), [])]
            if cuts:
                D["eod_comunas"][ciu] = sorted(cuts)
    except Exception as e:                                   # noqa: BLE001
        print("  aviso: no se pudo mapear ciudad EOD -> comunas:", e)
        D["eod_comunas"] = {}

    txt = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(txt, encoding="utf-8")
    print(f"payload -> {OUT}  {len(txt)/1e6:.2f} MB")
    for k in ["red", "zonas", "siniestros", "equip", "contadores", "eod"]:
        print(f"  {k:12s} {len(D[k]):>7,}")
    print(f"  {'comunas':12s} {len(D['comunas']):>7,} | geometrias "
          f"{len(D['comunasGeo']['features']):,}")


if __name__ == "__main__":
    main()
