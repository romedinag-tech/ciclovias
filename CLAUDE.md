# Ciclovías — movilidad activa (bicicleta) en Chile

## Propósito

Banco de datos propio sobre infraestructura ciclista y uso de la bicicleta en
Chile, construido desde las fuentes oficiales de SECTRA/MTT y MINVU y cruzado con
Censo 2024, EOD y siniestralidad. Tiene **dos dimensiones**: **banco** —los datos
y los análisis, para responder preguntas a medida que todavía no existen— y
**visor** —el sitio publicado, para leer la información en formato gráfico sin
abrir un entorno de análisis—. El visor no tiene fuentes propias: consume lo que
produce el banco.

## Estado

activo

Última actividad: 2026-09-19 (`4811871`).

> **Al abrir:** `python -X utf8 "C:/Users/Rodrigo/Análisis RMG/_orquestador/orquestador.py" --abiertos ciclovias`
> — qué encargos tengo abiertos y si el archivo citado ya cambió. Los recados del
> hub llegan a `_hub_encargos/`. Protocolo: `Análisis RMG/_orquestador/PROTOCOLO.md`.

### banco

Operativo. 17 capas descargadas (63.925 registros, 0 fallos) normalizadas a un
panel de cuatro cortes (16.001 tramos), más ocho scripts de análisis y cruce que
producen **17 salidas**. Documentado en [`FICHA_DOMINIO.md`](FICHA_DOMINIO.md),
que es la fase 0 del dominio y demuestra **13 trampas** ejecutando.

Sin resolver, y anotado como tal: el pico de **714,9 km declarados con año de
ejecución 2017** —el 25,3 % de la red existente— no está confirmado con SECTRA.

### visor

Publicado en <https://romedinag-tech.github.io/ciclovias/>. Tres secciones
—infraestructura, demanda, espacial—, tema claro/oscuro y paleta para daltonismo,
en un solo `index.html` de 7,89 MB con el payload incrustado. El mapa trabaja
sobre **zona censal** (4.577) con siete capas; los dos indicadores de la EOD van
normalizados por población y **condicionados a la muestra** (556 de 3.030 zonas
con EOD, 18,3 %).

## Entradas y salidas

**Produce**, y otros consumen:

- `data/analisis/` — **contrato de 17 salidas** que consume la skill
  `diag-ciclovias`. Renombrar o borrar una columna la rompe sin aviso.
- `data/parquet/catastro_panel.parquet` — la tabla canónica del catastro.
- El visor publicado, y las figuras de informe que exporta.
- Detalle en [`SALIDAS.md`](SALIDAS.md), que se autogenera desde
  `_diagnostico_kit/catalogo.json`.

**Consume, todo en solo lectura:** `GIS Gran Concepción` (manzanas y zonas Censo
2024, NSE por zona, geometría comunal), `EODs` (EOD homologadas, dataset
analítico e índice), `dashboard accidentes` (siniestros con ciclista),
`SERVEL/anclas` (directorio MINEDUC) y
`Hub Multidato\datos_oro\uso_suelo\comuna.geojson` (las 345 comunas INE, que
es la capa contra la que se valida la llave comunal).

## Datos canónicos

- `C:\Users\Rodrigo\Análisis RMG\Ciclovias\data\parquet\catastro_panel.parquet`
  — **la tabla que manda**. Grano: tramo × corte. Para hablar de red hay que
  filtrar **los dos** ejes, `corte` y `etapa`: sólo por `etapa` se suman las
  cuatro versiones y salen 10.330,2 km en vez de los **2.827,7 km existentes** de
  los 7.064,1 catastrados en el corte vigente (2026-07).
- `C:\Users\Rodrigo\Análisis RMG\Ciclovias\data\analisis\` — las 17 salidas
  del contrato. Granos: comuna, manzana censal, zona censal, tramo, componente
  conexa, punto y ciudad-año EOD.
- `C:\Users\Rodrigo\Análisis RMG\Ciclovias\data\MANIFIESTO.json` — la traza
  de la descarga.

**No sensible:** todo es agregado o infraestructura pública. No hay microdato
individual y no debe introducirse.

**Copias que NO se usan:** `data/raw/` (GeoJSON crudo, fuera de git, se
regenera), `_work/payload.json` (intermedio, no se versiona) y la capa 1 del
servicio de SECTRA, que no se suma a la vigente. Las trampas de cada fuente están
demostradas en [`FICHA_DOMINIO.md`](FICHA_DOMINIO.md) y no se repiten acá.

## Aprendizajes

La bitácora completa, con fecha y en orden, está en **[Bitácora de
aprendizajes](#bitácora-de-aprendizajes)**, en el manual de abajo. Todos son de
la misma familia: **fallas que no lanzan error**. Los tres que más se repiten:

- 2026-09-19 — **Un script que reescribe una tabla borra lo que otro le agregó.**
  `analisis_zonas.py` regenera `zona_demanda` entera, y las tres columnas de
  siniestros por zona sobrevivían de una corrida antigua: ningún script vigente
  las producía. El indicador del visor se habría quedado sin dato sin fallar. Hoy
  se calculan dentro del mismo script que escribe la tabla.
- 2026-09-15 — **Un reporte externo puede acertar en la cifra y errar en la
  causa.** Se arregla el mecanismo medido, no el propuesto. Ver el global.
- 2026-09-06 — **El disparador que se deja escrito es el que paga.** Reconstruir
  desde el microdato en vez de copiar un agregado ajeno dejó al banco inmune a
  una corrección aguas arriba, y el snapshot antes/después lo demostró.

## Cómo se ejecuta

```bash
cd "C:/Users/Rodrigo/Análisis RMG/Ciclovias"
python -X utf8 scripts/descarga_arcgis.py    # ArcGIS REST -> data/raw + data/parquet
python -X utf8 scripts/normaliza.py          # -> catastro_panel (falla si un CUT no es INE)
# ... seis scripts de análisis y cruce ...
python -X utf8 scripts/analisis_zonas.py     # agrega a zona censal
python -X utf8 scripts/cruza_eod_zonas_censales.py
python -X utf8 scripts/genera_catalogo.py && python -X utf8 scripts/genera_analisis.py
python -X utf8 scripts/prepara_payload.py && python -X utf8 scripts/genera_visor.py
```

El pipeline completo, con sus dos dependencias de orden, está en **[Pipeline y
fuentes, en detalle](#pipeline-y-fuentes-en-detalle)**. Al cerrar un bloque: subir
`version.json`, commit y push; GitHub Pages sirve desde `main`.

<!-- columna-vertebral: ultima_actualizacion=2026-09-19 commit=4811871 -->

---


## El proyecto en detalle
Base de datos propia sobre infraestructura ciclista y uso de la bicicleta en
Chile, construida desde las fuentes oficiales de SECTRA/MTT y MINVU y cruzada con
Censo 2024, EOD y siniestralidad. Tiene **dos dimensiones**, con público y
producto distintos:

- **banco** — los datos y los análisis. Sirve para responder preguntas a medida
  que todavía no existen: se consulta el Parquet y se calcula lo que haga falta.
- **visor** — el sitio publicado. Sirve para leer la información en formato
  gráfico desde la web, siempre disponible, sin abrir un entorno de análisis.

El visor no tiene fuentes propias: consume lo que produce el banco.

## Detalle del estado

La fecha y el commit vigentes están en la ficha de arriba; acá va el detalle.

### banco

Operativo. 17 capas descargadas (63.925 registros, 0 fallos), normalizadas a un
panel de cuatro cortes, más **ocho scripts de análisis y cruce** que producen 17
salidas: cobertura poblacional, accesibilidad a equipamiento educacional,
conectividad de red, demanda censal y de la EOD con sus cruces por sexo, edad,
quintil, propósito y hora, distribución de distancias, KPI por ciudad,
agregación a zona censal y el cruce de la EOD a esa zonificación.

Documentado en [`FICHA_DOMINIO.md`](FICHA_DOMINIO.md), que es la fase 0 del
dominio: inventario, cobertura medida año a año y unidad por unidad, nulos por
campo y por región, trece trampas demostradas ejecutando, contraste de
referencia sobre el Gran Concepción e indicadores ya calculados, separando los
publicados y estables de las recetas re-ejecutables.

Sin resolver, y anotado como tal: el pico de **714,9 km declarados con año de
ejecución 2017**, muy por encima de cualquier otro año, no está confirmado con
SECTRA. Puede ser el cierre de una cartera grande o el año por defecto asignado a
tramos de fecha desconocida.

### visor

Publicado en <https://romedinag-tech.github.io/ciclovias/>, tres secciones
—infraestructura, demanda, espacial— con tema claro/oscuro y paleta para
daltonismo. Un solo `index.html` de 7,89 MB con el payload incrustado.

El mapa trabaja sobre **zona censal** —la comuna resultó demasiado gruesa para
ver diferencias dentro de una ciudad— con siete capas: red existente, franja de
300 m, cartera futura, contadores, siniestros con ciclista, su concentración y
equipamiento educacional. Los dos indicadores de la EOD van **normalizados por
población y condicionados a la muestra**: sólo se pinta la zona con al menos
cinco viajes en bicicleta encuestados detrás, que a escala nacional es el
18,3 % de las zonas con EOD. Cada gráfico se amplía y se descarga como PNG, y el
mapa se exporta como **figura de informe con su leyenda compuesta**.

## Pipeline y fuentes, en detalle
### banco

Pipeline, en este orden:

```bash
python -X utf8 scripts/descarga_arcgis.py       # ArcGIS REST -> data/raw + data/parquet
python -X utf8 scripts/normaliza.py             # -> catastro_panel, catastro_comuna
python -X utf8 scripts/analisis_cobertura.py    # distancia manzana/establecimiento a la red
python -X utf8 scripts/analisis_conectividad.py # componentes conexas + sensibilidad
python -X utf8 scripts/analisis_demanda.py      # Censo + EOD + contadores + siniestros
python -X utf8 scripts/analisis_eod_cruces.py   # bicicleta por sexo, edad, quintil, hora x propósito
python -X utf8 scripts/analisis_eod_distancias.py  # distribución de distancias por ciudad
python -X utf8 scripts/analisis_eod_kpi.py      # KPI por ciudad, con tiempo y distancia propios
python -X utf8 scripts/analisis_zonas.py        # agrega a zona censal
python -X utf8 scripts/cruza_eod_zonas_censales.py # EOD -> zonificación censal
python -X utf8 scripts/genera_catalogo.py       # MANIFIESTO.json -> FUENTES.md
python -X utf8 scripts/genera_analisis.py       # data/analisis -> ANALISIS.md
```

El orden importa en dos puntos: `analisis_eod_kpi.py` lee el resumen que produce
`analisis_eod_distancias.py`, y `cruza_eod_zonas_censales.py` escribe sobre el
`zona_demanda` que produce `analisis_zonas.py`.

`scripts/fuentes.py` es el registro declarativo de qué se baja y de dónde; es el
único archivo que se edita para agregar una capa.

**Regla de oro: ninguna cifra se escribe a mano.** `FUENTES.md` y `ANALISIS.md`
se **generan** leyendo el dato en ese momento; editarlos a mano los desincroniza
en silencio.

Insumos externos, todos en **solo lectura**: `GIS Gran Concepción` (manzanas y
zonas Censo 2024, NSE por zona, geometría comunal), `EODs` (EOD homologadas,
`viajes_analiticos.parquet` e `indice_eod.csv`), `dashboard accidentes`
(siniestros con ciclista), `SERVEL/anclas` (directorio MINEDUC) y
`Hub Multidato\datos_oro\uso_suelo\comuna.geojson`, las **345 comunas INE**
contra las que `normaliza.py` valida la llave comunal. Se usa ésa y no la capa
del proyecto `elecciones`, que tiene 129 pares de comunas solapadas y duplica
filas en un punto-en-polígono.

Respaldo metodológico: `docs/benchmark_minvu_2018.md` y el PDF en `docs/fuentes/`.

### visor

Dos pasos, deliberadamente separados: el payload tarda minutos y la maqueta se
itera decenas de veces.

```bash
python -X utf8 scripts/prepara_payload.py      # -> _work/payload.json (7,78 MB)
python -X utf8 scripts/genera_visor.py         # -> index.html
```

Al cerrar un bloque: subir `version.json`, commit y push. GitHub Pages sirve
desde `main`.

## Los datos, en detalle
### banco

`data/parquet/` es la fuente de trabajo y **va versionada**; `data/raw/` (GeoJSON
crudo) queda fuera de git y se regenera con el descargador. `data/MANIFIESTO.json`
es la traza de la descarga: conteos, campos y problemas detectados.

**Tabla canónica: `data/parquet/catastro_panel.parquet`.** Los cuatro cortes con
campos homogeneizados. Desde el 2026-09-15 la llave comunal viene auditada:
`cut_com_origen` dice si el CUT es el declarado por SECTRA o se resolvió por
nombre, `cut_com_geo` es la comuna que contiene el tramo, `dist_comuna_llave_m`
la distancia a la comuna de su llave y `cut_com_discrepa_geo` marca los 43 tramos
a más de 500 m de ella —todos en cortes históricos, ninguno en el vigente—. Y
`normaliza.py` **falla** si algún `cut_com` queda fuera de las 345 comunas INE:
es un control, no una advertencia. Para hablar de red hay que filtrar **los dos** ejes:
`corte` —si no, se suman las cuatro versiones y salen 10.330,2 km de red
existente— y `etapa`. En el corte vigente (2026-07), de 7.064,1 km catastrados
sólo **2.827,7 km** existen.

**`data/analisis/` es un contrato, no archivos de trabajo.** La skill
`diag-ciclovias` lo consume. Son **17 salidas**: las trece de cobertura,
conectividad y demanda —`manzana_cobertura`, `cobertura_comuna`,
`equipamiento_cobertura`, `conectividad_comuna`, `conectividad_sensibilidad`,
`componentes`, `tramo_componente`, `zona_demanda`, `demanda_comuna`,
`demanda_eod_ciudad`, `demanda_eod_perfil`, `demanda_eod_zona` y
`siniestros_bici`— más las cuatro de la EOD: `eod_cruces`, `eod_distancias`,
`eod_distancias_resumen` y `eod_kpi`. Renombrar o borrar una columna rompe la
skill sin previo aviso; agregar columnas es seguro.

**Las trampas de las fuentes viven en [`FICHA_DOMINIO.md`](FICHA_DOMINIO.md)**,
donde cada una está demostrada con el resultado de la consulta que la delata:
`CUT_COM` sin relleno de ceros, `CUT_REG` que contradice a la comuna, el
pseudo-valor `s_i`, `smp` como senda multipropósito, el `KM` declarado contra la
geometría y la serie de cortes que no mide construcción. Esa ficha es la fase 0
del dominio y se lee antes de consultar el banco.

Dos que no están allá porque son de la descarga y no del dato: el servicio
`CICLOV_validVisor_WFL1` publica **dos** capas de red y la vigente es la 0
—**no sumarlas**—, y `objectIdField` varía por capa (`OBJECTID`, `FID`,
`OBJECTID_12`), de modo que se lee del metadato y no se asume.

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

## Bitácora de aprendizajes
Todos de la misma familia: **fallas que no lanzan error**.

- `[banco]` 2026-09-04 — **ArcGIS responde `404`, no `414`, con una URL demasiado larga**, y el error se lee como «la capa no existe». Las consultas por bloque de OBJECTID van por **POST**.
- `[banco]` 2026-09-04 — La serie de cortes **no mide construcción**: el salto entre versiones es mejora de catastro. Medido y demostrado en [`FICHA_DOMINIO.md`](FICHA_DOMINIO.md), trampa 7.
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
- `[visor]` 2026-09-04 — **Las teselas de `basemaps.cartocdn.com` vuelven con HTTP 200 y la marca «API KEY REQUIRED» encima.** Ningún chequeo estructural lo detecta. Acá se usan los lienzos claro/oscuro de Esri, sin clave. **Cerrado el 2026-09-04: se decidió no modificar el estándar compartido** `_dashboard_kit/plantilla.html`, de modo que los dashboards copiados de ella —`antofagasta`, `comercio exterior`, los de Rapa Nui, `EODs` y Costanera Mar— siguen sirviendo teselas con marca de agua hasta que se decida lo contrario.
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
- `[banco]` 2026-09-04 — **`smp` es «senda multipropósito»** (MOP, berma de ruta rural). No está declarado en el servicio; la evidencia que lo deduce está en [`FICHA_DOMINIO.md`](FICHA_DOMINIO.md), trampa 4.
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

- `[banco]` 2026-09-04 — **El `pct_bicicleta` del indice del tablero de
  movilidad no es utilizable en todas las ciudades**: marcaba 0,00 % en Gran
  Concepcion y Curico, que segun la reconstruccion validada tienen 1,91 % y
  8,74 %. Se publica la reconstruccion propia y no ese campo.
  **Actualizado el 2026-09-06:** `EODs` corrigio el orden de comprobacion en
  `codigos_canonicos.py` —`'no caminata'` se evalua antes que `'caminata'`, que
  la contiene como subcadena— y el Gran Concepcion quedo en 1,9 %. **Curico
  sigue sin corregir**: declara 30,5 % de caminata y 0,0 % de bicicleta cuando
  el microdato dice 21,8 % y 8,7 %. Por eso ahora tampoco se copia el
  `pct_caminata` del indice: se reconstruye aca, con `cam_pct_propio` en
  `eod_kpi`, que reproduce al indice en las 14 ciudades donde ya es consistente.
- `[banco]` 2026-09-04 — **El tiempo de viaje se calcula aca, no se copia.**
  Traia dos razones y hoy queda una: el indice publicaba `tiempo_medio_min`
  solo en 8 de 18 ciudades y desde el 2026-09-06 lo trae en las 18, pero
  publica un PROMEDIO. Se usa
  la MEDIANA ponderada por el factor y con tope de 300 minutos, porque el campo
  llega con registros de hasta 1.435 minutos que arrastran cualquier promedio.
  Resultado util: el viaje en bicicleta dura sistematicamente menos que el
  mediano de su ciudad (Santiago 15 contra 30 minutos), lo que no dice que sea
  rapida sino que se usa para los viajes cortos.

- `[visor]` 2026-09-04 — **La sintaxis del JS generado se valida con Node antes
  de abrir el navegador**: `node -e "new Function(script)"` sobre el bloque
  extraido del HTML. Una llave de mas dejaba `scales` como segundo argumento de
  `opt()` y el visor entero quedaba en blanco; en el navegador eso aparece como
  un `SyntaxError` sin linea util, mientras que la comprobacion previa cuesta
  un segundo.
- `[banco]` 2026-09-04 — **Las trampas de las fuentes se documentan una sola vez**,
  en [`FICHA_DOMINIO.md`](FICHA_DOMINIO.md), que las demuestra con la consulta que
  las delata. Este archivo las referencia y no las repite: tenerlas en dos lugares
  garantiza que una de las dos versiones envejezca sin que nadie lo note.
- `[banco]` 2026-09-05 — **La EOD no sostiene el nivel de zona para la
  bicicleta, y no falla al intentarlo**: produce un número por zona que parece
  dato. En el Gran Concepción son 800 viajes encuestados en 359 zonas de origen
  —mediana 2, y 77 zonas con uno solo— expandidos por un factor medio de 42,8.
  Lo que lo delata no es el tamaño de muestra sino su consecuencia: la razón
  entre viajes EOD y ciclistas del Censo debería ser casi constante entre zonas
  de una misma ciudad; en el agregado da 4,25 y por zona va de 0,56 (p10) a
  12,9 (p90). Por eso `cruza_eod_zonas_censales.py` arrastra `eod_n_gen` y
  `eod_n_atr`, los viajes **encuestados** detrás de cada cifra. Medido y
  tabulado ciudad por ciudad en [`FICHA_DOMINIO.md`](FICHA_DOMINIO.md),
  trampa 10.
- `[visor]` 2026-09-05 — **Una tasa y un conteo puestos en dos coropletas se
  leen como contradictorios aunque los dos sean correctos.** El `bici_pct` del
  Censo no depende del tamaño de la zona (ρ con población = −0,03) y los viajes
  EOD generados sí (+0,33), de modo que la misma zona salía verde en un mapa y
  roja en el otro. Todo conteo que comparta selector con una tasa va
  normalizado. Y `eod_bici_gen` contra `eod_bici_atr` eran prácticamente el
  mismo mapa (ρ = 0,995): lo que distingue al barrio que produce viajes del que
  los recibe es el **saldo**, con escala divergente en torno a cero, no cada
  lado por separado.
- `[visor]` 2026-09-05 — **Un gris de «no medido» tiene que ser distinguible
  del centro de la escala divergente**, que también es neutro. Con la misma
  opacidad, `#D9DCE1` y el `#EFEDE4` del centro de BrBG eran indistinguibles y
  no había forma de separar «zona equilibrada» de «zona sin muestra». Se
  resuelve con dos señales a la vez: gris más oscuro y opacidad al 42 %, para
  que la ausencia se lea como ausencia y no como un valor más.
- `[visor]` 2026-09-05 — **Un indicador divergente no se corta por cuantiles.**
  El cero tiene significado y los cuantiles lo desplazan a donde caiga la
  mediana, con lo que una zona equilibrada aparece pintada como si tuviera
  saldo. Los cortes van simétricos en torno a cero, escalados por el percentil
  90 del valor absoluto para que unas pocas zonas extremas no aplasten el resto.
- `[banco]` 2026-09-06 — **El disparador que se deja escrito es el que
  paga.** `EODs` corrigio la homologacion de modos del Gran Concepcion y la
  unica forma de saber si eso invalidaba lo publicado aca era la igualdad que
  se habia dejado anotada: la reconstruccion propia contra `viajes_analiticos`.
  Dio r = 1,00000 y diferencia cero en las 15 ciudades, de modo que ningun
  calculo propio se movio —`eod_cruces`, `eod_distancias` y las columnas
  propias de `eod_kpi` salieron identicas bit a bit—. Lo unico que cambio
  fueron los tres campos que se **copiaban** del indice. La leccion no es sobre
  la EOD: reconstruir desde el microdato en vez de copiar un agregado ajeno es
  lo que dejo el banco inmune a una correccion aguas arriba, y el snapshot
  antes/despues es lo que permitio demostrarlo en vez de suponerlo.
- `[banco]` 2026-09-06 — **Un 0,0 % en un agregado ajeno casi nunca es una
  medicion.** El indice declara 0,0 % de no motorizado en Gran Valparaiso y San
  Antonio, y ninguna ciudad tiene cero viajes a pie: es ausencia codificada
  como cero, y el tablero la mostraba como dato. Se publica como sin dato. Es
  la misma familia que el `pct_bicicleta` en cero de Curico, y por eso conviene
  desconfiar del cero exacto antes que del valor raro.
- `[banco]` 2026-09-15 — Un reporte externo acertó en las cifras y erró en la
  causa: los `cut_com` en `00000` los producía `CUT_COM = 0` de SECTRA, no el
  espacio duro, y eran 28 y no 26. **Promovido al `CLAUDE.md` global.** Acá
  quedó el control que falla si un CUT no es INE, probado inyectando una llave
  mala; el detalle está en la ficha, trampas 1 a 1c.
- `[banco]` 2026-09-15 — Un filtro `str(dtype).startswith('string')` se salta
  la columna entera en pandas 3, que llama `str` a su dtype de texto: un conteo
  de espacios duros dio 0 donde había 46. **Promovido al `CLAUDE.md` global**,
  que es donde vale.
- `[banco]` 2026-09-15 — **El snapshot antes/después separa lo propio de lo
  ajeno.** Re-ejecutar cobertura para verificar el arreglo de la llave trajo
  cambios que no eran de ese arreglo: `GIS Gran Concepción` regeneró
  `analysis_zona.parquet` ese día y el NSE se movió en 13.901 manzanas y 17
  comunas (±0,1 punto), más el contorno de Punta Arenas. El arreglo de la llave
  resultó neutro en todos los análisis —distancias, cobertura y componentes
  idénticos— y el NSE se restauró del snapshot para no publicar una zona censal
  con NSE de una fecha y manzanas de otra. **Pendiente decidir** si se
  incorpora esa actualización del NSE, re-ejecutando la cadena completa.

- `[banco]` 2026-09-19 — **Un script que reescribe una tabla borra lo que otro
  le agregó, y nadie se entera.** `analisis_zonas.py` regenera `zona_demanda`
  completa. Las tres columnas de siniestros por zona —`sin_bici`, `sin_fall`,
  `sin_grav`— sobrevivían de una corrida antigua y **ningún script vigente las
  producía**: al re-ejecutar el pipeline desaparecieron, y el indicador
  «Siniestros con ciclista» del visor se habría quedado en blanco sin lanzar un
  error, porque el payload las lee con `getattr(..., None)`. Ahora se calculan
  dentro del mismo script que escribe la tabla. Se validó contra el snapshot:
  11.607 siniestros, 167 fallecidos y 2.004 graves, cero filas distintas. De
  paso quedó a la vista que la columna `zona` de `siniestros_bici` dice
  `URBANA`/`RURAL` y **no** es la zona censal: el cruce es espacial.
- `[banco]` 2026-09-19 — **Incorporada la actualización del NSE** de
  `GIS Gran Concepción` del 2026-09-15: 13.901 manzanas y 17 comunas (±0,1
  punto, 0,4 en una) y 294 zonas censales en el visor. No movió la cobertura
  —96,8 % de las manzanas, 4.561 de 4.577 zonas— ni ningún otro indicador.

### Archivo

- `[visor]` 2026-09-04 — Una casilla de capa que nunca tiene datos es peor que no
  tenerla: la de mediciones SECTRA se escondía cuando el territorio no tenía
  ninguna. Obsoleto desde el mismo día: **la capa se eliminó del visor**. El dato
  sigue en el banco y en la ficha de dominio.

