# Ciclovías — banco de datos de movilidad activa (bicicleta), Chile

Proyecto para construir una base de datos propia sobre infraestructura ciclista y
uso de la bicicleta en Chile, a partir de las fuentes oficiales publicadas por
**SECTRA/MTT** y **MINVU**, y para analizar sobre ella.

Estado: **base de datos levantada y versionada**. Los análisis parten desde acá.

---

## Regla de oro del proyecto

**Ninguna cifra se escribe a mano en un documento.** Todo número publicado en
`FUENTES.md` o en cualquier entregable sale de leer `data/MANIFIESTO.json` o los
Parquet en ese momento. `FUENTES.md` se regenera, no se edita:

```bash
python -X utf8 scripts/genera_catalogo.py
```

---

## Estructura

```
Ciclovias/
├── scripts/
│   ├── fuentes.py            # registro declarativo: qué se baja y de dónde
│   ├── descarga_arcgis.py    # descargador paginado por OBJECTID + verificaciones
│   └── genera_catalogo.py    # MANIFIESTO.json -> FUENTES.md
├── data/
│   ├── raw/                  # GeoJSON crudo (fuera de git, se regenera)
│   ├── parquet/              # destilado de trabajo — ESTO va versionado
│   └── MANIFIESTO.json       # qué se bajó, cuántos registros, qué problemas
├── docs/fuentes/             # PDF de respaldo metodológico
├── FUENTES.md                # catálogo generado (no editar a mano)
└── _work/                    # scratch, fuera de git
```

## Cómo se baja el dato

`descarga_arcgis.py` no usa `resultOffset`. Pide primero **todos los OBJECTID**
(`returnIdsOnly=true`) y luego consulta por bloques con `where <oid> IN (...)`.
Es más robusto —no depende de que el servidor soporte paginación ni de que el
orden sea estable— y da una **cota independiente**: el número de ids recuperados
se contrasta contra `returnCountOnly`. Toda discrepancia queda escrita en el
campo `problemas` del manifiesto, nunca se silencia.

Verificaciones que corren en cada capa, y que quedan registradas:

- registros descargados vs `count` declarado por el servicio;
- registros sin geometría;
- *bounding box* dentro del rango de Chile continental e insular austral.

Los campos `esriFieldTypeDate` llegan como **epoch en milisegundos**. Se
conserva el valor original y se agrega una columna `<campo>_iso` al lado.

## Hallazgos verificados sobre el dato

Todo lo de abajo se midió sobre los Parquet descargados; se reproduce corriendo
`python -X utf8 scripts/normaliza.py`.

**El catastro no es una red construida: es un ciclo de vida completo.** De los
4.850 tramos del corte 2026-07, sólo 1.971 están en etapa `existentes`. Los
7.064,1 km que suma el catastro entero se reducen a **2.827,7 km existentes**;
el resto son 347,9 km en ejecución, 2.026,7 km en diseño y 1.861,8 km
planificados. Reportar «km de ciclovías de Chile» sobre el total infla la red a
más del doble. Filtrar siempre por `etapa == 'existentes'`.

**La serie de cortes NO mide construcción.** Entre el corte de noviembre de 2024
y el de julio de 2025 la red existente crece 441,1 km, pero al identificar los
268 tramos que aparecen nuevos y leer su año de ejecución declarado, sólo **25
tramos y 18,6 km** declaran 2025 o posterior. En cambio 201 tramos y 332,1 km
corresponden a obras de 2024 o antes que simplemente no estaban catastradas, y
otros 166,9 km no traían año. Es decir: el salto es **mejora de catastro, no obra
nueva**, y quien calcule construcción anual restando versiones consecutivas la
sobreestima en más de un orden de magnitud. Para medir construcción hay que usar
`year_ejecucion` dentro de un mismo corte, nunca la diferencia entre cortes.

Con ese método, y sobre el corte 2026-07, el año declarado con más kilometraje es
**2017 con 714,9 km en 456 tramos**, muy por encima de cualquier otro año de la
serie. Antes de usar esa cifra hay que confirmarla con SECTRA: un pico así puede
ser real (cierre de una cartera grande) o puede ser el año que se asignó por
defecto a tramos de fecha desconocida. Está sin verificar.

**La geometría es consistente con el atributo.** El kilometraje declarado del
corte 2026-07 (7.064,1 km) y el medido sobre la geometría reproyectada a
EPSG:32719 (7.056,9 km) difieren en **0,10 %**. El campo `KM` es confiable; aun
así `normaliza.py` guarda `km_geom` al lado para poder auditarlo.

**El crecimiento de cobertura comunal sí es legible.** Las comunas con al menos un
tramo existente pasan de 193 (sep-2024) a 222 (jul-2026).

## Trampas ya detectadas en las fuentes

- **`CUT_COM` viene sin relleno de ceros en las regiones 1 a 9**: 2.496 de los
  4.850 registros del corte 2026-07 traen 4 dígitos («9201» por «09201»).
  Normalizar con `zfill(5)` antes de cualquier cruce, o el join falla justo en
  media Araucanía, Biobío y el norte.
- **`CUT_REG` no es confiable y no debe usarse.** 29 registros del panel (0,18 %)
  declaran una región que no corresponde a su comuna: tramos de Negrete y Los
  Ángeles marcados región 9 siendo del Biobío, y un tramo de Colina marcado
  región 6. El `CUT_COM` sí está correcto en esos casos, de modo que la región se
  **deriva** de sus dos primeros dígitos. `normaliza.py` deja la discrepancia
  marcada en `cut_reg_declarado_discrepa` en lugar de corregirla en silencio.

- **`minvu_contadores.COMUNA` no trae el nombre de la comuna, trae el código
  CUT.** El campo `CUT_COM` repite ese mismo valor. Si se necesita el nombre hay
  que unirlo desde el maestro comunal, nunca leerlo de `COMUNA`.
- El servicio SECTRA `CICLOV_validVisor_WFL1` publica **dos** capas de red
  (`CICLOVIA_jul2026` con más registros y `CICLOVIA_LOCAL_CAPA2` con menos). La
  vigente es la capa 0; la 1 se conserva marcada `vigente=False` sin
  interpretarla, porque **no está confirmado** si es un respaldo previo o un
  subconjunto editable. No sumarlas.
- Los nombres de campo cambian entre cortes del catastro nacional
  (`EMPLAZA_TEX`/`EMPLAZA_TE`, `NOM_PROYECTO`/`NOMBRE_PRO`,
  `FECHA_EJECUCION`/`YEAR_EJECU`/`YEAR_EJECUCION`). Cualquier comparación entre
  años exige mapear campos explícitamente, no concatenar.
- El campo `objectIdField` varía por capa (`OBJECTID`, `FID`, `OBJECTID_12`); el
  descargador lo lee del metadato, no lo asume.
- **ArcGIS responde `404` cuando la URL es demasiado larga**, no `414`. Al pedir
  los tramos por lista de OBJECTID en bloques de 400, la query string supera el
  límite del servidor y el error se lee como «la capa no existe» cuando en
  realidad es «la URL no cabe». Por eso las consultas por bloque van por **POST**.
  Costó un diagnóstico falso: las capas chicas pasaban en un solo bloque y sólo
  fallaba el catastro, que es justo el dato central.

## Lo que NO se guarda acá, y por qué

- **Geometría comunal.** Las cinco capas de indicadores ICC repiten los mismos
  polígonos de comuna con distintos atributos; guardarlas completas costaba unos
  120 MB de geometría duplicada. Se descargan con `solo_atributos=True` y se unen
  por `cod_comuna` → `cut_com` contra la división comunal que el repo ya tiene.
- **Manzanas censales.** La base nacional de manzanas (Censo 2024 + catastro SII,
  llave `MANZENT`) ya vive en `GIS Gran Concepción`, en **solo lectura**. No se
  duplica. La capa `minvu_manzanas_poblacion_beneficiada` sí se conserva con
  geometría porque es cosa distinta: es la *selección* que hizo MINVU de las
  manzanas dentro del área de influencia, con su cifra oficial de población
  beneficiada, y **no trae `MANZENT`**, de modo que sólo puede unirse a nuestra
  base por cruce espacial. Ese cruce, cuando se haga, se materializa acá.

## Benchmark metodológico (MINVU 2018)

`docs/fuentes/minvu_2018_analisis_contadores.pdf` es análisis **descriptivo**
sobre 48 ejes en 23 sistemas y 19 ciudades con más de 9 meses de contador. Sus
cifras son la referencia contra la cual validar cálculos propios sobre los
contadores. Área de influencia usada: **694 m medidos por la red vial**.

Efectos reportados sobre pasadas promedio diarias:

| Variable | Efecto | Base → con atributo |
|---|---|---|
| Emplazamiento en bandejón-parque | +69 % | vs acera/bandejón/mixta |
| Emplazamiento en calzada | +59 % | vs acera/bandejón/mixta |
| Bicibox en intersecciones | +36 % | 192 → 262 |
| Biciestacionamientos junto a la ciclovía | +26 % | 197 → 249 |
| Ancho ≥ recomendado (bidir 2,4 m / unidir 1,8 m) | +17 % | 196 → 229 |
| ≥50 % de intersecciones a nivel de calzada | +5 % | 212 → 222 |
| Iluminación propia | **−8 %** | 211 → 204 |
| Fin de semana | −26 % | 228 → 169 |
| Temperatura mínima < 5 °C | −18 % | 221 → 182 |
| Día con lluvia | −37 % | 237 → 150 |
| Día con lluvia fuerte | −56 % | 217 → 96 |
| Día con viento fuerte | −74 % | 213 → 55 |

Por zona: la lluvia baja las pasadas **−35 % en el sur** (VIII región al sur) y
**−23 % en el norte**; la lluvia fuerte, **−53 %** y **−49 %** respectivamente.
Temperatura máxima: **+14 viajes por cada grado** adicional.

**Dos advertencias que hay que arrastrar al usar estas cifras.** Primero, la
relación con equipamientos que el propio informe reporta —`y = 0,5957x + 175,1`,
es decir +5,9 pasadas por cada 10 equipamientos— tiene **R² = 0,096**: explica
menos del 10 % de la varianza y no sostiene una afirmación causal ni predictiva.
Segundo, el informe declara explícitamente que los resultados son descriptivos y
no permiten inferir causalidad; el signo negativo de la iluminación es el caso
que más claramente delata variable omitida (probablemente ciclovías nuevas y
mejor iluminadas en ejes de menor demanda). Citar estos números como
correlaciones observadas, nunca como elasticidades de diseño.

Contexto de partición modal (ECVU 2015, citada en el mismo informe): **3,2 %** de
los desplazamientos al trabajo en bicicleta, y **49 %** de la población de
ciudades sobre 20.000 habitantes considera que no hay ciclovías en su comuna o
que son de mala calidad (sube a **63 %** en ciudades intermedias menores).

## Capa de análisis

`scripts/analisis_cobertura.py` y `scripts/analisis_conectividad.py` producen
`data/analisis/`, y `scripts/genera_analisis.py` escribe `ANALISIS.md` desde esas
salidas — misma regla que `FUENTES.md`: el documento no se edita a mano.

Tres decisiones de método que conviene no volver a discutir desde cero:

**Distancia en vez de buffer.** No se fija un radio y se cuenta lo que cae
adentro: se calcula para cada manzana y cada establecimiento la distancia al
tramo existente más cercano. Cualquier umbral se deriva después sin recalcular
—300 m es el del ICC de SECTRA, 694 m el del estudio MINVU 2018— y se puede
mostrar la curva completa en vez de un número que depende del radio elegido.

**El grafo de conectividad une tramos, no extremos.** Medido sobre la red
existente, el 37,0 % de los extremos coincide con el extremo de otro tramo, pero
otro **11,9 % cae sobre el interior de otro tramo**: son empalmes en T. Un grafo
que sólo mira extremos los pierde y reporta la red bastante más fragmentada de
lo que es — con el método por extremos la componente mayor daba 56,4 km y con el
correcto da 311,8 km. La tolerancia adoptada es **20 m**, elegida porque es donde
la curva se aplana: entre 20 y 50 m la componente mayor casi no se mueve. El
supuesto es optimista (dos ciclovías que se cruzan quedan unidas aunque el cruce
no permita virar), así que la fragmentación reportada es una **cota inferior**.

**El NSE viene de la zona censal, no se recalcula.** Se une por `ID_ZONA` de la
manzana contra `zona` de `analysis_ready/analysis_zona.parquet` — llave verificada
(CUT + distrito + zona, p. ej. `810101001`). Resuelve el 96,8 % de las manzanas;
el resto queda NULL y se declara.

## Convenciones heredadas del repo

- Llave territorial: comuna `cut_com` (5 díg. INE), región `cut_reg` (2 díg.).
- CRS de publicación EPSG:4326; métrico EPSG:32719.
- `python -X utf8` siempre (Windows/es-CL).
- Privacidad: todo lo aquí guardado es agregado (manzana, comuna) o
  infraestructura pública. No hay microdato individual y no debe introducirse.

## Publicación

Repositorio: `romedinag-tech/ciclovias`. Se versiona el Parquet (compacto y es
la fuente de trabajo) y no el GeoJSON crudo, que se regenera corriendo el
descargador.
