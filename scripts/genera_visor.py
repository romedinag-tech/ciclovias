# -*- coding: utf-8 -*-
"""
Genera el visor de ciclovias: un unico index.html autocontenido.

Por que NO usa `_dashboard_kit/lib_dashboard.py`. El motor del kit construye su
capa de datos a partir de puntos por rol del catastro SII (lat/lon, valor,
superficie, año) y sus "unidades" son lentes sobre esos puntos con umbrales de
tamaño. No tiene el concepto de una capa LINEAL, que es exactamente el centro de
un visor de ciclovias, ni de componentes conexas. Forzar una red de 4.850 tramos
dentro de ese contrato seria improvisar una variante del estandar en vez de
usarlo. Lo que si se reutiliza es su ESTANDAR GRAFICO —paleta, layout de panel
izquierdo de 370 px, mapa Leaflet con base y satelite, selector territorial con
buscador y coropleta por quintiles—, leido de `plantilla.html` en solo lectura.
Queda declarado en CLAUDE.md.

Todo va incrustado en un solo archivo: nada de rutas relativas a datos o
imagenes, de modo que el HTML se pueda mandar por correo y siga funcionando.

Uso:  python -X utf8 scripts/genera_visor.py
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PQ = RAIZ / "data" / "parquet"
AN = RAIZ / "data" / "analisis"
SALIDA = RAIZ / "index.html"

RMG = Path(r"C:\Users\Rodrigo\Análisis RMG")
GIS = RMG / "GIS Gran Concepción" / "Analisis uso de suelo Gran Concepción"
P_COMUNAS = GIS / "proyecto_nacional" / "data" / "comunas.geojson"
P_METROS = GIS / "proyecto_nacional" / "data" / "metro_areas.json"

VERSION = 1
TOL_SIMPL = 0.00012      # ~13 m en latitud: bajo el ancho de una calzada
DEC = 5                  # 5 decimales ~ 1 m


def redondea(obj, d=DEC):
    if isinstance(obj, float):
        return round(obj, d)
    if isinstance(obj, list):
        return [redondea(x, d) for x in obj]
    return obj


def geom_a_coords(g):
    """LineString / MultiLineString -> lista de listas [lat, lon] para Leaflet."""
    if g is None or g.is_empty:
        return []
    partes = g.geoms if g.geom_type == "MultiLineString" else [g]
    return [[[round(y, DEC), round(x, DEC)] for x, y in p.coords]
            for p in partes if len(p.coords) >= 2]


def main():
    # ------------------------------------------------------------------ #
    # Red
    # ------------------------------------------------------------------ #
    panel = gpd.read_parquet(PQ / "catastro_panel.parquet")
    red = panel[panel.corte == "2026-07"].copy()
    red["geometry"] = red.geometry.simplify(TOL_SIMPL, preserve_topology=False)

    comp = pd.read_parquet(AN / "componentes.parquet")
    # se recalcula la etiqueta de componente sobre el mismo orden de tramos
    ex_idx = red.index[red.existente]
    comp_km = dict(zip(comp.componente, comp.km))

    con_comp = gpd.read_parquet(PQ / "catastro_panel.parquet")
    del con_comp

    def txt(v, n=60):
        """Los campos de texto llegan como pandas.NA en algunos cortes, y `NA or
        ""` levanta TypeError en vez de caer al valor por defecto."""
        return "" if v is None or pd.isna(v) else str(v)[:n]

    tramos = []
    for i, r in red.iterrows():
        cs = geom_a_coords(r.geometry)
        if not cs:
            continue
        tramos.append({
            "e": {"existentes": 0, "ejecución": 1, "diseño": 2,
                  "planificadas": 3}.get(r.etapa, 3),
            "c": txt(r.cut_com, 5),
            "n": txt(r.eje_via, 60),
            "k": round(float(0 if pd.isna(r.km) else r.km), 2),
            "t": txt(r.tipo, 24),
            "a": txt(r.year_ejecucion, 4),
            "g": cs,
        })
    print(f"tramos en el visor: {len(tramos):,}")

    # ------------------------------------------------------------------ #
    # Indicadores comunales
    # ------------------------------------------------------------------ #
    cob = pd.read_parquet(AN / "cobertura_comuna.parquet")
    ccom = pd.read_parquet(AN / "conectividad_comuna.parquet")
    km_etapa = (red.groupby(["cut_com", "etapa"]).km.sum().unstack(fill_value=0)
                  .rename(columns=lambda c: f"km_{c}").reset_index())

    ind = cob.merge(ccom, on="cut_com", how="outer").merge(
        km_etapa, on="cut_com", how="outer")

    # brecha NSE dentro de la comuna: cobertura del quintil alto menos la del bajo
    mz = pd.read_parquet(AN / "manzana_cobertura.parquet",
                         columns=["cut_com", "nse_score", "n_per", "AREA_C",
                                  "dist_existente_m", "n_transporte_bicicleta"])
    mz = mz[(mz.AREA_C == "URBANO") & mz.nse_score.notna() & (mz.n_per > 0)]

    def brecha(d):
        if d.nse_score.nunique() < 5:
            return np.nan
        q = pd.qcut(d.nse_score, 5, labels=False, duplicates="drop")
        alto, bajo = d[q == q.max()], d[q == 0]
        if not len(alto) or not len(bajo) or not alto.n_per.sum() or not bajo.n_per.sum():
            return np.nan
        f = lambda x: 100 * x.loc[x.dist_existente_m <= 300, "n_per"].sum() / x.n_per.sum()
        return f(alto) - f(bajo)

    br = mz.groupby("cut_com").apply(brecha, include_groups=False).rename("brecha_nse")
    ind = ind.merge(br, on="cut_com", how="left")

    ind = ind.replace([np.inf, -np.inf], np.nan)
    campos = ["pob", "bici", "pct_pob_300", "pct_bici_300", "km",
              "n_componentes", "pct_km_componente_mayor", "brecha_nse",
              "km_existentes", "km_diseño", "km_planificadas", "km_ejecución",
              "nse_score_pob"]
    for c in campos:
        if c not in ind.columns:
            ind[c] = np.nan
    ind["cut_com"] = ind["cut_com"].astype(str).str.zfill(5)
    indic = {r.cut_com: {c: (None if pd.isna(getattr(r, c))
                            else round(float(getattr(r, c)), 2))
                         for c in campos}
             for r in ind.itertuples()}

    # ------------------------------------------------------------------ #
    # Comunas (geometria) — activo de otro proyecto, en solo lectura
    # ------------------------------------------------------------------ #
    gj = json.loads(P_COMUNAS.read_text(encoding="utf-8"))
    feats = []
    for f in gj["features"]:
        pr = f.get("properties", {})
        cut = str(pr.get("cut") or pr.get("CUT") or
                  pr.get("cut_com") or "").split(".")[0].zfill(5)
        if cut not in indic:
            continue
        f["properties"] = {"cut": cut,
                           "nom": pr.get("comuna") or pr.get("Comuna") or ""}
        f["geometry"]["coordinates"] = redondea(f["geometry"]["coordinates"], 4)
        feats.append(f)
    comunas_gj = {"type": "FeatureCollection", "features": feats}
    print(f"comunas con geometria e indicador: {len(feats)}")

    metros = {}
    if P_METROS.exists():
        try:
            metros = json.loads(P_METROS.read_text(encoding="utf-8")).get("metros", {})
        except Exception:                       # noqa: BLE001
            metros = {}

    # ------------------------------------------------------------------ #
    # Contadores y equipamiento
    # ------------------------------------------------------------------ #
    ct = gpd.read_parquet(PQ / "minvu_contadores.parquet")
    contadores = [{
        "n": txt(r.NOMBRE_CONTADOR, 50),
        "c": str(r.CUT_COM or "").zfill(5),
        "m": None if pd.isna(r.Media_diaria) else round(float(r.Media_diaria), 1),
        "x": None if pd.isna(r.Max_diaria) else float(r.Max_diaria),
        "hab": None if pd.isna(r.Promedio_dia_de_semana) else round(float(r.Promedio_dia_de_semana), 1),
        "fds": None if pd.isna(r.Promedio_fin_de_semana) else round(float(r.Promedio_fin_de_semana), 1),
        "p": txt(r.PROVEEDOR, 30),
        "ll": [round(r.geometry.y, DEC), round(r.geometry.x, DEC)],
    } for r in ct.itertuples() if r.geometry is not None]

    eq = pd.read_parquet(AN / "equipamiento_cobertura.parquet")
    eq = eq[eq.dist_existente_m.notna()]
    equip = [{
        "n": txt(r.nombre, 50),
        "c": str(r.cut_com or ""),
        "k": 0 if r.clase == "escolar" else 1,
        "d": round(float(r.dist_existente_m)),
        "m": None if pd.isna(r.matricula) else int(r.matricula),
        "ll": [round(float(r.lat), DEC), round(float(r.lon), DEC)],
    } for r in eq.itertuples()]
    print(f"contadores {len(contadores)} | establecimientos {len(equip):,}")

    DATA = {
        "version": VERSION,
        "tramos": tramos,
        "comunas": comunas_gj,
        "indic": indic,
        "metros": metros,
        "contadores": contadores,
        "equip": equip,
    }

    html = PLANTILLA.replace("/*__DATA__*/", json.dumps(DATA, ensure_ascii=False,
                                                        separators=(",", ":")))
    SALIDA.write_text(html, encoding="utf-8")
    print(f"-> {SALIDA.name}  {SALIDA.stat().st_size/1e6:.1f} MB")


PLANTILLA = r"""<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Visor de ciclovías de Chile — red, cobertura y conectividad</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root{--ink:#1a1f2b;--mut:#667;--line:#e3e6ec;--bg:#f6f7f9;--acc:#c05a00}
*{box-sizing:border-box} html,body{margin:0;height:100%;font-family:system-ui,'Segoe UI',Roboto,sans-serif;color:var(--ink)}
#app{display:flex;height:100vh} #map{flex:1;height:100%;background:#dfe4ea}
#side{width:370px;max-width:46vw;border-right:1px solid var(--line);display:flex;flex-direction:column;background:#fff}
header{padding:14px 16px;border-bottom:1px solid var(--line)}
h1{font-size:16px;margin:0 0 4px} .sub{font-size:12px;color:var(--mut);line-height:1.35}
select,#cbox{width:100%;padding:8px;border:1px solid var(--line);border-radius:8px;font-size:13px;background:#fff;color:var(--ink)}
#selInd{margin:8px 0;padding:9px;border:1.5px solid var(--acc);font-weight:700;color:var(--acc)}
.searchw{position:relative;margin-top:8px}
#clist{position:absolute;left:0;right:0;top:39px;z-index:1000;background:#fff;border:1px solid var(--line);border-radius:8px;max-height:280px;overflow:auto;box-shadow:0 8px 24px rgba(0,0,0,.14);display:none}
#clist .ci{padding:7px 10px;font-size:13px;cursor:pointer;border-bottom:1px solid #f2f4f7}
#clist .ci:hover{background:var(--bg)} .ci .rg{color:var(--mut);font-size:11px;float:right}
.lyr{display:flex;gap:12px;flex-wrap:wrap;margin-top:10px;font-size:12.5px;color:var(--mut)}
.lyr label{display:flex;align-items:center;gap:5px;cursor:pointer}
#panel{padding:14px 16px;overflow:auto;flex:1}
#panel h2{font-size:15px;margin:0 0 4px} .stat{font-size:13px;color:var(--mut);margin:5px 0} .stat b{color:var(--ink);font-size:15px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}
.card{border:1px solid var(--line);border-radius:8px;padding:8px 10px;background:var(--bg)}
.card .v{font-size:17px;font-weight:700} .card .l{font-size:11px;color:var(--mut);line-height:1.25}
.hint{color:var(--mut);font-size:12.5px;margin-top:14px;line-height:1.45}
.leg{padding:10px 16px;border-top:1px solid var(--line);font-size:11px;color:var(--mut)}
.leg .row{display:flex;align-items:center;gap:6px;margin:2px 0}
.sw{width:14px;height:4px;border-radius:2px;display:inline-block} .sq{width:13px;height:13px;border-radius:3px;display:inline-block}
.foot{padding:8px 16px;border-top:1px solid var(--line);font-size:10.5px;color:#99a;line-height:1.4}
.bar{height:6px;background:#e9ecf1;border-radius:3px;overflow:hidden;margin-top:3px}
.bar i{display:block;height:100%;background:var(--acc)}
@media(max-width:820px){#app{flex-direction:column}#side{width:100%;max-width:none;height:52vh}#map{height:48vh}}
</style></head><body>
<div id="app">
 <div id="side">
  <header>
   <h1>Ciclovías de Chile</h1>
   <div class="sub">Catastro Nacional SECTRA/MTT (corte jul-2026) cruzado con Censo 2024 por manzana, NSE por zona censal y catastro MINEDUC.</div>
   <select id="selInd"></select>
   <div class="searchw">
     <input id="cbox" placeholder="Buscar comuna o área metropolitana…" autocomplete="off">
     <div id="clist"></div>
   </div>
   <div class="lyr">
     <label><input type="checkbox" id="lRed" checked> Red</label>
     <label><input type="checkbox" id="lPlan"> Cartera</label>
     <label><input type="checkbox" id="lCont"> Contadores</label>
     <label><input type="checkbox" id="lEq"> Colegios y U.</label>
   </div>
  </header>
  <div id="panel"></div>
  <div class="leg" id="leg"></div>
  <div class="foot">Fuentes: Catastro Nacional de Ciclovías (SECTRA/Programa de Vialidad y Transporte Urbano, MTT) · Contadores de flujo (MINVU–DDU) · Censo 2024 (INE) · Directorio de establecimientos (MINEDUC). Elaboración propia. Las distancias son euclidianas desde el centroide de la manzana.</div>
 </div>
 <div id="map"></div>
</div>
<script>
const DATA = /*__DATA__*/;
const ETAPAS=['existentes','ejecución','diseño','planificadas'];
const COLE=['#1b6ca8','#e08a1e','#8e7cc3','#9aa5b1'];

const INDICADORES=[
 {k:'pct_pob_300', t:'Cobertura: % de población a 300 m de la red', u:'%', inv:false,
  d:'Porcentaje de habitantes cuya manzana censal tiene su centroide a menos de 300 m de un tramo existente. 300 m es el umbral que usa el índice de ciclo-inclusión de SECTRA.'},
 {k:'pct_bici_300', t:'Cobertura de quienes ya pedalean (%)', u:'%', inv:false,
  d:'Mismo cálculo, pero sobre las personas que declaran la bicicleta como modo principal al trabajo o al estudio en el Censo 2024.'},
 {k:'km_existentes', t:'Kilómetros de red existente', u:' km', inv:false,
  d:'Suma del kilometraje declarado de los tramos en etapa existentes.'},
 {k:'pct_km_componente_mayor', t:'Integración: % de km en la componente mayor', u:'%', inv:false,
  d:'Qué proporción de los kilómetros de la comuna pertenece al fragmento conectado más grande. Un valor bajo significa muchos tramos sueltos que no permiten un viaje continuo.'},
 {k:'n_componentes', t:'Número de fragmentos desconectados', u:'', inv:true,
  d:'Componentes conexas de la red existente en la comuna, uniendo tramos cuyas geometrías quedan a menos de 20 m.'},
 {k:'brecha_nse', t:'Brecha de cobertura por NSE (puntos)', u:' pts', inv:true,
  d:'Cobertura a 300 m del quintil socioeconómico más alto de la comuna menos la del más bajo. Positivo significa que la infraestructura favorece a las manzanas de mayor nivel.'},
 {k:'bici', t:'Personas que usan la bicicleta', u:'', inv:false,
  d:'Censo 2024, modo principal de transporte al trabajo o al estudio.'}
];

const map=L.map('map',{preferCanvas:true}).setView([-35.5,-71.3],5);
// Esri World_Gray_Canvas y World_Imagery se sirven sin clave. Se evita
// basemaps.cartocdn.com, que desde 2025 responde teselas con la marca
// "API KEY REQUIRED" y deja el mapa ilegible sin lanzar ningun error.
const base=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
  {attribution:'Esri, HERE, Garmin, &copy; OpenStreetMap',maxZoom:16}).addTo(map);
const osm=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  {attribution:'&copy; OpenStreetMap',maxZoom:19});
const sat=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  {attribution:'Esri',maxZoom:19});
L.control.layers({'Mapa claro':base,'Calles (OSM)':osm,'Satélite':sat},null,
                 {position:'topright'}).addTo(map);

// El orden de dibujo se fija con panes de z-index, no llamando bringToFront:
// capaRed es un LayerGroup y ese metodo no existe en LayerGroup, lo que rompia
// el script justo antes de pintar el panel y la leyenda.
map.createPane('pComunas').style.zIndex=350;   // coropleta, bajo todo lo demas
map.createPane('pRed').style.zIndex=420;       // la red, sobre la coropleta
map.createPane('pPtos').style.zIndex=460;      // contadores y equipamiento arriba

let indActual=INDICADORES[0], cortes=[], capaCom, comSel=null;

function valores(){return Object.values(DATA.indic).map(d=>d[indActual.k]).filter(v=>v!==null&&v!==undefined&&isFinite(v));}
function quintiles(v){v=v.slice().sort((a,b)=>a-b);return [.2,.4,.6,.8].map(p=>v[Math.floor(p*(v.length-1))]);}
const PAL=['#f2e6d8','#e5c39a','#d69a5f','#c47430','#a4530d'];
function color(v){if(v===null||v===undefined||!isFinite(v))return '#eef0f3';
  let i=0;while(i<cortes.length&&v>cortes[i])i++;return indActual.inv?PAL[4-i]:PAL[i];}
function fmt(v,d){if(v===null||v===undefined||!isFinite(v))return 's/d';
  return v.toLocaleString('es-CL',{minimumFractionDigits:d,maximumFractionDigits:d});}

function pintaComunas(){
  cortes=quintiles(valores());
  if(capaCom) map.removeLayer(capaCom);
  capaCom=L.geoJSON(DATA.comunas,{
    pane:'pComunas',
    style:f=>{const d=DATA.indic[f.properties.cut]||{};
      return {fillColor:color(d[indActual.k]),fillOpacity:.72,color:'#fff',weight:.6};},
    onEachFeature:(f,l)=>{
      const c=f.properties.cut,d=DATA.indic[c]||{};
      l.bindTooltip(`<b>${f.properties.nom}</b><br>${indActual.t}: ${fmt(d[indActual.k],1)}${indActual.u}`,{sticky:true});
      l.on('click',()=>{seleccionar(c,f.properties.nom,l.getBounds());});
    }}).addTo(map);
  leyenda();
}

function leyenda(){
  const c=cortes,u=indActual.u;
  let h=`<div style="font-weight:600;color:var(--ink);margin-bottom:4px">${indActual.t}</div>`;
  const et=[`≤ ${fmt(c[0],1)}${u}`,`≤ ${fmt(c[1],1)}${u}`,`≤ ${fmt(c[2],1)}${u}`,`≤ ${fmt(c[3],1)}${u}`,`> ${fmt(c[3],1)}${u}`];
  et.forEach((e,i)=>{h+=`<div class="row"><span class="sq" style="background:${indActual.inv?PAL[4-i]:PAL[i]}"></span>${e}</div>`;});
  h+=`<div class="row" style="margin-top:6px"><span class="sq" style="background:#eef0f3"></span>sin dato</div>`;
  h+=`<div style="margin-top:8px;font-weight:600;color:var(--ink)">Red</div>`;
  ETAPAS.forEach((e,i)=>{h+=`<div class="row"><span class="sw" style="background:${COLE[i]}"></span>${e}</div>`;});
  h+=`<div style="margin-top:8px;font-weight:600;color:var(--ink)">Puntos</div>
      <div class="row"><span class="sq" style="background:#14b8a6;border-radius:50%"></span>contador de flujo — el tamaño es la media diaria de pasadas</div>
      <div class="row"><span class="sq" style="background:#22c55e;border-radius:50%"></span>colegio o sede a menos de 300 m de la red</div>
      <div class="row"><span class="sq" style="background:#ef4444;border-radius:50%"></span>colegio o sede a más de 300 m</div>
      <div class="row" style="margin-top:4px;color:#99a">El círculo grande corresponde a educación superior; el pequeño, a un establecimiento escolar.</div>`;
  document.getElementById('leg').innerHTML=h;
}

let capaRed=L.layerGroup().addTo(map), capaPlan=L.layerGroup(), capaCont=L.layerGroup(), capaEq=L.layerGroup();
function dibujaRed(){
  capaRed.clearLayers(); capaPlan.clearLayers();
  DATA.tramos.forEach(t=>{
    const destino = t.e===0 ? capaRed : capaPlan;
    const est={pane:'pRed',color:COLE[t.e],weight:t.e===0?2.6:1.8,
               opacity:t.e===0?.95:.75,dashArray:t.e>=2?'4,4':null};
    t.g.forEach(p=>{
      const ln=L.polyline(p,est);
      ln.bindTooltip(`<b>${t.n||'(sin nombre de eje)'}</b><br>${ETAPAS[t.e]} · ${t.t}<br>${fmt(t.k,2)} km${t.a?' · '+t.a:''}`,{sticky:true});
      destino.addLayer(ln);
    });
  });
}
function dibujaPuntos(){
  capaCont.clearLayers(); capaEq.clearLayers();
  DATA.contadores.forEach(c=>{
    const r=c.m?Math.max(4,Math.min(16,Math.sqrt(c.m)*.65)):4;
    L.circleMarker(c.ll,{pane:'pPtos',radius:r,color:'#0f766e',weight:1.4,fillColor:'#14b8a6',fillOpacity:.75})
     .bindTooltip(`<b>${c.n}</b><br>Media diaria: ${fmt(c.m,1)} pasadas<br>Día hábil ${fmt(c.hab,0)} · fin de semana ${fmt(c.fds,0)}<br>Máximo ${fmt(c.x,0)} · ${c.p}`,{sticky:true})
     .addTo(capaCont);
  });
  DATA.equip.forEach(e=>{
    const cerca=e.d<=300;
    L.circleMarker(e.ll,{pane:'pPtos',radius:e.k?5:3,color:cerca?'#166534':'#b91c1c',weight:1,
      fillColor:cerca?'#22c55e':'#ef4444',fillOpacity:.8})
     .bindTooltip(`<b>${e.n}</b><br>${e.k?'Educación superior':'Establecimiento escolar'}<br>A ${fmt(e.d,0)} m de la red${e.m?'<br>Matrícula '+fmt(e.m,0):''}`,{sticky:true})
     .addTo(capaEq);
  });
}

function seleccionar(cut,nom,bounds){
  comSel=cut?{cut,nom}:null;
  if(bounds) map.fitBounds(bounds,{padding:[24,24]});
  panel();
}

function panel(){
  const p=document.getElementById('panel');
  if(!comSel){
    const t={}; ['pob','bici','km_existentes','km_diseño','km_planificadas'].forEach(k=>
      t[k]=Object.values(DATA.indic).reduce((a,d)=>a+(d[k]||0),0));
    const cub=Object.entries(DATA.indic).reduce((a,[c,d])=>a+((d.pct_pob_300||0)/100*(d.pob||0)),0);
    p.innerHTML=`<h2>Chile — resumen nacional</h2>
      <div class="grid">
        <div class="card"><div class="v">${fmt(t.km_existentes,0)} km</div><div class="l">red existente</div></div>
        <div class="card"><div class="v">${fmt(t.km_diseño+t.km_planificadas,0)} km</div><div class="l">en diseño o planificados</div></div>
        <div class="card"><div class="v">${fmt(100*cub/t.pob,1)} %</div><div class="l">población a 300 m de la red</div></div>
        <div class="card"><div class="v">${fmt(t.bici,0)}</div><div class="l">personas que usan la bicicleta</div></div>
      </div>
      <div class="hint">${indActual.d}</div>
      <div class="hint">Haz clic en una comuna del mapa o búscala arriba para ver su ficha. El color del mapa corresponde al indicador seleccionado.</div>`;
    return;
  }
  const d=DATA.indic[comSel.cut]||{};
  const barra=(v,max)=>`<div class="bar"><i style="width:${Math.max(0,Math.min(100,100*v/max))}%"></i></div>`;
  p.innerHTML=`<h2>${comSel.nom}</h2>
   <div class="sub" style="color:var(--mut);font-size:12px">CUT ${comSel.cut} · ${fmt(d.pob,0)} habitantes</div>
   <div class="grid">
     <div class="card"><div class="v">${fmt(d.km_existentes,1)} km</div><div class="l">red existente</div></div>
     <div class="card"><div class="v">${fmt((d.km_diseño||0)+(d.km_planificadas||0),1)} km</div><div class="l">cartera futura</div></div>
     <div class="card"><div class="v">${fmt(d.pct_pob_300,1)} %</div><div class="l">población a 300 m${barra(d.pct_pob_300||0,100)}</div></div>
     <div class="card"><div class="v">${fmt(d.pct_bici_300,1)} %</div><div class="l">ciclistas a 300 m${barra(d.pct_bici_300||0,100)}</div></div>
     <div class="card"><div class="v">${fmt(d.n_componentes,0)}</div><div class="l">fragmentos desconectados</div></div>
     <div class="card"><div class="v">${fmt(d.pct_km_componente_mayor,0)} %</div><div class="l">km en el fragmento mayor${barra(d.pct_km_componente_mayor||0,100)}</div></div>
   </div>
   <div class="stat">Personas que declaran la bicicleta como modo principal: <b>${fmt(d.bici,0)}</b></div>
   ${d.brecha_nse!==null&&d.brecha_nse!==undefined?
     `<div class="stat">Brecha de cobertura entre el quintil socioeconómico más alto y el más bajo de la comuna: <b>${fmt(d.brecha_nse,1)} puntos</b>${d.brecha_nse>0?' a favor del más alto':' a favor del más bajo'}.</div>`:''}
   <div class="hint">${indActual.d}</div>
   <div class="hint" style="cursor:pointer;color:var(--acc);font-weight:600" onclick="seleccionar(null)">← Volver al resumen nacional</div>`;
}

// selector de indicador
const si=document.getElementById('selInd');
INDICADORES.forEach((x,i)=>{const o=document.createElement('option');o.value=i;o.textContent=x.t;si.appendChild(o);});
si.onchange=()=>{indActual=INDICADORES[si.value];pintaComunas();panel();};

// buscador
const nombres={}; DATA.comunas.features.forEach(f=>nombres[f.properties.cut]=f.properties.nom);
const items=Object.entries(nombres).map(([cut,nom])=>({cut,nom,tipo:'comuna'}));
Object.entries(DATA.metros||{}).forEach(([m,cuts])=>items.push({cuts:cuts.map(c=>String(c).padStart(5,'0')),nom:m,tipo:'metro'}));
const cbox=document.getElementById('cbox'),clist=document.getElementById('clist');
const sinAcento=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
cbox.oninput=()=>{
  const q=sinAcento(cbox.value.trim()); if(q.length<2){clist.style.display='none';return;}
  const r=items.filter(i=>sinAcento(i.nom).includes(q)).slice(0,30);
  clist.innerHTML=r.map((i,k)=>`<div class="ci" data-k="${k}">${i.nom}<span class="rg">${i.tipo}</span></div>`).join('');
  clist.style.display=r.length?'block':'none';
  clist.querySelectorAll('.ci').forEach(el=>el.onclick=()=>{
    const i=r[+el.dataset.k]; clist.style.display='none'; cbox.value=i.nom;
    const cuts=i.tipo==='metro'?i.cuts:[i.cut];
    const fs=DATA.comunas.features.filter(f=>cuts.includes(f.properties.cut));
    if(!fs.length)return;
    const b=L.geoJSON({type:'FeatureCollection',features:fs}).getBounds();
    if(i.tipo==='metro'){comSel=null;map.fitBounds(b,{padding:[24,24]});panel();}
    else seleccionar(i.cut,i.nom,b);
  });
};
document.addEventListener('click',e=>{if(!e.target.closest('.searchw'))clist.style.display='none';});

// capas
const bind=(id,capa)=>{document.getElementById(id).onchange=e=>{
  e.target.checked?map.addLayer(capa):map.removeLayer(capa);};};
bind('lRed',capaRed);bind('lPlan',capaPlan);bind('lCont',capaCont);bind('lEq',capaEq);

dibujaRed();dibujaPuntos();pintaComunas();panel();
</script></body></html>
"""

if __name__ == "__main__":
    main()
