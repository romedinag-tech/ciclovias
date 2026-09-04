# Ciclovías — movilidad activa (bicicleta) en Chile

## Propósito

Base de datos propia sobre infraestructura ciclista y uso de la bicicleta en
Chile, construida desde las fuentes oficiales de SECTRA/MTT y MINVU y cruzada con
Censo 2024, EOD y siniestralidad. Tiene **dos dimensiones**, con público y
producto distintos:

- **banco** — los datos y los análisis. Sirve para responder preguntas a medida
  que todavía no existen: se consulta el Parquet y se calcula lo que haga falta.
- **visor** — el sitio publicado. Sirve para leer la información en formato
  gráfico desde la web, siempre disponible, sin abrir un entorno de análisis.

El visor no tiene fuentes propias: consume lo que produce el banco.

## Estado

Última actividad: 2026-09-04 (`c9b5ff9`).

### banco

Operativo y completo en su primera vuelta. 17 capas descargadas (63.925
registros, 0 fallos), normalizadas a un panel de cuatro cortes, más cinco
análisis: cobertura poblacional, accesibilidad a equipamiento educacional,
conectividad de red, demanda y agregación a zona censal.

Sin resolver, y anotado como tal: el pico de **714,9 km declarados con año de
ejecución 2017**, muy por encima de cualquier otro año, no está confirmado con
SECTRA. Puede ser el cierre de una cartera grande o el año por defecto asignado a
tramos de fecha desconocida.

### visor

Publicado en <https://romedinag-tech.github.io/ciclovias/>, tres secciones
—infraestructura, demanda, espacial— con tema claro/oscuro y paleta para
daltonismo. Un solo `index.html` de 6,9 MB con el payload incrustado.

## Entradas y salidas

### banco

Pipeline, en este orden:

```bash
python -X utf8 scripts/descarga_arcgis.py      # ArcGIS REST -> data/raw + data/parquet
python -X utf8 scripts/normaliza.py            # -> catastro_panel, catastro_comuna
python -X utf8 scripts/analisis_cobertura.py   # distancia manzana/establecimiento a la red
python -X utf8 scripts/analisis_conectividad.py# componentes conexas + sensibilidad
python -X utf8 scripts/analisis_demanda.py     # Censo + EOD + contadores + siniestros
python -X utf8 scripts/analisis_zonas.py       # agrega a zona censal
python -X utf8 scripts/genera_catalogo.py      # MANIFIESTO.json -> FUENTES.md
python -X utf8 scripts/genera_analisis.py      # data/analisis -> ANALISIS.md
```

`scripts/fuentes.py` es el registro declarativo de qué se baja y de dónde; es el
único archivo que se edita para agregar una capa.

**Regla de oro: ninguna cifra se escribe a mano.** `FUENTES.md` y `ANALISIS.md`
se **generan** leyendo el dato en ese momento; editarlos a mano los desincroniza
en silencio.

Insumos externos, todos en **solo lectura**: `GIS Gran Concepción` (manzanas y
zonas Censo 2024, NSE por zona, geometría comunal), `EODs` (EOD homologadas e
`indice_eod.csv`), `dashboard accidentes` (siniestros con ciclista), `SERVEL/anclas`
(directorio MINEDUC).

Respaldo metodológico: `docs/benchmark_minvu_2018.md` y el PDF en `docs/fuentes/`.

### visor

Dos pasos, deliberadamente separados: el payload tarda minutos y la maqueta se
itera decenas de veces.

```bash
python -X utf8 scripts/prepara_payload.py      # -> _work/payload.json (6,8 MB)
python -X utf8 scripts/genera_visor.py         # -> index.html
```

Al cerrar un bloque: subir `version.json`, commit y push. GitHub Pages sirve
desde `main`.

## Datos canónicos

### banco

`data/parquet/` es la fuente de trabajo y **va versionada**; `data/raw/` (GeoJSON
crudo) queda fuera de git y se regenera con el descargador. `data/MANIFIESTO.json`
es la traza de la descarga: conteos, campos y problemas detectados.

**Tabla canónica: `data/parquet/catastro_panel.parquet`.** Los cuatro cortes con
campos homogeneizados. Filtrar `etapa == 'existentes'` para hablar de red
construida: de 7.064,1 km catastrados sólo **2.827,7 km** existen.

**`data/analisis/` es un contrato, no archivos de trabajo.** La skill
`diag-ciclovias` lo consume. Son trece salidas: `manzana_cobertura`,
`cobertura_comuna`, `equipamiento_cobertura`, `conectividad_comuna`,
`conectividad_sensibilidad`, `componentes`, `tramo_componente`, `zona_demanda`,
`demanda_comuna`, `demanda_eod_ciudad`, `demanda_eod_perfil`, `demanda_eod_zona`
y `siniestros_bici`. Renombrar o borrar una columna rompe la skill sin previo
aviso; agregar columnas es seguro.

Trampas de las fuentes, ya verificadas:

- **`CUT_COM` sin relleno de ceros** en las regiones 1 a 9 (2.496 de 4.850
  registros). `zfill(5)` antes de cualquier cruce.
- **`CUT_REG` no es confiable**: 29 registros del panel declaran una región que
  no corresponde a su comuna. La región se **deriva** del `CUT_COM` y la
  discrepancia queda marcada en `cut_reg_declarado_discrepa`.
- **`minvu_contadores.COMUNA` trae el código CUT, no el nombre.**
- El servicio `CICLOV_validVisor_WFL1` publica **dos** capas de red; la vigente
  es la 0. **No sumarlas.**
- Los nombres de campo cambian entre cortes (`EMPLAZA_TEX`/`EMPLAZA_TE`,
  `NOM_PROYECTO`/`NOMBRE_PRO`, `FECHA_EJECUCION`/`YEAR_EJECU`). Mapear explícito.
- `objectIdField` varía por capa (`OBJECTID`, `FID`, `OBJECTID_12`); se lee del
  metadato.

Lo que **no** se guarda acá: la geometría comunal (las cinco capas ICC repiten
los mismos polígonos, ~120 MB duplicados; se bajan con `solo_atributos=True`) y
las manzanas censales nacionales, que ya viven en `GIS Gran Concepción`. La capa
`minvu_manzanas_poblacion_beneficiada` sí se conserva con geometría porque es la
*selección* de MINVU con su cifra oficial y **no trae `MANZENT`**: sólo se une
por cruce espacial.

Convenciones del repo: `cut_com` 5 dígitos, CRS 4326 para publicar y 32719 para
medir, `python -X utf8`. Todo el contenido es agregado o infraestructura pública;
no hay microdato individual y no debe introducirse.

### visor

`_work/payload.json` es intermedio y **no se versiona**: se reconstruye. Lo que
se versiona es `index.html`, que lo lleva incrustado.

No usa `_dashboard_kit/lib_dashboard.py`: ese motor arma su capa de datos desde
puntos por rol del catastro SII y no tiene concepto de capa lineal ni de
componentes de red. Se reutiliza su **estándar gráfico** —leído en solo lectura—,
no su motor.

## Aprendizajes

Todos de la misma familia: **fallas que no lanzan error**.

- `[banco]` 2026-09-04 — **ArcGIS responde `404`, no `414`, cuando la URL es
  demasiado larga.** Con bloques de 400 OBJECTID la query string excede el
  límite y el error se lee como «la capa no existe». Las consultas por bloque van
  por **POST**. Costó un diagnóstico falso: las capas chicas pasaban en un bloque
  y sólo fallaba el catastro, que es el dato central.
- `[banco]` 2026-09-04 — **La serie de cortes no mide construcción.** El salto de
  441,1 km entre nov-2024 y jul-2025 es mejora de catastro: sólo 18,6 km declaran
  ejecución 2025 o posterior. La construcción anual se lee de `year_ejecucion`
  dentro de un corte, nunca restando versiones.
- `[banco]` 2026-09-04 — **El grafo de conectividad debe unir geometrías, no
  extremos.** El 37,0 % de los extremos coincide con otro extremo, pero un
  11,9 % cae sobre el *interior* de otro tramo (empalmes en T). Ignorarlos daba
  una componente mayor de 56,4 km en vez de 311,8 km. Tolerancia 20 m, donde la
  curva se aplana; el supuesto es optimista, así que la fragmentación reportada
  es **cota inferior**.
- `[banco]` 2026-09-04 — **La bicicleta sí está en las EOD**, aunque la base
  homologada sólo la declare en Talca. Dentro del grupo no motorizado el código
  original se parte en dos: el dominante es caminata, el resto bicicleta (Gran
  Concepción lo confirma con sus etiquetas «1.Caminata» y «2.No Caminata»).
  Validado contra los informes oficiales: r = 0,9999 y error medio de 0,033 pp en
  las 8 ciudades donde el índice oficial es consistente. En las otras 7 el índice
  se contradice a sí mismo —Coquimbo-La Serena declara caminata cero; Puerto
  Montt, 45,5 % de caminata con 18,7 % de no motorizados totales— y se descarta
  como referencia. Contra el Censo 2024, r = 0,945.
- `[banco]` 2026-09-04 — **Un merge puede vaciar un indicador sin avisar.**
  `bici` existía en dos tablas y quedó partido en `bici_x`/`bici_y`; el KPI
  nacional mostró cero sin error. Antes de confiar en un agregado, verificar que
  reproduce la cifra del script que lo generó.
- `[banco]` 2026-09-04 — **Sumar conteos por comuna sobrecuenta lo que cruza
  límites.** La componente mayor toca 19 comunas y se contaba 19 veces (799 en
  vez de 732). Para contar en un recorte hay que contar entidades distintas, y
  para eso se guarda `tramo_componente.parquet`.
- `[visor]` 2026-09-04 — **`requestAnimationFrame` se suspende con la pestaña en
  segundo plano.** El mapa quedaba sin inicializar y no había error. Usar
  `setTimeout` para inicialización diferida.
- `[visor]` 2026-09-04 — **`fitBounds` y `setZoom` animados se pierden bajo carga
  de canvas.** Con 4.577 zonas dibujadas se aceptaban y el mapa revertía en
  silencio. Todo encuadre programático va con `animate:false`, y el encuadre se
  pospone si el contenedor aún no tiene tamaño (lo resuelve un `ResizeObserver`
  sobre el contenedor: el `resize` de window llega antes de que el layout
  asiente).
- `[visor]` 2026-09-04 — **Las teselas de `basemaps.cartocdn.com` vuelven con
  HTTP 200 y la marca «API KEY REQUIRED» encima.** Ningún chequeo estructural lo
  detecta. Se usan los lienzos claro/oscuro de Esri, sin clave. Alcanza a
  `_dashboard_kit/plantilla.html` y a los dashboards copiados de ella; **pendiente
  decidir si se corrige el estándar**, porque afecta a todos.
- `[visor]` 2026-09-04 — **Un mapa se verifica midiendo el render.** El criterio
  usado acá es `getBoundingClientRect` del contenedor más el conteo de píxeles
  con alfa > 0 en el canvas, sirviendo por HTTP. Contar nodos del DOM no distingue
  un mapa correcto de uno vacío.

- `[banco]` 2026-09-04 — **`hora_inicio` de la EOD llega en tres formatos y
  ninguno esta declarado**: fecha centinela de Access (`1899-12-30 13:20:00`,
  donde solo importa la hora), fraccion de dia de Excel (`0,5416` = 13:00) y la
  hora pelada (`17`). Leerla como numero devuelve nanosegundos en el primer caso
  y cero en el segundo, y la curva horaria sale vacia sin que nada falle: asi
  estuvo el grafico de Demanda hasta detectarlo. Normalizar con
  `hora_del_viaje()` en `analisis_demanda.py`.
- `[banco]` 2026-09-04 — **`smp` es «senda multiproposito»**, la infraestructura
  del MOP en la berma de una ruta rural. El servicio no lo declara: se dedujo
  del propio catastro, donde los nombres de proyecto de esos tramos dicen
  «construccion de sendas multiproposito en red vial», 372 de 421 son cartera
  MOP, 343 son rurales y 324 van por berma. Antes estaba glosado a ojo como
  «servicio de movilidad particular», que era invencion.
- `[banco]` 2026-09-04 — `viajes_analiticos.parquet` reproduce **exactamente** la
  reconstruccion de bicicleta hecha sobre los archivos por ciudad (r = 1,00000,
  diferencia media 0,0000 pp en 15 ciudades). Por eso los cruces por edad, sexo
  y quintil se calculan ahi, que es el unico archivo con los atributos de la
  persona pegados al viaje. Si esa igualdad se rompe, el dataset analitico
  cambio de criterio y hay que revisarlo antes de seguir publicando los cruces.
- `[visor]` 2026-09-04 — **El mismo nombre de ciudad llega con y sin tilde segun
  la fuente** —«Gran Concepcion» desde el nombre de carpeta, «Gran Concepción»
  desde el dataset analitico— y compararlos literal hacia caer siempre al
  agregado nacional sin error visible. Todo emparejamiento de ciudad va por
  clave sin acentos. Lo mismo con la comuna de un contador: se resuelve por la
  lista de comunas de cada EOD, no por nombre, porque un contador de Chiguayante
  pertenece a la EOD del Gran Concepcion.
- `[visor]` 2026-09-04 — La coropleta usa **rojo-amarillo-verde de siete clases**
  (rojo = casi nada, verde = mucho), por pedido explicito: la rampa azul
  secuencial no dejaba ver de un vistazo donde se usa mas y donde menos. Como
  esa combinacion es la peor para la deuteranopia, el boton de daltonismo
  cambia a viridis, que ordena por luminosidad. Los graficos no espaciales
  conservan la rampa azul neutra.

- `[banco]` 2026-09-04 — **La distancia del viaje no viene en la EOD**: se
  calcula entre centroides de zona de origen y destino, y el viaje intrazonal
  se estima con el radio equivalente de la zona (0,7 R). El metodo NO es propio,
  es el de `EODs/geo_distancias.py`; se replica aca porque ese script escribe
  dentro de `EODs` —solo lectura— y porque el parquet se regenera aguas arriba
  perdiendo la columna `distancia_km`, de modo que el codigo del tablero de
  movilidad la pide y no esta. El tratamiento del intrazonal importa
  especialmente para la bicicleta, que es el modo de los viajes cortos:
  dejarlo en cero hundiria la moda en el primer tramo. Resultado: el 97,1 % de
  los viajes en bicicleta ocurre bajo 8 km (promedio 2,24 km) contra 83,2 % del
  conjunto de modos (4,37 km).
- `[visor]` 2026-09-04 — **Una linea de un solo color desaparece sobre una
  coropleta saturada.** La red quedaba ilegible justo cuando se miraba contra
  la capa de cobertura, que es cuando mas se necesita. Se dibuja con reborde:
  una linea oscura ancha debajo y el color encima, tecnica cartografica
  estandar que funciona sobre cualquier fondo.
- `[visor]` 2026-09-04 — Para leer la cobertura a 300 m **no hace falta cambiar
  de zonificacion**: se dibuja la franja real de 300 m en torno a la red como
  capa. La zona censal promedia manzanas y esconde justamente lo que el umbral
  quiere mostrar; la geometria lo muestra tal cual.

- `[banco]` 2026-09-04 — **La EOD si se puede llevar a la zonificacion censal**,
  y ese es el techo metodologico correcto. En la base homologada el hogar NO
  trae coordenada —la geografia mas fina es la zona EOD— pero existen los
  poligonos de zona de 20 ciudades en `EODs/EOD-Chile/data/geojson`. El cruce
  reparte los viajes en proporcion a la POBLACION de cada trozo y no a su area:
  repartir por area supone gente distribuida pareja y en una zona que mezcla
  barrio denso con paño agricola manda viajes al potrero. Conserva el 97,8 % de
  los viajes; el resto son zonas EOD sin contraparte censal. Aunque el hogar
  trajera coordenada, desagregar bajo la zona daria precision falsa: los
  factores de expansion estan calibrados a nivel de zona.
- `[banco]` 2026-09-04 — Varias zonificaciones EOD traen **poligonos invalidos**
  y cualquier operacion de conjunto revienta con `TopologyException`. Reparar
  con `make_valid()` antes de intersectar; no altera la extension.

- `[visor]` 2026-09-04 — **La figura del mapa se COMPONE, no se captura.** Se
  dibujan a mano las teselas visibles, encima las capas vectoriales y debajo la
  leyenda y la linea de fuentes. No se usa una libreria de captura de pantalla
  porque Leaflet reparte el mapa entre imagenes sueltas y varios canvas, y
  porque lo que hace falta para un informe no es una foto del navegador sino una
  figura con su leyenda. Dos condiciones para que funcione: las teselas se
  piden con `crossOrigin:'anonymous'` —sin eso el canvas queda contaminado y
  `toDataURL` lanza una excepcion de seguridad— y el area del mapa se **recorta**
  antes de dibujar, porque Leaflet mantiene teselas mas alla del borde visible y
  sin recorte se derraman sobre la cabecera y la leyenda.
- `[visor]` 2026-09-04 — **Un canvas sin ancho exporta `data:,`**, es decir un
  archivo roto que el navegador descarga sin avisar. Pasa cuando el modal se
  abre antes de que el layout asiente. Se comprueba el ancho antes de exportar.

<!-- columna-vertebral: ultima_actualizacion=2026-09-04 commit=pendiente -->
