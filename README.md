# Ciclovías Chile — banco de datos de movilidad activa

Base de datos propia sobre **infraestructura ciclista y uso de la bicicleta en
Chile**, construida a partir de las fuentes oficiales publicadas por SECTRA /
Ministerio de Transportes y Telecomunicaciones y por el Ministerio de Vivienda y
Urbanismo, descargadas íntegramente desde sus servicios ArcGIS REST.

El inventario completo —capas, número de registros, campos, servicio de origen y
verificaciones de integridad— está en **[`FUENTES.md`](FUENTES.md)**, que se
genera automáticamente y no se edita a mano.

## Qué contiene

- **Catastro Nacional de Ciclovías (SECTRA)** en varios cortes temporales, desde
  septiembre de 2024 hasta el corte vigente. Cada tramo trae eje, inicio y fin,
  kilometraje, tipo, característica funcional, emplazamiento, etapa, cartera,
  código BIP o PMU, normativa y llave territorial (`CUT_REG`, `CUT_COM`). Tener
  varios cortes del mismo catastro permite medir el crecimiento de la red y no
  sólo fotografiarla.
- **Índice de ciclo-inclusión comunal (ICC, SECTRA)** para el universo de comunas
  del país, con km de red vial, km de ciclovía, nodos, población y equipamientos
  cubiertos a 300 m, e índices normalizados de red y de cobertura. Incluye la
  versión que incorpora la cartera planificada, lo que habilita comparar la
  situación actual contra el escenario con proyectos.
- **Contadores automáticos de flujo de bicicletas (MINVU)**: puntos de medición
  permanente con media diaria, semanal y mensual, promedio de día hábil contra
  fin de semana, mínimo y máximo diario, y la ventana de observación de cada
  equipo.
- **Mediciones de flujo ciclista (SECTRA)** en Antofagasta y Talca: puntos de
  control con conteos por período, total de ciclos y factores de expansión de
  ciclos y vehículos.
- **Red de ciclovías MINVU** (medida presidencial y otras medidas) y su entorno:
  equipamientos cercanos y manzanas censales con población beneficiada,
  desagregada por sexo y tramo etario.
- **Respaldo metodológico**: el análisis descriptivo de contadores de MINVU
  (2018), que fija el área de influencia de 694 m medida por la red vial y aporta
  las magnitudes de referencia sobre diseño, entorno y clima.

## Estructura

```
scripts/fuentes.py          registro declarativo de qué se descarga y de dónde
scripts/descarga_arcgis.py  descarga completa + verificaciones de integridad
scripts/genera_catalogo.py  MANIFIESTO.json -> FUENTES.md
data/parquet/               destilado de trabajo (versionado)
data/raw/                   GeoJSON crudo (no versionado, se regenera)
data/MANIFIESTO.json        traza de la descarga: conteos, campos, problemas
docs/fuentes/               documentos de respaldo
```

## Reproducir la descarga

```bash
python -X utf8 scripts/descarga_arcgis.py
python -X utf8 scripts/genera_catalogo.py
```

Requiere `geopandas`, `shapely` y `pyarrow`. La descarga se pagina pidiendo
primero todos los `OBJECTID` de cada capa y consultándolos por bloques, de modo
que el conteo recuperado se pueda contrastar contra el que declara el servicio;
cualquier discrepancia queda escrita en `data/MANIFIESTO.json` y publicada en
`FUENTES.md` en vez de corregirse en silencio.

## Alcance y límites

Todo el contenido es **agregado o de infraestructura pública** —tramos de
ciclovía, puntos de contador, indicadores comunales, manzanas censales— y no
incluye microdato individual. Las cifras del informe MINVU 2018 recogidas en
[`CLAUDE.md`](CLAUDE.md) son **descriptivas**: el propio informe advierte que no
permiten inferir causalidad, y la relación que reporta entre equipamientos y
pasadas tiene un R² de 0,096, de modo que no sostiene uso predictivo.

Los datos son de sus organismos de origen (SECTRA/MTT y MINVU) y se redistribuyen
aquí sólo como copia de trabajo, con la traza de su procedencia.
