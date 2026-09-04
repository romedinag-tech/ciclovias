# -*- coding: utf-8 -*-
"""
Genera el visor: un unico index.html autocontenido, con el payload incrustado.

Arquitectura en tres secciones, siguiendo el patron del tablero de siniestros de
transito del repositorio (misma distribucion: header institucional con gradiente,
pestañas, barra de filtros globales, migas de navegacion y vistas):

  Infraestructura   la red y su vialidad: cuanto hay, de que tipo, desde cuando
                    y si esta conectada
  Demanda           quien pedalea: Censo 2024, las EOD donde el modo existe y
                    los contadores de flujo
  Espacial          lo anterior sobre el territorio: que zonas generan viajes,
                    donde ocurren los siniestros, donde se mide

Estandar visual: tokens del tema propio (claro institucional / oscuro con LED
naranja), serif de display para titulos, Inter para interfaz y mono tabular para
cifras. El naranja es chrome de interfaz, nunca color de dato, para no romper la
neutralidad de la escala. Incluye toggle de tema y paleta alternativa para
daltonismo.

Por que no usa `_dashboard_kit/lib_dashboard.py`: el motor del kit arma su capa
de datos desde puntos por rol del catastro SII y sus "unidades" son lentes con
umbrales de superficie. No tiene capa lineal ni componentes de red, que es el
centro de este visor. Se reutiliza el estandar grafico, no el motor.

Uso:
    python -X utf8 scripts/prepara_payload.py
    python -X utf8 scripts/genera_visor.py
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAYLOAD = RAIZ / "_work" / "payload.json"
SALIDA = RAIZ / "index.html"
VERSION = 2


def main():
    if not PAYLOAD.exists():
        raise SystemExit("falta _work/payload.json — corre antes prepara_payload.py")
    data = PAYLOAD.read_text(encoding="utf-8")
    html = PLANTILLA.replace("/*__DATA__*/", data).replace("__VER__", str(VERSION))
    SALIDA.write_text(html, encoding="utf-8")
    print(f"-> {SALIDA.name}  {SALIDA.stat().st_size/1e6:.2f} MB  (v{VERSION})")


PLANTILLA = r"""<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ciclovías de Chile — infraestructura, demanda y territorio</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#128690;</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
  --paper:#FBFBFD; --surface:#FFFFFF; --surface-alt:#F4F6F9;
  --line:#E3E8EF; --line-2:#D6DEE9;
  --ink:#0E2338; --ink-mid:#4A5A70; --ink-lo:#7C8AA0;
  --mut:var(--ink-mid); --mut-2:var(--ink-lo);
  --navy:#16365a; --accent:#1F6FEB; --focus:#1F6FEB;
  --grad:linear-gradient(135deg,#0E2338 0%,#16365a 60%,#21507F 100%);
  --or:#C55A11;
  --r:14px; --r-sm:10px;
  --sh-sm:0 1px 2px rgba(14,35,56,.04),0 1px 3px rgba(14,35,56,.04);
  --sh:0 1px 3px rgba(14,35,56,.05),0 8px 24px rgba(14,35,56,.05);
  --font-display:'Source Serif 4',Georgia,serif;
  --font-ui:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  --font-data:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;
  --seq-1:#EFF3FB; --seq-2:#C6D9F0; --seq-3:#8CB3DE; --seq-4:#4A80C0; --seq-5:#16365A;
  --div-pos:#2166AC; --div-pos-2:#67A9CF;
  --e0:#16365A; --e1:#2E7EBB; --e2:#7FB3D9; --e3:#B9CFE4;
  --c-sin:#B2182B; --c-cont:#3F8E86; --c-ok:#2E8B57;
}
:root[data-theme="dark"]{
  --paper:#0a0d13; --surface:#151c27; --surface-alt:#1a212c; --line:#232c3a; --line-2:#2b3547;
  --ink:#e9eef5; --ink-mid:#8a93a5; --ink-lo:#6b7382; --mut:#8a93a5; --mut-2:#6b7382;
  --navy:#ff6a1a; --accent:#ff6a1a; --focus:#ff9d2f; --or:#ff9d2f;
  --grad:linear-gradient(135deg,#12161f 0%,#0d1119 60%,#161d28 100%);
  --sh-sm:0 1px 2px rgba(0,0,0,.5);
  --sh:0 8px 22px rgba(0,0,0,.55),0 2px 6px rgba(0,0,0,.5);
  --card-grad:linear-gradient(180deg,#1a212c 0%,#11161f 100%);
  --card-3d:inset 0 1px 0 rgba(255,255,255,.06),inset 0 -18px 30px rgba(0,0,0,.28),0 18px 34px -12px rgba(0,0,0,.70);
  --led:0 0 6px rgba(255,150,40,.85),0 0 16px rgba(255,106,26,.55),0 0 30px rgba(255,106,26,.30);
  --seq-1:#16283d; --seq-2:#1d4468; --seq-3:#2f6ea8; --seq-4:#4f9ada; --seq-5:#8fc6f5;
  --div-pos:#7FB9EC; --div-pos-2:#4a86bd;
  --e0:#8fc6f5; --e1:#4f9ada; --e2:#2f6ea8; --e3:#40566f;
  --c-sin:#E4736B; --c-cont:#5CC6BB; --c-ok:#5FBF87;
}
:root[data-cb="1"]{
  --seq-1:#f7f7f7; --seq-2:#cccccc; --seq-3:#969696; --seq-4:#636363; --seq-5:#252525;
  --e0:#000000; --e1:#5b5b5b; --e2:#969696; --e3:#c9c9c9;
  --c-sin:#d95f02; --c-cont:#1b9e77; --c-ok:#7570b3;
}
:root[data-theme="dark"][data-cb="1"]{
  --seq-1:#1c1c1c; --seq-2:#4d4d4d; --seq-3:#828282; --seq-4:#bdbdbd; --seq-5:#f0f0f0;
  --e0:#ffffff; --e1:#c9c9c9; --e2:#969696; --e3:#5b5b5b;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--paper)}
body{font-family:var(--font-ui);color:var(--ink);font-size:14px;line-height:1.5;
  -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
.wrap{max-width:1520px;margin:0 auto;padding:0 18px 40px}
h1,h2,h3{font-family:var(--font-display);color:var(--ink);letter-spacing:-.01em;margin:0}
h2{font-size:1.06rem;font-weight:600;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
h3{font-size:.95rem;font-weight:600;margin:18px 0 2px}
a{color:var(--accent)}
.ic{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;
  stroke-linecap:round;stroke-linejoin:round;flex:none}
.apptop{display:grid;grid-template-columns:auto 1fr auto;grid-template-rows:auto auto;
  gap:2px 14px;align-items:center;background:var(--grad);color:#fff;
  padding:14px 20px;border-radius:0 0 var(--r) var(--r);margin-bottom:14px}
.apptop .emblem{width:30px;height:30px;grid-row:1/3;fill:none;stroke:#fff;stroke-width:1.8;
  stroke-linecap:round;stroke-linejoin:round;opacity:.95}
.apptop .brand{font-family:var(--font-display);font-weight:700;font-size:1.22rem}
.apptop .sub{font-size:.74rem;letter-spacing:.3px;opacity:.85}
.apptop .actions{grid-row:1/3;display:flex;align-items:center;gap:9px}
.live-badge{display:inline-flex;align-items:center;gap:6px;font-size:.68rem;font-weight:700;
  text-transform:uppercase;letter-spacing:.4px;color:#fff;opacity:.92}
.live-badge .led{width:8px;height:8px;border-radius:50%;background:#ff9d2f;box-shadow:var(--led,none)}
.hdr-btn{border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.13);color:#fff;
  width:33px;height:33px;border-radius:9px;cursor:pointer;font-size:1rem;line-height:1}
.hdr-btn:hover{background:rgba(255,255,255,.24)}
.hdr-btn[aria-pressed="true"]{background:#fff;color:#16365a}
.tabs{display:flex;gap:2px;border-bottom:1px solid var(--line);margin-bottom:12px;overflow-x:auto}
.tabs button{border:none;background:none;padding:13px 17px;cursor:pointer;font-size:.93rem;
  font-weight:700;color:var(--mut);border-bottom:3px solid transparent;margin-bottom:-1px;
  display:flex;align-items:center;gap:7px;white-space:nowrap;font-family:var(--font-ui)}
.tabs button.on,.tabs button:hover{color:var(--accent);border-bottom-color:var(--accent)}
.tabs button:focus-visible{outline:2px solid var(--focus);outline-offset:-2px}
.filters{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;background:var(--surface);
  border:1px solid var(--line);border-radius:var(--r);padding:12px 14px;box-shadow:var(--sh-sm)}
.fg{display:flex;flex-direction:column;gap:5px;min-width:150px}
.fg label{font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;
  color:var(--ink-lo);display:flex;align-items:center;gap:5px}
.fg select,.fg input{padding:7px 9px;border:1px solid var(--line-2);border-radius:var(--r-sm);
  font-size:.86rem;background:var(--surface);color:var(--ink);font-family:var(--font-ui);min-width:160px}
.fg select:focus,.fg input:focus{outline:2px solid var(--focus);outline-offset:1px}
.tbtn{padding:7px 13px;border:1px solid var(--line-2);border-radius:var(--r-sm);
  background:var(--surface);color:var(--mut);font-weight:600;cursor:pointer;font-size:.84rem}
.tbtn:hover{border-color:var(--accent);color:var(--accent)}
#breadcrumb{margin:10px 2px 0;font-size:.84rem;color:var(--mut);min-height:20px}
#breadcrumb b{color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:12px;margin:14px 0}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);
  padding:14px 16px;box-shadow:var(--sh-sm)}
:root[data-theme="dark"] .kpi{background-image:var(--card-grad);box-shadow:var(--card-3d)}
.kpi .label{font-size:.72rem;color:var(--mut);font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.kpi .v{font-family:var(--font-data);font-size:1.6rem;font-weight:700;color:var(--navy);line-height:1.15;margin:5px 0 2px}
.kpi .s{color:var(--mut);font-size:.78rem;line-height:1.35}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);
  padding:16px 18px;box-shadow:var(--sh);margin-bottom:14px}
:root[data-theme="dark"] .card{background-image:var(--card-grad);box-shadow:var(--card-3d)}
.desc{color:var(--mut);font-size:.87rem;margin:5px 0 12px;max-width:80ch}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:980px){.grid2{grid-template-columns:1fr}}
.chartbox{position:relative;height:290px}
.chartbox.sm{height:225px}
.chartbox.lg{height:380px}
.src{font-size:.73rem;color:var(--mut-2);margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
details.method{margin-top:10px;border:1px solid var(--line);border-radius:var(--r-sm);
  background:var(--surface-alt);padding:9px 12px}
details.method summary{cursor:pointer;font-weight:600;font-size:.83rem;color:var(--accent)}
details.method p{font-size:.845rem;color:var(--mut);margin:9px 0 0;max-width:82ch}
.callout{border-left:3px solid var(--or);background:var(--surface-alt);padding:10px 13px;
  border-radius:0 var(--r-sm) var(--r-sm) 0;font-size:.86rem;color:var(--mut);margin:10px 0;max-width:84ch}
.callout b{color:var(--ink)}
.maprow{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:10px}
.seglab{font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;color:var(--ink-lo)}
.seg{display:inline-flex;border:1px solid var(--line-2);border-radius:22px;overflow:hidden}
.seg button{border:none;background:var(--surface);color:var(--mut);padding:6px 13px;cursor:pointer;
  font-weight:600;font-size:.82rem;font-family:var(--font-ui)}
.seg button+button{border-left:1px solid var(--line-2)}
.seg button.on{background:var(--accent);color:#fff}
.seg button:focus-visible{outline:2px solid var(--focus);outline-offset:-2px}
#mapInd{padding:6px 9px;border:1px solid var(--line-2);border-radius:var(--r-sm);
  background:var(--surface);color:var(--ink);font-size:.84rem;font-family:var(--font-ui);max-width:340px}
#map{height:min(70vh,660px);border-radius:var(--r-sm);border:1px solid var(--line);background:var(--surface-alt)}
.legend{display:flex;flex-wrap:wrap;gap:16px;margin-top:11px;font-size:.78rem;color:var(--mut);align-items:center}
.legend .grp{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.legend .ttl{font-weight:700;color:var(--ink);font-size:.75rem}
.sw{width:15px;height:15px;border-radius:3px;display:inline-block;border:1px solid rgba(125,125,125,.25)}
.swl{width:19px;height:3px;border-radius:2px;display:inline-block}
.swd{width:11px;height:11px;border-radius:50%;display:inline-block}
.lyr{display:flex;gap:14px;flex-wrap:wrap;font-size:.82rem;color:var(--mut)}
.lyr label{display:flex;align-items:center;gap:5px;cursor:pointer}
table{width:100%;border-collapse:collapse;font-size:.85rem}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left}
th{font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-lo);
  font-weight:700;position:sticky;top:0;background:var(--surface);cursor:pointer;user-select:none}
th:hover{color:var(--accent)}
td.n,th.n{text-align:right;font-family:var(--font-data)}
.tw{max-height:340px;overflow:auto;border:1px solid var(--line);border-radius:var(--r-sm)}
tbody tr:hover{background:var(--surface-alt)}
.hide{display:none}
.foot{color:var(--mut-2);font-size:.76rem;margin-top:20px;line-height:1.55;max-width:96ch}
</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">
<symbol id="i-bike" viewBox="0 0 24 24"><circle cx="5.5" cy="17.5" r="3.5"/><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="15" cy="5" r="1"/><path d="M12 17.5V14l-3-3 4-3 2 3h3"/></symbol>
<symbol id="i-road" viewBox="0 0 24 24"><path d="M4 22 8 2h8l4 20"/><line x1="12" y1="4" x2="12" y2="7"/><line x1="12" y1="11" x2="12" y2="14"/><line x1="12" y1="18" x2="12" y2="21"/></symbol>
<symbol id="i-users" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/></symbol>
<symbol id="i-layers" viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></symbol>
<symbol id="i-map" viewBox="0 0 24 24"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></symbol>
<symbol id="i-pin" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></symbol>
<symbol id="i-building" viewBox="0 0 24 24"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/></symbol>
<symbol id="i-trend" viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></symbol>
<symbol id="i-alert" viewBox="0 0 24 24"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></symbol>
<symbol id="i-gauge" viewBox="0 0 24 24"><circle cx="12" cy="12" r="2"/><path d="M13.4 10.6 19 5"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/></symbol>
<symbol id="i-grid" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></symbol>
<symbol id="i-filter" viewBox="0 0 24 24"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></symbol>
</svg>

<div class="wrap">
<header class="apptop">
  <svg class="emblem"><use href="#i-bike"/></svg>
  <div class="brand">Ciclovías de Chile</div>
  <div class="actions">
    <span class="live-badge"><span class="led"></span>Datos abiertos</span>
    <button class="hdr-btn" id="cbBtn" title="Paleta para daltonismo" aria-label="Paleta para daltonismo" aria-pressed="false">◐</button>
    <button class="hdr-btn" id="themeBtn" title="Tema claro / oscuro" aria-label="Cambiar tema">☾</button>
  </div>
  <div class="sub">Catastro Nacional SECTRA/MTT &middot; Censo 2024 &middot; Encuestas Origen-Destino &middot; Contadores MINVU &middot; Siniestros CONASET</div>
</header>

<nav class="tabs" id="mainTabs" aria-label="Secciones">
  <button data-v="infra" class="on" aria-current="page"><svg class="ic"><use href="#i-road"/></svg>Análisis de infraestructura</button>
  <button data-v="demanda"><svg class="ic"><use href="#i-users"/></svg>Análisis de demanda</button>
  <button data-v="espacial"><svg class="ic"><use href="#i-layers"/></svg>Análisis espacial</button>
</nav>

<div class="filters">
  <div class="fg"><label><svg class="ic"><use href="#i-pin"/></svg>Región</label><select id="fRegion"></select></div>
  <div class="fg"><label><svg class="ic"><use href="#i-building"/></svg>Comuna o área metropolitana</label><select id="fComuna"></select></div>
  <div class="fg"><label><svg class="ic"><use href="#i-filter"/></svg>Buscar</label><input id="fBuscar" placeholder="Escribe un nombre…" autocomplete="off"></div>
  <div class="fg"><label>&nbsp;</label><button class="tbtn" id="reset">Limpiar filtros</button></div>
</div>
<div id="breadcrumb"></div>

<section id="viewInfra">
  <div class="kpis" id="kInfra"></div>
  <div class="grid2">
    <div class="card">
      <h2><svg class="ic"><use href="#i-trend"/></svg>Kilómetros construidos por año</h2>
      <p class="desc">Kilómetros de red <b>existente</b> según el año de ejecución que declara el catastro. Es la forma correcta de leer el ritmo de construcción: restar versiones consecutivas del catastro no lo mide, porque cada actualización incorpora obras antiguas que antes no estaban registradas.</p>
      <div class="chartbox"><canvas id="cAnio"></canvas></div>
      <div class="src">Fuente: Catastro Nacional de Ciclovías, SECTRA / Programa de Vialidad y Transporte Urbano, MTT (corte julio 2026).</div>
    </div>
    <div class="card">
      <h2><svg class="ic"><use href="#i-road"/></svg>Ciclo de vida de la red</h2>
      <p class="desc">El catastro cubre las cuatro etapas del ciclo de vida, no solo lo construido. Reportar el total como «la red de Chile» la infla a más del doble.</p>
      <div class="chartbox sm"><canvas id="cEtapa"></canvas></div>
      <h3>Tipo de infraestructura</h3>
      <div class="chartbox sm"><canvas id="cTipo"></canvas></div>
      <div class="src">Fuente: SECTRA/MTT. «smp» = servicio de movilidad particular; «s_i» = sin información.</div>
    </div>
  </div>
  <div class="grid2">
    <div class="card">
      <h2><svg class="ic"><use href="#i-grid"/></svg>Kilómetros no son red: la fragmentación</h2>
      <p class="desc">Cada burbuja es una comuna, y su tamaño la población. El eje horizontal es cuánta red tiene; el vertical, qué proporción de esos kilómetros pertenece a su fragmento conectado más grande. Abajo a la derecha están las comunas con mucha red repartida en tramos sueltos: kilometraje sin continuidad de viaje.</p>
      <div class="chartbox"><canvas id="cFrag"></canvas></div>
      <details class="method"><summary>Cómo se midió la conectividad</summary>
        <p>Se construye el grafo de la red existente uniendo dos tramos cuando sus geometrías quedan a menos de 20 m, y se cuentan las componentes conexas. Unir por geometría y no por extremos coincidentes es lo correcto: el 37,0 % de los extremos coincide con el extremo de otro tramo, pero otro 11,9 % cae sobre el <i>interior</i> de otro tramo —empalmes en T— y un grafo por extremos los pierde, reportando la red mucho más partida de lo que está. La tolerancia de 20 m se eligió porque es donde la curva se aplana: entre 20 y 50 m la componente mayor casi no se mueve. El supuesto es optimista, porque dos ciclovías que se cruzan quedan unidas aunque el cruce no permita virar; la fragmentación reportada es por tanto una cota inferior.</p>
      </details>
    </div>
    <div class="card">
      <h2><svg class="ic"><use href="#i-road"/></svg>Emplazamiento de la red existente</h2>
      <p class="desc">Dónde va físicamente la ciclovía. El emplazamiento es la variable de diseño que el análisis de contadores de MINVU (2018) asoció con las mayores diferencias de uso.</p>
      <div class="chartbox"><canvas id="cEmpl"></canvas></div>
      <h3>Evolución del catastro entre cortes</h3>
      <div class="chartbox sm"><canvas id="cEvol"></canvas></div>
      <div class="callout"><b>Cómo leer esta última serie.</b> El crecimiento entre cortes es en su mayor parte mejora de catastro, no obra nueva. Entre noviembre de 2024 y julio de 2025 la red existente sube 441,1 km, pero solo 18,6 km declaran ejecución de 2025 o posterior.</div>
    </div>
  </div>
  <div class="card">
    <h2><svg class="ic"><use href="#i-building"/></svg>Detalle comunal</h2>
    <p class="desc">Red, cobertura y fragmentación por comuna. Haz clic en el encabezado de una columna para ordenar.</p>
    <div class="tw"><table id="tInfra"><thead></thead><tbody></tbody></table></div>
    <div class="src">Cobertura = población cuya manzana censal tiene su centroide a menos de 300 m de un tramo existente, el mismo umbral que usa el índice de ciclo-inclusión de SECTRA. La brecha por nivel socioeconómico es la cobertura del quintil más alto de la comuna menos la del más bajo.</div>
  </div>
</section>

<section id="viewDemanda" class="hide">
  <div class="kpis" id="kDem"></div>
  <div class="grid2">
    <div class="card">
      <h2><svg class="ic"><use href="#i-users"/></svg>Participación de la bicicleta según la EOD</h2>
      <p class="desc">Porcentaje de viajes en bicicleta sobre el total de viajes de cada Encuesta Origen-Destino. La barra es la reconstrucción propia; la cruz, la cifra oficial del informe del estudio, cuando ese índice resulta utilizable.</p>
      <div class="chartbox lg"><canvas id="cEod"></canvas></div>
      <details class="method"><summary>De dónde sale la bicicleta en la EOD, y cómo se validó</summary>
        <p>La base EOD homologada del repositorio declara el modo bicicleta solo en Talca 2022; en el resto queda absorbida en «No Motorizado» junto con la caminata. Eso no significa que las demás encuestas no la midieran, sino que la homologación colapsó un código propio de cada estudio. Un nivel más abajo el dato sí está: dentro del grupo no motorizado el campo original se parte en exactamente dos códigos, uno masivo y uno menor, y Gran Concepción lo confirma casi literalmente porque sus etiquetas son «1.Caminata» y «2.No Caminata». Se asigna el código dominante a la caminata y el resto a la bicicleta.</p>
        <p>La reconstrucción no se publica sin contrastar. El índice de estudios del repositorio trae, tomadas de los informes oficiales, la caminata y el resto del grupo no motorizado por separado. En las ocho ciudades donde ese índice es internamente consistente —donde su propio total reproduce el que entrega el microdato— la reconstrucción replica la cifra oficial con una correlación de 0,9999 y un error absoluto medio de 0,033 puntos porcentuales. En las siete restantes el índice se contradice a sí mismo y queda marcado como no utilizable: Coquimbo-La Serena trae la caminata en cero y mete los 329.575 viajes no motorizados enteros en la otra columna, y Puerto Montt declara 45,5 % de caminata cuando el microdato entrega 18,7 % de no motorizados en total. En esos casos se conserva la reconstrucción propia y se descarta la referencia.</p>
      </details>
    </div>
    <div class="card">
      <h2><svg class="ic"><use href="#i-gauge"/></svg>La EOD contra el Censo 2024</h2>
      <p class="desc">Cada punto es una ciudad: en el eje horizontal la participación reconstruida de la EOD, en el vertical la del Censo 2024 sobre las mismas comunas. Miden universos distintos —la EOD todos los viajes, el Censo el modo principal al trabajo o al estudio—, de modo que los niveles no coinciden; lo que valida la reconstrucción es que ordenen igual.</p>
      <div class="chartbox"><canvas id="cEodCenso"></canvas></div>
      <div class="src" id="srcCorr"></div>
      <h3>Propósito del viaje en bicicleta</h3>
      <div class="chartbox sm"><canvas id="cProp"></canvas></div>
    </div>
  </div>
  <div class="grid2">
    <div class="card">
      <h2><svg class="ic"><use href="#i-clock"/></svg>Distribución horaria del viaje en bicicleta</h2>
      <p class="desc">Viajes en bicicleta por hora de inicio, sumando todas las EOD reconstruidas. Una forma de doble punta indica viaje obligado —trabajo y estudio— más que recreativo.</p>
      <div class="chartbox"><canvas id="cHora"></canvas></div>
      <div class="src">Fuente: EOD homologadas del Ministerio de Transportes, 15 ciudades entre 2010 y 2023.</div>
    </div>
    <div class="card">
      <h2><svg class="ic"><use href="#i-gauge"/></svg>Contadores automáticos de flujo</h2>
      <p class="desc">Cada punto es un contador: en el eje horizontal su promedio de día hábil, en el vertical el de fin de semana. La diagonal marca la igualdad; por debajo de ella el uso cae el fin de semana, señal de viaje obligado, y por encima el uso es predominantemente recreativo.</p>
      <div class="chartbox"><canvas id="cCont"></canvas></div>
      <div class="src" id="srcCont"></div>
    </div>
  </div>
  <div class="card">
    <h2><svg class="ic"><use href="#i-building"/></svg>Uso de la bicicleta por comuna (Censo 2024)</h2>
    <p class="desc">Personas que declaran la bicicleta como modo principal de transporte al trabajo o al estudio, y qué proporción representan de quienes declaran algún modo.</p>
    <div class="tw"><table id="tDem"><thead></thead><tbody></tbody></table></div>
    <div class="src">Fuente: Censo de Población y Vivienda 2024, INE. El universo son las personas que declaran un modo de transporte, no la población total. Siniestros: CONASET 2020-2024.</div>
  </div>
</section>

<section id="viewEspacial" class="hide">
  <div class="card">
    <h2><svg class="ic"><use href="#i-map"/></svg>Mapa <span class="desc" id="mapHint" style="margin:0;font-weight:400"></span></h2>
    <p class="desc" id="mapDesc"></p>
    <div class="maprow">
      <span class="seglab">Unidad</span>
      <div class="seg" id="mapUnit">
        <button data-u="comuna" class="on">Comuna</button>
        <button data-u="zona">Zona censal</button>
      </div>
      <span class="seglab">Indicador</span>
      <select id="mapInd"></select>
      <span class="seglab">Fondo</span>
      <div class="seg" id="mapBase">
        <button data-b="claro" class="on">Claro</button>
        <button data-b="calles">Calles</button>
        <button data-b="satelite">Satélite</button>
      </div>
    </div>
    <div class="maprow lyr">
      <label><input type="checkbox" id="lRed" checked> Red existente</label>
      <label><input type="checkbox" id="lPlan"> Cartera futura</label>
      <label><input type="checkbox" id="lCont"> Contadores de flujo</label>
      <label><input type="checkbox" id="lSin"> Siniestros con ciclista</label>
      <label><input type="checkbox" id="lHeat"> Concentración de siniestros</label>
      <label><input type="checkbox" id="lEq"> Colegios y educación superior</label>
    </div>
    <div id="map"></div>
    <div class="legend" id="legend"></div>
    <div class="src">La coropleta se dibuja por quintiles del indicador dentro del territorio filtrado. Sobre el fondo satelital el relleno baja su opacidad para que la imagen se lea por debajo. Las distancias son euclidianas desde el centroide de la unidad, no medidas por la red vial.</div>
  </div>
  <div class="grid2">
    <div class="card">
      <h2><svg class="ic"><use href="#i-alert"/></svg>Siniestros con ciclista</h2>
      <p class="desc">Siniestros de tránsito con participación de bicicleta registrados por Carabineros y publicados por CONASET.</p>
      <div class="chartbox sm"><canvas id="cSinAnio"></canvas></div>
      <h3>Hora de ocurrencia</h3>
      <div class="chartbox sm"><canvas id="cSinHora"></canvas></div>
      <div class="src">Fuente: CONASET, datos abiertos 2020-2024. Solo los siniestros con coordenada válida dentro de Chile.</div>
    </div>
    <div class="card">
      <h2><svg class="ic"><use href="#i-grid"/></svg>Zonas que generan viajes en bicicleta</h2>
      <p class="desc">Las veinte zonas censales con mayor participación de la bicicleta entre las que superan los 500 habitantes. La última columna indica a qué distancia media, ponderada por población, está la zona del tramo de ciclovía más cercano.</p>
      <div class="tw"><table id="tZonas"><thead></thead><tbody></tbody></table></div>
      <div class="callout">Varias de las zonas con más uso de bicicleta del país están a kilómetros de una ciclovía. Es demanda que ya existe sin infraestructura que la acompañe, y es el argumento más directo para priorizar cartera.</div>
    </div>
  </div>
</section>

<div class="foot">
  Elaboración propia sobre fuentes públicas: Catastro Nacional de Ciclovías e índice de ciclo-inclusión (SECTRA / Programa de Vialidad y Transporte Urbano, MTT), contadores automáticos de flujo y análisis de contadores 2018 (MINVU, División de Desarrollo Urbano), Censo de Población y Vivienda 2024 (INE), Encuestas Origen-Destino del MTT y siniestros de tránsito (CONASET). Todo el contenido es agregado o de infraestructura pública; no contiene microdato individual.
  <br>Las asociaciones que muestra este visor son observadas y no permiten inferir causalidad: la cercanía entre ciclovía y uso de la bicicleta admite las dos direcciones.
</div>
</div>

<script>
const D = /*__DATA__*/;
const ETAPAS=['existentes','ejecución','diseño','planificadas'];
const cssv=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const fmt=(v,d=0)=>(v===null||v===undefined||!isFinite(v))?'s/d':
  Number(v).toLocaleString('es-CL',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=(v,d=1)=>(v===null||v===undefined||!isFinite(v))?'s/d':fmt(v,d)+' %';
const sinAc=s=>String(s).normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();

let F={region:'',cut:'',metro:null,metroNom:''};
let vista='infra';

function enFiltro(cut){
  if(F.cut) return cut===F.cut;
  if(F.metro) return F.metro.includes(cut);
  if(F.region) return (D.comunas[cut]||{}).reg===F.region;
  return true;
}
function comunasFiltradas(){
  const o={};
  for(const [c,d] of Object.entries(D.comunas)) if(enFiltro(c)) o[c]=d;
  return o;
}
const sum=(o,k)=>Object.values(o).reduce((a,d)=>a+(d[k]||0),0);

function kpis(){
  const o=comunasFiltradas(), n=Object.keys(o).length;
  const kme=sum(o,'kme'), kmc=sum(o,'kmd')+sum(o,'kmp'), pob=sum(o,'pob');
  const cub=Object.values(o).reduce((a,d)=>a+((d.cob||0)/100*(d.pob||0)),0);
  const bici=sum(o,'bici');
  const bcub=Object.values(o).reduce((a,d)=>a+((d.cobb||0)/100*(d.bici||0)),0);
  // fragmentos: se cuentan las componentes DISTINTAS que tocan el territorio,
  // no la suma de los conteos comunales, que multiplicaria las que lo cruzan
  const cuts=new Set(Object.keys(o));
  let ncomp=0;
  for(const [id,cs] of Object.entries(D.compComunas||{})) if(cs.some(c=>cuts.has(c))) ncomp++;
  const conRed=Object.values(o).filter(d=>(d.kme||0)>0).length;
  const sini=sum(o,'sini'), sinf=sum(o,'sinf');
  const modos=sum(o,'viajes_modo')||Object.values(o).reduce((a,d)=>a+(d.bici||0),0);

  document.getElementById('kInfra').innerHTML=[
    ['Red existente',fmt(kme,1)+' km',`en ${fmt(conRed)} de ${fmt(n)} comunas`],
    ['Cartera futura',fmt(kmc,1)+' km','en diseño y planificados, aún no construidos'],
    ['Fragmentos',fmt(ncomp),'tramos continuos sin conexión entre sí (tolerancia 20 m)'],
    ['Largo por fragmento',ncomp?fmt(kme/ncomp,2)+' km':'s/d','promedio de tramo continuo'],
    ['Población cubierta',pct(pob?100*cub/pob:NaN),'vive a menos de 300 m de la red'],
  ].map(k=>`<div class="kpi"><div class="label">${k[0]}</div><div class="v">${k[1]}</div><div class="s">${k[2]}</div></div>`).join('');

  document.getElementById('kDem').innerHTML=[
    ['Usan la bicicleta',fmt(bici),'personas, modo principal al trabajo o estudio'],
    ['Participación modal',pct(modos?100*bici/modos:NaN,2),'de quienes declaran algún modo (Censo 2024)'],
    ['Ciclistas cubiertos',pct(bici?100*bcub/bici:NaN),'viven a menos de 300 m de una ciclovía'],
    ['Contadores de flujo',fmt(D.contadores.filter(c=>enFiltro(c.c)).length),'puntos de medición permanente (MINVU)'],
    ['Siniestros con ciclista',fmt(sini),`${fmt(sinf)} con resultado de muerte, 2020-2024`],
  ].map(k=>`<div class="kpi"><div class="label">${k[0]}</div><div class="v">${k[1]}</div><div class="s">${k[2]}</div></div>`).join('');
}

let CH={};
function destruir(id){ if(CH[id]){CH[id].destroy(); delete CH[id];} }
function ctx(){
  const mut=cssv('--mut'), line=cssv('--line');
  Chart.defaults.font.family="Inter, system-ui, sans-serif";
  Chart.defaults.color=mut;
  return {mut,line};
}
function opt(extra={}){
  const {mut,line}=ctx();
  return Object.assign({responsive:true,maintainAspectRatio:false,animation:{duration:280},
    plugins:{legend:{labels:{boxWidth:12,font:{size:11},color:mut}}},
    scales:{x:{grid:{display:false},ticks:{color:mut,font:{size:10}}},
            y:{grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true}}},extra);
}
function corr(a,b){
  const n=a.length; if(n<3) return NaN;
  const ma=a.reduce((x,y)=>x+y,0)/n, mb=b.reduce((x,y)=>x+y,0)/n;
  let sa=0,sb=0,sab=0;
  for(let i=0;i<n;i++){const da=a[i]-ma,db=b[i]-mb;sa+=da*da;sb+=db*db;sab+=da*db;}
  return sab/Math.sqrt(sa*sb);
}

function graficos(){
  const {mut,line}=ctx();
  const ec=[cssv('--e0'),cssv('--e1'),cssv('--e2'),cssv('--e3')];

  destruir('cAnio');
  const ay=D.por_anio.filter(x=>x.anio>=2005);
  CH.cAnio=new Chart(document.getElementById('cAnio'),{type:'bar',
    data:{labels:ay.map(x=>x.anio),datasets:[{label:'km ejecutados',data:ay.map(x=>x.km),
      backgroundColor:cssv('--e1'),borderRadius:3}]},
    options:opt({plugins:{legend:{display:false},tooltip:{callbacks:{
      label:c=>fmt(c.raw,1)+' km · '+fmt(ay[c.dataIndex].tramos)+' tramos'}}}})});

  destruir('cEtapa');
  CH.cEtapa=new Chart(document.getElementById('cEtapa'),{type:'doughnut',
    data:{labels:D.por_etapa.map(x=>x.etapa),datasets:[{data:D.por_etapa.map(x=>x.km),
      backgroundColor:ec,borderWidth:0}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'58%',
      plugins:{legend:{position:'right',labels:{boxWidth:12,font:{size:11},color:mut}},
      tooltip:{callbacks:{label:c=>c.label+': '+fmt(c.raw,1)+' km'}}}}});

  destruir('cTipo');
  const tp=D.por_tipo.slice(0,8);
  CH.cTipo=new Chart(document.getElementById('cTipo'),{type:'bar',
    data:{labels:tp.map(x=>x.tipo),datasets:[{label:'km existentes',data:tp.map(x=>x.km_existentes),
      backgroundColor:cssv('--e0'),borderRadius:3}]},
    options:opt({indexAxis:'y',plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>fmt(c.raw,1)+' km existentes'}}},
      scales:{x:{grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true},
              y:{grid:{display:false},ticks:{color:mut,font:{size:10}}}}})});

  destruir('cEmpl');
  const em=D.por_emplazamiento.slice(0,8);
  CH.cEmpl=new Chart(document.getElementById('cEmpl'),{type:'bar',
    data:{labels:em.map(x=>x.emplaza),datasets:[{label:'km',data:em.map(x=>x.km),
      backgroundColor:cssv('--e1'),borderRadius:3}]},
    options:opt({indexAxis:'y',plugins:{legend:{display:false},
      tooltip:{callbacks:{label:c=>fmt(c.raw,1)+' km'}}},
      scales:{x:{grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true},
              y:{grid:{display:false},ticks:{color:mut,font:{size:9}}}}})});

  destruir('cEvol');
  CH.cEvol=new Chart(document.getElementById('cEvol'),{type:'bar',
    data:{labels:D.evolucion.map(x=>x.corte),datasets:[
      {label:'km existentes',data:D.evolucion.map(x=>x.km),backgroundColor:cssv('--e1'),borderRadius:3,yAxisID:'y'},
      {label:'comunas con red',data:D.evolucion.map(x=>x.comunas),type:'line',
       borderColor:cssv('--seq-5'),backgroundColor:cssv('--seq-5'),tension:.3,yAxisID:'y1'}]},
    options:opt({scales:{x:{grid:{display:false},ticks:{color:mut,font:{size:10}}},
      y:{grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true},
      y1:{position:'right',grid:{display:false},ticks:{color:mut,font:{size:10}},beginAtZero:true}}})});

  destruir('cFrag');
  const cf=Object.entries(comunasFiltradas()).filter(([,d])=>(d.kme||0)>3&&d.pmayor!==null&&d.pmayor!==undefined)
    .map(([,d])=>({x:d.kme,y:d.pmayor,n:d.nom,r:Math.max(3,Math.min(13,Math.sqrt((d.pob||0)/8000)))}));
  CH.cFrag=new Chart(document.getElementById('cFrag'),{type:'bubble',
    data:{datasets:[{data:cf,backgroundColor:cssv('--seq-4')+'bb',borderColor:cssv('--seq-5')}]},
    options:opt({plugins:{legend:{display:false},tooltip:{callbacks:{
      label:c=>`${c.raw.n}: ${fmt(c.raw.x,1)} km · ${fmt(c.raw.y,0)} % en el fragmento mayor`}}},
      scales:{x:{title:{display:true,text:'km de red existente',color:mut,font:{size:10}},
                 grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true},
              y:{title:{display:true,text:'% de km en la componente mayor',color:mut,font:{size:10}},
                 grid:{color:line},ticks:{color:mut,font:{size:10}},min:0,max:100}}})});

  destruir('cEod');
  const e=D.eod;
  CH.cEod=new Chart(document.getElementById('cEod'),{type:'bar',
    data:{labels:e.map(x=>x.ciudad+' '+x.anio),datasets:[
      {label:'reconstrucción propia',data:e.map(x=>x.bici_pct),backgroundColor:cssv('--seq-4'),borderRadius:3},
      {label:'cifra oficial del informe',data:e.map(x=>x.ok?x.ofi:null),type:'scatter',
       backgroundColor:cssv('--seq-5'),borderColor:cssv('--seq-5'),pointStyle:'crossRot',radius:7,borderWidth:2}]},
    options:opt({indexAxis:'y',
      plugins:{legend:{labels:{boxWidth:12,font:{size:11},color:mut}},
        tooltip:{callbacks:{afterLabel:c=>e[c.dataIndex]&&!e[c.dataIndex].ok?'índice oficial no utilizable':''}}},
      scales:{x:{title:{display:true,text:'% de viajes en bicicleta',color:mut,font:{size:10}},
                 grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true},
              y:{grid:{display:false},ticks:{color:mut,font:{size:9.5}}}}})});

  destruir('cEodCenso');
  const ec2=e.filter(x=>x.censo!==null&&x.censo!==undefined);
  CH.cEodCenso=new Chart(document.getElementById('cEodCenso'),{type:'scatter',
    data:{datasets:[{data:ec2.map(x=>({x:x.bici_pct,y:x.censo,n:x.ciudad})),
      backgroundColor:cssv('--seq-4'),borderColor:cssv('--seq-5'),pointRadius:6}]},
    options:opt({plugins:{legend:{display:false},tooltip:{callbacks:{
      label:c=>`${c.raw.n}: EOD ${fmt(c.raw.x,2)} % · Censo ${fmt(c.raw.y,2)} %`}}},
      scales:{x:{title:{display:true,text:'EOD reconstruida (%)',color:mut,font:{size:10}},
                 grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true},
              y:{title:{display:true,text:'Censo 2024 (%)',color:mut,font:{size:10}},
                 grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true}}})});
  const r=corr(ec2.map(x=>x.bici_pct),ec2.map(x=>x.censo));
  document.getElementById('srcCorr').textContent=
    `Correlación de Pearson entre ambas fuentes sobre ${ec2.length} ciudades: r = ${fmt(r,3)}. `+
    `Fuentes: EOD del Ministerio de Transportes y Censo 2024 (INE).`;

  destruir('cProp');
  const pr=(D.eod_perfil.proposito||[]).slice(0,7);
  CH.cProp=new Chart(document.getElementById('cProp'),{type:'doughnut',
    data:{labels:pr.map(x=>x.v),datasets:[{data:pr.map(x=>x.n),
      backgroundColor:[cssv('--seq-5'),cssv('--seq-4'),cssv('--seq-3'),cssv('--seq-2'),
        cssv('--div-pos'),cssv('--div-pos-2'),cssv('--seq-1')],borderWidth:0}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'56%',
      plugins:{legend:{position:'right',labels:{boxWidth:11,font:{size:10},color:mut}},
      tooltip:{callbacks:{label:c=>c.label+': '+fmt(c.raw,0)+' viajes'}}}}});

  destruir('cHora');
  const hh=Array.from({length:24},(_,i)=>{
    const f=(D.eod_perfil.hora||[]).find(x=>Number(x.v)===i); return f?f.n:0;});
  CH.cHora=new Chart(document.getElementById('cHora'),{type:'line',
    data:{labels:Array.from({length:24},(_,i)=>i+'h'),datasets:[{label:'viajes',
      data:hh,borderColor:cssv('--seq-5'),backgroundColor:cssv('--seq-3')+'55',
      fill:true,tension:.35,pointRadius:2}]},
    options:opt({plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fmt(c.raw,0)+' viajes'}}}})});

  destruir('cCont');
  const co=D.contadores.filter(c=>enFiltro(c.c)&&c.hab!==null&&c.fds!==null);
  const mx=Math.max(10,...co.map(c=>Math.max(c.hab,c.fds)));
  CH.cCont=new Chart(document.getElementById('cCont'),{type:'scatter',
    data:{datasets:[
      {label:'contador',data:co.map(c=>({x:c.hab,y:c.fds,n:c.n})),
       backgroundColor:cssv('--c-cont'),pointRadius:5},
      {label:'igualdad hábil = fin de semana',type:'line',data:[{x:0,y:0},{x:mx,y:mx}],
       borderColor:cssv('--mut'),borderDash:[5,4],pointRadius:0,borderWidth:1.2}]},
    options:opt({plugins:{legend:{labels:{boxWidth:12,font:{size:10},color:mut}},
      tooltip:{callbacks:{label:c=>c.raw.n?`${c.raw.n}: hábil ${fmt(c.raw.x,0)} · fin de semana ${fmt(c.raw.y,0)}`:''}}},
      scales:{x:{title:{display:true,text:'promedio día hábil (pasadas)',color:mut,font:{size:10}},
                 grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true},
              y:{title:{display:true,text:'promedio fin de semana',color:mut,font:{size:10}},
                 grid:{color:line},ticks:{color:mut,font:{size:10}},beginAtZero:true}}})});
  const bajo=co.filter(c=>c.fds<c.hab).length;
  document.getElementById('srcCont').textContent=co.length
    ? `${co.length} contadores con ambos promedios. En ${bajo} de ellos (${fmt(100*bajo/co.length,0)} %) el uso baja el fin de semana. Fuente: contadores automáticos de flujo, MINVU–DDU.`
    : 'No hay contadores en el territorio seleccionado.';

  destruir('cSinAnio');
  CH.cSinAnio=new Chart(document.getElementById('cSinAnio'),{type:'bar',
    data:{labels:D.sin_anio.map(x=>x.anio),datasets:[{label:'siniestros',data:D.sin_anio.map(x=>x.n),
      backgroundColor:cssv('--c-sin'),borderRadius:3}]},
    options:opt({plugins:{legend:{display:false}}})});

  destruir('cSinHora');
  const sh=Array.from({length:24},(_,i)=>{const f=D.sin_hora.find(x=>x.hora===i);return f?f.n:0;});
  CH.cSinHora=new Chart(document.getElementById('cSinHora'),{type:'bar',
    data:{labels:Array.from({length:24},(_,i)=>i+'h'),datasets:[{label:'siniestros',data:sh,
      backgroundColor:cssv('--c-sin'),borderRadius:2}]},
    options:opt({plugins:{legend:{display:false}}})});
}

function tabla(id,cols,filas){
  const t=document.getElementById(id);
  t.querySelector('thead').innerHTML='<tr>'+cols.map(c=>
    `<th class="${c.n?'n':''}" data-k="${c.k}" title="Ordenar">${c.t}</th>`).join('')+'</tr>';
  const pinta=()=>t.querySelector('tbody').innerHTML=filas.length?filas.map(f=>'<tr>'+cols.map(c=>
    `<td class="${c.n?'n':''}">${c.f?c.f(f[c.k],f):(f[c.k]??'s/d')}</td>`).join('')+'</tr>').join('')
    :`<tr><td colspan="${cols.length}" style="color:var(--mut-2)">Sin datos para el territorio seleccionado.</td></tr>`;
  pinta();
  let asc=false;
  t.querySelectorAll('th').forEach(th=>th.onclick=()=>{
    const k=th.dataset.k; asc=!asc;
    filas.sort((a,b)=>{const x=a[k],y=b[k];
      if(typeof x==='string'||typeof y==='string') return asc?String(x).localeCompare(String(y)):String(y).localeCompare(String(x));
      return asc?((x??-1e12)-(y??-1e12)):((y??-1e12)-(x??-1e12));});
    pinta();});
}
function tablas(){
  const o=comunasFiltradas();
  const fi=Object.entries(o).map(([c,d])=>({cut:c,...d})).filter(d=>(d.kme||0)>0)
    .sort((a,b)=>(b.kme||0)-(a.kme||0));
  tabla('tInfra',[
    {k:'nom',t:'Comuna'},{k:'reg',t:'Región'},
    {k:'kme',t:'km existentes',n:1,f:v=>fmt(v,1)},
    {k:'kmd',t:'km en diseño',n:1,f:v=>fmt(v,1)},
    {k:'ncomp',t:'Fragmentos',n:1,f:v=>fmt(v)},
    {k:'pmayor',t:'% en el mayor',n:1,f:v=>pct(v,0)},
    {k:'cob',t:'Cobertura 300 m',n:1,f:v=>pct(v)},
    {k:'brecha',t:'Brecha NSE (pts)',n:1,f:v=>(v===null||v===undefined)?'s/d':fmt(v,1)},
  ],fi);

  const fd=Object.entries(o).map(([c,d])=>({cut:c,...d})).filter(d=>(d.bici||0)>0)
    .sort((a,b)=>(b.bici||0)-(a.bici||0)).slice(0,250);
  tabla('tDem',[
    {k:'nom',t:'Comuna'},{k:'reg',t:'Región'},
    {k:'bici',t:'Personas en bicicleta',n:1,f:v=>fmt(v)},
    {k:'bici_pct',t:'Participación modal',n:1,f:v=>pct(v,2)},
    {k:'cobb',t:'Ciclistas a 300 m',n:1,f:v=>pct(v)},
    {k:'sini',t:'Siniestros',n:1,f:v=>fmt(v||0)},
    {k:'kme',t:'km de red',n:1,f:v=>fmt(v,1)},
  ],fd);

  const zz=D.zonas.filter(z=>enFiltro(z.c)&&z.pob>=500&&z.bp!==null)
    .sort((a,b)=>b.bp-a.bp).slice(0,20);
  tabla('tZonas',[
    {k:'nom',t:'Comuna'},{k:'pob',t:'Habitantes',n:1,f:v=>fmt(v)},
    {k:'bici',t:'En bicicleta',n:1,f:v=>fmt(v)},
    {k:'bp',t:'Participación',n:1,f:v=>pct(v)},
    {k:'d',t:'A la red',n:1,f:v=>fmt(v)+' m'},
  ],zz);
}

const IND=[
  {k:'cob',u:'comuna',t:'Cobertura: población a 300 m de la red',s:'%',inv:false,
   d:'Porcentaje de habitantes cuya manzana censal está a menos de 300 m de un tramo existente. Es el umbral que usa el índice de ciclo-inclusión de SECTRA.'},
  {k:'bici_pct',u:'comuna',t:'Uso de la bicicleta (Censo 2024)',s:'%',inv:false,
   d:'Participación de la bicicleta como modo principal de transporte al trabajo o al estudio, sobre quienes declaran algún modo.'},
  {k:'kme',u:'comuna',t:'Kilómetros de red existente',s:' km',inv:false,
   d:'Suma del kilometraje declarado de los tramos en etapa existentes.'},
  {k:'pmayor',u:'comuna',t:'Integración: % de km en el fragmento mayor',s:'%',inv:false,
   d:'Qué proporción de los kilómetros de la comuna pertenece al fragmento conectado más grande. Valores bajos indican tramos sueltos que no permiten un viaje continuo.'},
  {k:'brecha',u:'comuna',t:'Brecha de cobertura por nivel socioeconómico',s:' pts',inv:true,
   d:'Cobertura del quintil socioeconómico más alto de la comuna menos la del más bajo. Un valor positivo significa que la infraestructura favorece a las manzanas de mayor nivel.'},
  {k:'sini',u:'comuna',t:'Siniestros con ciclista (2020-2024)',s:'',inv:true,
   d:'Siniestros de tránsito con participación de bicicleta registrados por CONASET. Es un conteo, no una tasa: las comunas grandes tienen más por población, no necesariamente por mayor riesgo.'},
  {k:'bp',u:'zona',t:'Uso de la bicicleta por zona censal',s:'%',inv:false,
   d:'Participación de la bicicleta en la zona censal. Es la unidad más fina que permite ver diferencias dentro de una misma ciudad.'},
  {k:'cob',u:'zona',t:'Cobertura de la zona a 300 m',s:'%',inv:false,
   d:'Población de la zona censal que vive a menos de 300 m de la red existente.'},
  {k:'d',u:'zona',t:'Distancia media a la ciclovía más cercana',s:' m',inv:true,
   d:'Distancia desde la zona al tramo existente más cercano, ponderada por la población de cada manzana.'},
  {k:'nse',u:'zona',t:'Nivel socioeconómico de la zona',s:'',inv:false,
   d:'Índice de 0 a 100 por zona censal. Es un atributo del territorio, no de las personas que viven en él.'},
];
let map,capaCom,capaZona,cortes=[0,0,0,0],indAct=IND[0],unidad='comuna',baseAct,bases;
// El fondo neutro sigue al tema: un lienzo claro bajo la interfaz oscura
// desentona y ademas hace ilegible la coropleta, que en oscuro usa azules
// claros. Esri publica las dos variantes del mismo lienzo sin clave.
const urlLienzo=()=>'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_'
  +(document.documentElement.getAttribute('data-theme')==='dark'?'Dark':'Light')
  +'_Gray_Base/MapServer/tile/{z}/{y}/{x}';
function sincronizaLienzo(){
  if(!map||!bases) return;
  const activo=document.querySelector('#mapBase button.on');
  bases.claro.setUrl(urlLienzo());
  if(activo&&activo.dataset.b==='claro') bases.claro.redraw();
}
let cRed,cPlan,cCont,cSin,cHeat,cEq,pendienteEncuadre=false;

function initMapa(){
  map=L.map('map',{preferCanvas:true}).setView([-35.5,-71.3],5);
  ['pPoli','pRed','pPtos'].forEach((n,i)=>map.createPane(n).style.zIndex=[350,420,470][i]);
  bases={
    claro:L.tileLayer(urlLienzo(),
      {attribution:'Esri, HERE, Garmin, &copy; OpenStreetMap',maxZoom:16}),
    calles:L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      {attribution:'&copy; OpenStreetMap',maxZoom:19}),
    satelite:L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      {attribution:'Esri',maxZoom:19})};
  baseAct=bases.claro.addTo(map);
  document.getElementById('mapBase').onclick=ev=>{
    const b=ev.target.dataset.b; if(!b) return;
    document.querySelectorAll('#mapBase button').forEach(x=>x.classList.toggle('on',x.dataset.b===b));
    map.removeLayer(baseAct); baseAct=bases[b].addTo(map); pintaPoli();
  };
  cRed=L.layerGroup().addTo(map); cPlan=L.layerGroup();
  cCont=L.layerGroup(); cSin=L.layerGroup(); cEq=L.layerGroup();
  dibujaRed(); dibujaPuntos();
  const bind=(id,capa)=>document.getElementById(id).onchange=ev=>
    ev.target.checked?map.addLayer(capa):map.removeLayer(capa);
  bind('lRed',cRed); bind('lPlan',cPlan); bind('lCont',cCont);
  bind('lSin',cSin); bind('lEq',cEq);
  document.getElementById('lHeat').onchange=ev=>{
    if(cHeat){map.removeLayer(cHeat);cHeat=null;}
    if(ev.target.checked){
      const pts=D.siniestros.filter(s=>enFiltro(s.c)).map(s=>[s.ll[0],s.ll[1],1]);
      cHeat=L.heatLayer(pts,{radius:18,blur:22,maxZoom:14}); map.addLayer(cHeat);
    }};
  document.getElementById('mapUnit').onclick=ev=>{
    const u=ev.target.dataset.u; if(!u) return;
    document.querySelectorAll('#mapUnit button').forEach(x=>x.classList.toggle('on',x.dataset.u===u));
    unidad=u; llenaInd(); pintaPoli();
  };
  document.getElementById('mapInd').onchange=ev=>{indAct=IND[Number(ev.target.value)];pintaPoli();};
  llenaInd();
}
function llenaInd(){
  const sel=document.getElementById('mapInd'); sel.innerHTML='';
  IND.forEach((x,i)=>{ if(x.u!==unidad) return;
    const o=document.createElement('option'); o.value=i; o.textContent=x.t; sel.appendChild(o);});
  indAct=IND[Number(sel.value)];
}
function quintiles(v){
  v=v.slice().sort((a,b)=>a-b);
  return [.2,.4,.6,.8].map(p=>v[Math.max(0,Math.floor(p*(v.length-1)))]);
}
function colorDe(v){
  const P=[cssv('--seq-1'),cssv('--seq-2'),cssv('--seq-3'),cssv('--seq-4'),cssv('--seq-5')];
  if(v===null||v===undefined||!isFinite(v)) return cssv('--surface-alt');
  let i=0; while(i<cortes.length&&v>cortes[i])i++;
  return indAct.inv?P[4-i]:P[i];
}
function pintaPoli(){
  if(capaCom){map.removeLayer(capaCom);capaCom=null;}
  if(capaZona){map.removeLayer(capaZona);capaZona=null;}
  const satel=document.querySelector('#mapBase button.on').dataset.b==='satelite';
  const op=satel?0.58:0.78;
  document.getElementById('mapDesc').textContent=indAct.d;

  if(unidad==='comuna'){
    const vals=Object.entries(D.comunas).filter(([c])=>enFiltro(c))
      .map(([,d])=>d[indAct.k]).filter(v=>v!==null&&v!==undefined&&isFinite(v));
    cortes=quintiles(vals.length?vals:[0]);
    capaCom=L.geoJSON(D.comunasGeo,{pane:'pPoli',
      filter:f=>enFiltro(f.properties.cut),
      style:f=>{const d=D.comunas[f.properties.cut]||{};
        return{fillColor:colorDe(d[indAct.k]),fillOpacity:op,color:'#fff',weight:.6};},
      onEachFeature:(f,l)=>{const c=f.properties.cut,d=D.comunas[c]||{};
        l.bindTooltip(`<b>${f.properties.nom}</b><br>${indAct.t}: ${fmt(d[indAct.k],1)}${indAct.s}`
          +`<br>${fmt(d.pob)} hab · ${fmt(d.kme,1)} km existentes`,{sticky:true});
        l.on('click',()=>{F.cut=c;F.metro=null;F.metroNom='';sincroniza();});
        l.on('mouseover',()=>l.setStyle({weight:2,color:cssv('--accent')}));
        l.on('mouseout',()=>l.setStyle({weight:.6,color:'#fff'}));
      }}).addTo(map);
    document.getElementById('mapHint').textContent=`· ${Object.keys(comunasFiltradas()).length} comunas`;
  } else {
    const zs=D.zonas.filter(z=>enFiltro(z.c));
    const vals=zs.map(z=>z[indAct.k]).filter(v=>v!==null&&v!==undefined&&isFinite(v));
    cortes=quintiles(vals.length?vals:[0]);
    capaZona=L.layerGroup();
    zs.forEach(z=>z.g.forEach(anillo=>{
      const p=L.polygon(anillo,{pane:'pPoli',fillColor:colorDe(z[indAct.k]),fillOpacity:op,
        color:'#fff',weight:.4});
      p.bindTooltip(`<b>${z.nom}</b> · zona ${z.z}<br>${indAct.t}: ${fmt(z[indAct.k],1)}${indAct.s}`
        +`<br>${fmt(z.pob)} hab · ${fmt(z.bici)} en bicicleta<br>a ${fmt(z.d)} m de la red`,{sticky:true});
      capaZona.addLayer(p);}));
    capaZona.addTo(map);
    document.getElementById('mapHint').textContent=`· ${zs.length} zonas censales`;
  }
  leyenda();
}
function leyenda(){
  const P=[cssv('--seq-1'),cssv('--seq-2'),cssv('--seq-3'),cssv('--seq-4'),cssv('--seq-5')];
  const et=[`≤ ${fmt(cortes[0],1)}`,`≤ ${fmt(cortes[1],1)}`,`≤ ${fmt(cortes[2],1)}`,
            `≤ ${fmt(cortes[3],1)}`,`> ${fmt(cortes[3],1)}`];
  let h=`<div class="grp"><span class="ttl">${indAct.t}${indAct.s.trim()?' ('+indAct.s.trim()+')':''}</span>`;
  et.forEach((e,i)=>h+=`<span class="sw" style="background:${indAct.inv?P[4-i]:P[i]}"></span>${e}`);
  h+=`<span class="sw" style="background:${cssv('--surface-alt')}"></span>sin dato</div>`;
  h+=`<div class="grp"><span class="ttl">Red</span>`;
  ETAPAS.forEach((e,i)=>h+=`<span class="swl" style="background:${cssv('--e'+i)}"></span>${e}`);
  h+=`</div><div class="grp"><span class="ttl">Puntos</span>`
   +`<span class="swd" style="background:${cssv('--c-cont')}"></span>contador (tamaño = media diaria)`
   +`<span class="swd" style="background:${cssv('--c-sin')}"></span>siniestro con ciclista`
   +`<span class="swd" style="background:${cssv('--c-ok')}"></span>colegio o sede a menos de 300 m`
   +`<span class="swd" style="background:${cssv('--c-sin')};opacity:.5"></span>a más de 300 m</div>`;
  document.getElementById('legend').innerHTML=h;
}
function dibujaRed(){
  cRed.clearLayers(); cPlan.clearLayers();
  D.red.forEach(t=>{ if(!enFiltro(t.c)) return;
    const dst=t.e===0?cRed:cPlan;
    const st={pane:'pRed',color:cssv('--e'+t.e),weight:t.e===0?2.6:1.7,
      opacity:t.e===0?.95:.7,dashArray:t.e>=2?'4,4':null};
    t.g.forEach(p=>{const ln=L.polyline(p,st);
      ln.bindTooltip(`<b>${t.n||'(sin nombre de eje)'}</b><br>${ETAPAS[t.e]} · ${t.t}`
        +`<br>${fmt(t.k,2)} km${t.a?' · '+t.a:''}`,{sticky:true});
      dst.addLayer(ln);});});
}
function dibujaPuntos(){
  cCont.clearLayers(); cSin.clearLayers(); cEq.clearLayers();
  D.contadores.forEach(c=>{ if(!enFiltro(c.c))return;
    const r=c.m?Math.max(4,Math.min(15,Math.sqrt(c.m)*.62)):4;
    L.circleMarker(c.ll,{pane:'pPtos',radius:r,color:'#0f766e',weight:1.3,
      fillColor:cssv('--c-cont'),fillOpacity:.8})
      .bindTooltip(`<b>${c.n}</b><br>Media diaria ${fmt(c.m,1)} pasadas`
        +`<br>Hábil ${fmt(c.hab,0)} · fin de semana ${fmt(c.fds,0)}`
        +`<br>Máximo ${fmt(c.x,0)}${c.d0?'<br>Mide desde '+c.d0+' hasta '+c.d1:''}`,{sticky:true})
      .addTo(cCont);});
  D.siniestros.forEach(s=>{ if(!enFiltro(s.c))return;
    L.circleMarker(s.ll,{pane:'pPtos',radius:s.f>0?5:3,color:cssv('--c-sin'),weight:1,
      fillColor:cssv('--c-sin'),fillOpacity:s.f>0?.95:.5})
      .bindTooltip(`Siniestro con ciclista${s.a?' · '+s.a:''}${s.h!==null&&s.h!==undefined?' · '+s.h+'h':''}`
        +`<br>${s.t||''}${s.f?'<br><b>'+s.f+' fallecido(s)</b>':''}${s.gr?'<br>'+s.gr+' grave(s)':''}`,{sticky:true})
      .addTo(cSin);});
  D.equip.forEach(e=>{ if(!enFiltro(e.c))return;
    const ok=e.d<=300;
    L.circleMarker(e.ll,{pane:'pPtos',radius:e.k?5:3,color:ok?'#166534':'#7f1d1d',weight:1,
      fillColor:ok?cssv('--c-ok'):cssv('--c-sin'),fillOpacity:ok?.85:.5})
      .bindTooltip(`<b>${e.n}</b><br>${e.k?'Educación superior':'Establecimiento escolar'}`
        +`<br>A ${fmt(e.d)} m de la red${e.m?'<br>Matrícula '+fmt(e.m):''}`,{sticky:true})
      .addTo(cEq);});
}

const REG=[...new Set(Object.values(D.comunas).map(d=>d.reg).filter(Boolean))].sort();
function initFiltros(){
  const fr=document.getElementById('fRegion');
  fr.innerHTML='<option value="">Todo Chile</option>'+REG.map(r=>`<option>${r}</option>`).join('');
  fr.onchange=()=>{F.region=fr.value;F.cut='';F.metro=null;F.metroNom='';llenaComunas();sincroniza();};
  llenaComunas();
  document.getElementById('fComuna').onchange=ev=>{
    const v=ev.target.value;
    if(v.startsWith('M:')){const m=v.slice(2);
      F.metro=(D.metros[m]||[]).map(c=>String(c).padStart(5,'0'));F.metroNom=m;F.cut='';}
    else {F.cut=v;F.metro=null;F.metroNom='';}
    sincroniza();};
  document.getElementById('reset').onclick=()=>{
    F={region:'',cut:'',metro:null,metroNom:''};
    fr.value='';document.getElementById('fBuscar').value='';llenaComunas();sincroniza();};
  const bs=document.getElementById('fBuscar');
  bs.oninput=()=>{
    const q=sinAc(bs.value.trim()); if(q.length<3) return;
    const met=Object.keys(D.metros||{}).find(m=>sinAc(m).startsWith(q));
    if(met){F.metro=D.metros[met].map(c=>String(c).padStart(5,'0'));F.metroNom=met;F.cut='';F.region='';
      fr.value='';llenaComunas();sincroniza();return;}
    const hit=Object.entries(D.comunas).find(([,d])=>sinAc(d.nom||'').startsWith(q));
    if(hit){F.cut=hit[0];F.metro=null;F.metroNom='';F.region='';fr.value='';llenaComunas();sincroniza();}
  };
}
function llenaComunas(){
  const s=document.getElementById('fComuna');
  const met=Object.keys(D.metros||{}).sort();
  const com=Object.entries(D.comunas)
    .filter(([,d])=>!F.region||d.reg===F.region)
    .sort((a,b)=>String(a[1].nom).localeCompare(String(b[1].nom)));
  s.innerHTML='<option value="">Todas las comunas</option>'
    +(F.region?'':'<optgroup label="Áreas metropolitanas">'+met.map(m=>`<option value="M:${m}">${m}</option>`).join('')+'</optgroup>')
    +'<optgroup label="Comunas">'+com.map(([c,d])=>`<option value="${c}">${d.nom}</option>`).join('')+'</optgroup>';
  s.value=F.metro?('M:'+F.metroNom):(F.cut||'');
}
function migas(){
  const b=document.getElementById('breadcrumb');
  const p=['<b>Chile</b>'];
  if(F.region) p.push(F.region);
  if(F.metro) p.push(`<b>${F.metroNom}</b> (${F.metro.length} comunas)`);
  if(F.cut) p.push('<b>'+((D.comunas[F.cut]||{}).nom||F.cut)+'</b>');
  b.innerHTML=p.join(' › ')+(p.length>1?' · <a href="#" id="volver">volver a todo Chile</a>':'');
  const v=document.getElementById('volver');
  if(v) v.onclick=ev=>{ev.preventDefault();document.getElementById('reset').click();};
}
function zoomFiltro(){
  // Todos los encuadres programaticos van con animate:false. Con las 4.577
  // zonas censales dibujadas sobre el canvas, la transicion de zoom de Leaflet
  // no alcanza a completarse y el mapa revierte a la vista anterior sin lanzar
  // ningun error: fitBounds y setZoom se aceptan y no pasa nada. Sin animacion
  // el cambio de vista es inmediato y deterministico.
  // Si el contenedor todavia no tiene tamaño real —seccion recien mostrada,
  // ventana minimizada, pestaña en segundo plano— getBoundsZoom devuelve un
  // zoom absurdo calculado sobre dos pixeles. Se pospone el encuadre y se
  // reintenta cuando el mapa ya mide algo.
  const sz=map.getSize();
  if(sz.x<80||sz.y<80){ pendienteEncuadre=true; return; }
  pendienteEncuadre=false;
  const cuts=F.cut?[F.cut]:(F.metro||null);
  if(!cuts){map.setView([-35.5,-71.3],5,{animate:false});return;}
  const fs=D.comunasGeo.features.filter(f=>cuts.includes(f.properties.cut));
  if(!fs.length) return;
  const b=L.geoJSON({type:'FeatureCollection',features:fs}).getBounds();
  if(!b.isValid()) return;
  map.setView(b.getCenter(),Math.min(map.getBoundsZoom(b,false,[20,20]),14),{animate:false});
}
function sincroniza(){
  llenaComunas(); migas(); kpis(); graficos(); tablas();
  if(map){dibujaRed();dibujaPuntos();pintaPoli();zoomFiltro();
    if(document.getElementById('lHeat').checked){
      document.getElementById('lHeat').dispatchEvent(new Event('change'));}}
}

document.getElementById('mainTabs').onclick=ev=>{
  const b=ev.target.closest('button'); if(!b) return;
  vista=b.dataset.v;
  document.querySelectorAll('#mainTabs button').forEach(x=>{
    const on=x===b; x.classList.toggle('on',on);
    if(on) x.setAttribute('aria-current','page'); else x.removeAttribute('aria-current');});
  document.getElementById('viewInfra').classList.toggle('hide',vista!=='infra');
  document.getElementById('viewDemanda').classList.toggle('hide',vista!=='demanda');
  document.getElementById('viewEspacial').classList.toggle('hide',vista!=='espacial');
  if(vista==='espacial'){
    // La seccion nace oculta, asi que el contenedor mide 0 hasta mostrarse:
    // hay que dejar pasar un turno antes de inicializar el mapa y revalidar su
    // tamaño. Se usa setTimeout y NO requestAnimationFrame: el navegador
    // suspende los frames de animacion cuando la pestaña esta en segundo
    // plano, de modo que con rAF el mapa se quedaba sin inicializar —sin
    // lanzar error alguno— si el usuario abria la pagina en otra pestaña.
    setTimeout(()=>{
      if(!map){ initMapa(); map.invalidateSize(); pintaPoli(); zoomFiltro(); }
      else { map.invalidateSize(); pintaPoli(); if(pendienteEncuadre) zoomFiltro(); }
    },0);
  }
};

function rerender(){ graficos(); sincronizaLienzo(); if(map){dibujaRed();dibujaPuntos();pintaPoli();} }
// Si la ventana cambia de ancho, Leaflet necesita que se le avise: no observa
// el contenedor por su cuenta y queda dibujando sobre un tamaño viejo.
// Se observa el CONTENEDOR del mapa, no la ventana. El evento `resize` de
// window llega antes de que el layout termine de asentarse, de modo que
// Leaflet todavia reporta el tamaño viejo y el encuadre diferido no se
// resuelve. ResizeObserver dispara justo cuando la caja del elemento cambio.
if(window.ResizeObserver){
  new ResizeObserver(()=>{
    if(!map) return;
    map.invalidateSize();
    if(pendienteEncuadre) zoomFiltro();
  }).observe(document.getElementById('map'));
}
function setTheme(dark){
  document.documentElement.setAttribute('data-theme',dark?'dark':'light');
  try{localStorage.setItem('theme',dark?'dark':'light');}catch(e){}
  document.getElementById('themeBtn').textContent=dark?'☀':'☾';
  rerender();
}
try{ if(localStorage.getItem('theme')==='dark') document.documentElement.setAttribute('data-theme','dark'); }catch(e){}
document.getElementById('themeBtn').textContent=
  document.documentElement.getAttribute('data-theme')==='dark'?'☀':'☾';
document.getElementById('themeBtn').onclick=()=>
  setTheme(document.documentElement.getAttribute('data-theme')!=='dark');
document.getElementById('cbBtn').onclick=ev=>{
  const on=document.documentElement.getAttribute('data-cb')==='1';
  if(on) document.documentElement.removeAttribute('data-cb');
  else document.documentElement.setAttribute('data-cb','1');
  ev.currentTarget.setAttribute('aria-pressed',String(!on));
  rerender();
};

initFiltros(); migas(); kpis(); graficos(); tablas();
</script></body></html>
"""

if __name__ == "__main__":
    main()
