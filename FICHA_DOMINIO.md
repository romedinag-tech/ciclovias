# Ficha de dominio · CICLOVÍAS Y MOVILIDAD ACTIVA

> Qué hay en este banco y cómo se usa, para no tener que volver a analizarlo cada vez.
> **Todas las cifras se midieron ejecutando sobre los archivos el 4 de septiembre de 2026.**
> Lo que no se pudo medir se declara como brecha; nada se deduce del nombre de un archivo.

## Inventario

54 archivos de datos, 243,2 MB. El GeoJSON crudo (147 MB) queda fuera de git y se regenera
corriendo el descargador; el Parquet es lo que se versiona.

| Formato | Archivos | Peso |
|---|---:|---:|
| `.geojson` (crudo, regenerable) | 12 | 147,1 MB |
| `.parquet` | 36 | 80,5 MB |
| `.json` (manifiesto y payload) | 4 | 7,8 MB |
| `.html` (visor publicado) | 1 | 7,6 MB |
| `.pdf` (respaldo metodológico) | 1 | 0,3 MB |

Reparto por carpeta: `data/parquet` 19 archivos y 50,4 MB (descarga normalizada),
`data/analisis` 17 archivos y 30,1 MB (resultados), `data/raw` 12 archivos y 147,1 MB (crudo).

### Cuál es el archivo canónico

**Para cualquier análisis nuevo: `data/parquet/catastro_panel.parquet`** — 16.001 filas, los cuatro
cortes del Catastro Nacional con los nombres de campo homogeneizados y la llave territorial
normalizada. Es el único archivo del banco donde `cut_com` tiene siempre cinco dígitos y la región
está derivada y no declarada.

`data/parquet/sectra_ciclovias_nac_2026_07.parquet` (4.850 tramos) es la **descarga cruda** del corte
vigente. Sirve para auditar contra el servicio de SECTRA, no para analizar: sus llaves vienen sin
normalizar y filtrar por ellas descarta datos en silencio (ver Trampa 1).

Historial, no vigente: `sectra_ciclovias_nac_2025_07` (4.217), `_2024_11` (3.511) y `_2024_09`
(3.423). Se conservan porque permiten distinguir obra nueva de mejora de catastro, no porque sean
versiones alternativas.

`sectra_ciclovias_nac_local_capa2` (4.409 tramos) es la **capa 1 del mismo servicio** que la vigente.
Tiene menos registros y no está confirmado con SECTRA si es un respaldo previo o un subconjunto
editable. **No sumarla a la capa 0.**

### Las demás capas

| Capa | Filas | Qué aporta |
|---|---:|---|
| `sectra_icc_comunas` | 346 | Índice de ciclo-inclusión: km de red vial y de ciclovía, población y equipamiento cubiertos a 300 m, índices normalizados |
| `sectra_icc_comunas_planes` | 346 | El mismo índice incorporando la cartera planificada |
| `sectra_icc_red_ciclov` | 1.831 | La red efectivamente usada en el índice, que no es la red completa |
| `minvu_contadores` | 185 | Contadores automáticos de flujo ciclista |
| `minvu_manzanas_poblacion_beneficiada` | 33.232 | Selección MINVU de manzanas en el área de influencia, con su cifra oficial de población |
| `minvu_equipamientos` | 5.504 | Equipamiento cercano a ciclovías |
| `sectra_mediciones_antofagasta_talca` | 128 | Puntos de conteo con reparto por período, **sólo dos ciudades** |
| `manzana_cobertura` | 197.168 | Distancia de cada manzana a la red, con perfil censal y NSE |
| `zona_demanda` | 4.577 | Zona censal con demanda, cobertura, NSE, siniestros y viajes EOD |
| `siniestros_bici` | 13.357 | Siniestros con ciclista georreferenciados (CONASET) |
| `eod_kpi`, `eod_cruces`, `eod_distancias` | 18 / 621 / 297 | Demanda de la EOD por ciudad |

## Llave, grano y geometría

- **Llave territorial:** `cut_com`, código INE de comuna de cinco dígitos. En `catastro_panel` está
  normalizada; en los archivos crudos **no**. La región se deriva de sus dos primeros dígitos y
  nunca se toma del campo declarado.
- **Grano atómico:** el tramo de ciclovía, identificado por `identifica`. En el panel la llave es
  `identifica + corte`, porque el mismo tramo aparece en varios cortes.
- **Otros granos del banco:** manzana censal (`MANZENT`), zona censal (`zona`, formada por
  CUT + distrito + zona, p. ej. `810101001`), punto (contador, medición, establecimiento,
  siniestro) y componente conexa de red.
- **CRS:** EPSG:4326 en todos los Parquet. Para medir longitudes o distancias hay que reproyectar a
  **EPSG:32719**; la columna `km_geom` del panel ya viene medida así.
- **Peso de expansión:** el catastro no lleva. La demanda EOD sí, y es el campo `factor`, que debe
  aplicarse siempre; sin él las cifras describen la muestra y no la ciudad.

## Cobertura medida

### Temporal

**El banco no es una serie.** Cada corte del catastro es una fotografía completa, no un período:

| Corte | Tramos | km totales | Existentes | km existentes |
|---|---:|---:|---:|---:|
| 2024-09 | 3.423 | 5.132,6 | 1.631 | 2.351,4 |
| 2024-11 | 3.511 | 6.487,4 | 1.636 | 2.355,0 |
| 2025-07 | 4.217 | 6.464,1 | 1.854 | 2.796,1 |
| 2026-07 | 4.850 | 7.064,1 | 1.971 | 2.827,7 |

Para leer construcción hay que usar `year_ejecucion` **dentro de un corte**, nunca la diferencia
entre cortes (ver Trampa 7). Sobre el corte vigente, la red existente reparte así sus kilómetros:

- años **residuales** —menos de un vigésimo del año mayor—: 1996 a 2011 salvo 2005, más 2026, que
  suman en conjunto 220,9 km;
- concentración fuerte en **2017 con 714,9 km en 456 tramos, el 25,3 % de toda la red existente**,
  muy por encima de cualquier otro año;
- los últimos años declaran entre 78 y 145 km anuales.

**Contadores MINVU:** ventana del 4 de diciembre de 2015 al 5 de noviembre de 2024. 124 de los 185
contadores tienen su último registro en 2024; 23 en 2023 y 21 en 2021.

**Siniestros con ciclista:** cinco años completos y comparables — 2020 (2.787), 2021 (2.997),
2022 (2.778), 2023 (2.514) y 2024 (2.281).

**EOD:** 18 ciudades, cada una con **un año distinto** entre 2010 y 2023. No admite lectura temporal.

### Territorial

De las 334 comunas de la base censal, **246 tienen algún tramo catastrado y 222 tienen red
existente**. Las 89 restantes no aparecen en el catastro: entre ellas Camiña, Huara, Sierra Gorda,
María Elena, Chañaral, Diego de Almagro, Alto del Carmen y Freirina, todas de baja población en el
norte.

**Una comuna del catastro no existe en la base censal: `12104` (San Gregorio, Magallanes), con tres
tramos existentes.** Cualquier cruce con el Censo la pierde, y hay que declararlo en vez de dejar
que desaparezca del conteo.

### Nulos, campo por campo (corte vigente, 4.850 tramos)

El catastro casi no tiene celdas vacías: lo que tiene es el pseudo-valor **`s_i`**, que significa
«sin información» y **no es nulo**, de modo que `notna()` lo cuenta como dato.

| Campo | Nulo | `s_i` |
|---|---:|---:|
| `identifica`, `eje_via`, `km`, `etapa`, `cut_com` | 0,0 % | 0,0 % |
| `inicio` / `fin` | 0,0 % | 2,7 % / 4,0 % |
| `tipo` | 0,0 % | 8,6 % |
| `carac_func` | 0,0 % | 41,6 % |
| `emplaza_txt` | 0,0 % | 43,4 % |
| `nombre_proyecto` | 0,6 % | 44,0 % |
| `bip_pmu` | 0,6 % | 56,5 % |
| `year_ejecucion` | 2,6 % | 56,6 % |
| `normativa` | 0,8 % | 68,9 % |

**El `year_ejecucion` está sin informar en el 56,6 % del catastro completo pero completo al 100 % en
la red existente.** Esa distinción es lo que permite medir construcción: el año existe para lo
construido, no para la cartera.

### Nulos por unidad territorial

Es la sección que evita el error más caro del banco. **La calidad del registro varía tanto entre
regiones que comparar sin advertirlo ordena por cobertura del dato y no por el territorio:**

| Campo | Mejor región | Peor región |
|---|---|---|
| `year_ejecucion` sin informar | 34 % (Araucanía, 205 tramos) | **84 %** (Arica, 135 tramos) |
| `emplaza_txt` sin informar | 0 % (Ñuble, 121 tramos) | **56 %** (Arica) |
| `tipo` sin informar | 0 % (Atacama, 80 tramos) | **48 %** (Arica) |
| `bip_pmu` sin informar | 10 % (Antofagasta, 139) | **80 %** (O'Higgins, 444) |

### Tipos reales

`year_ejecucion` es **texto**, no número: ordenar por ese campo sin convertirlo ordena
alfabéticamente y deja la cadena vacía delante de 1996. `cut_reg_declarado`, `urbana` y `emplaza_n`
son `double` aunque sean códigos. `km` y `km_geom` son `double` y sí se pueden sumar.

## Trampas, comprobadas ejecutando

**1 · `CUT_COM` viene sin relleno de ceros en el archivo crudo.** De los 4.850 registros, 2.496
traen cuatro dígitos y 2.354 cinco. Medido: filtrar `CUT_COM == '08101'` sobre el archivo crudo
devuelve **0 tramos**; filtrar `'8101'` devuelve 92. Sobre `catastro_panel` la consulta correcta
`cut_com == '08101'` devuelve los mismos 92. **Usar siempre el panel, o aplicar `zfill(5)` antes de
cualquier cruce.**

**2 · `CUT_REG` contradice a la comuna en cinco registros.** Colina aparece declarada en la región 6,
y tramos de Negrete y Los Ángeles en la región 9 siendo del Biobío. El `cut_com` está correcto en los
tres casos. **La región se deriva del `cut_com`**, y la discrepancia queda marcada en
`cut_reg_declarado_discrepa`.

**3 · `s_i` no es nulo.** Es el pseudo-valor de «sin información» y aparece hasta en el 68,9 % de un
campo. Un `groupby` lo trata como categoría y un `notna()` lo cuenta como dato.

**4 · Los códigos de `TIPO` no traen catálogo.** El servicio los publica sin dominio codificado:
`ciclovía` (3.687), `smp` (421), `s_i` (415), `zona30` (148), `cicloparque` (119). **`smp` es
«senda multipropósito»**, la infraestructura del MOP en la berma de una ruta rural. No está declarado
en ninguna parte del servicio: se dedujo del propio catastro, donde los nombres de proyecto de esos
tramos dicen «construcción de sendas multipropósito en red vial» y, medido, el **88 % son cartera
MOP, el 81 % rurales y el 77 % van por berma**.

**5 · El índice de ciclo-inclusión está calculado sobre la comuna completa.** Sus 346 filas traen
`ind_red`, `ind_cob` y sus versiones normalizadas, siempre para el polígono comunal entero. **No
sirve para un área menor**: para un polígono hay que reaplicar la receta, no recortar el valor
publicado.

**6 · El `KM` declarado no coincide con la geometría, y la diferencia crece al bajar de escala.**
Medido: país completo 7.064,1 declarados contra 7.056,9 geométricos (**0,10 %**); sólo la red
existente, 2.827,7 contra 2.844,4 (**0,59 %**); Gran Concepción, 159,9 contra 156,8 (**1,97 %**).
Hay que declarar cuál se usa, porque a escala de una conurbación ya no da lo mismo.

**7 · La serie de cortes no mide construcción.** Entre noviembre de 2024 y julio de 2025 la red
existente crece 441,1 km, pero de los 268 tramos que aparecen nuevos **sólo 25, con 18,6 km,
declaran ejecución de 2025 o posterior**; 201 tramos con 332,1 km son obras de 2024 o antes que no
estaban catastradas. Restar versiones consecutivas sobreestima la construcción en más de un orden
de magnitud.

**8 · Los contadores MINVU no traen serie temporal.** Publican sólo agregados: media diaria, semanal
y mensual, promedio de día hábil y de fin de semana, mínimo, máximo y ventana. **No permiten perfil
estacional ni curva horaria.** Lo que sí dan, y vale, es la razón entre día hábil y fin de semana,
que separa el contador utilitario del recreativo. La API pública de Eco-Counter exige el token de la
organización, de modo que la serie no es recuperable por ahora.

**9 · La conectividad depende del método y no se agrega.** Sumar kilómetros de dos áreas no da la
conectividad de la unión, y un tramo cortado en el borde del área deja de ser un tramo: hay que
evaluar con buffer y sin recortar. La tolerancia de unión se sensibiliza siempre; medida a escala
nacional:

| Tolerancia | Componentes | km de la mayor | % de la red |
|---:|---:|---:|---:|
| 1 m | 910 | 245,7 | 8,6 % |
| 5 m | 828 | 297,6 | 10,5 % |
| 20 m | 733 | 311,8 | 11,0 % |
| 50 m | 682 | 314,1 | 11,0 % |

Se adopta 20 m, donde la curva se aplana.

## Contraste de referencia · Gran Concepción, 12 comunas

Calculado ahora. Sirve para comprobar que una consulta nueva sobre este banco da lo mismo.

- **288 tramos catastrados**, de los cuales **152 existentes**.
- **159,9 km declarados existentes · 156,8 km medidos sobre la geometría.**
- Cartera futura: **151,0 km declarados** (diseño 83,9 · planificadas 52,7 · ejecución 14,4), que en
  geometría son **149,7 km** (83,3 · 51,8 · 14,6).
- **49 componentes conexas** a tolerancia de 20 m, de 3,20 km de largo medio; la mayor reúne
  **20,8 km, el 13,3 %** de los kilómetros del área.
- **13 contadores MINVU**, con media diaria mediana de **275,2 pasadas**.
- Censo 2024: **359.048 personas declaran modo, 8.258 en bicicleta, 2,30 %**.
- **Florida, Penco y Santa Juana tienen cero kilómetros construidos.**
- Kilómetros existentes por comuna: Concepción 53,1 · San Pedro de la Paz 37,7 · Hualpén 19,7 ·
  Talcahuano 15,2 · Chiguayante 13,1 · Coronel 10,2 · Tomé 6,4 · Hualqui 4,2 · **Lota 0,2**.

## Qué falta

- **89 comunas sin ningún tramo catastrado.** No está establecido si es que no tienen
  infraestructura o si no han sido catastradas; el banco no permite distinguirlo.
- **El pico de 2017 (714,9 km, el 25,3 % de la red) no está confirmado con SECTRA.** Puede ser el
  cierre de una cartera grande o el año asignado por defecto a tramos de fecha desconocida.
- **La comuna 12104 (San Gregorio) no tiene contraparte censal** y se pierde en todo cruce.
- **La serie de los contadores no es recuperable** con las fuentes públicas actuales.
- **`CICLOVIA_LOCAL_CAPA2` sigue sin interpretar.** Falta confirmar con SECTRA qué es.
- Cobertura de las capas derivadas: `manzana_cobertura` cubre 197.168 manzanas de las 221 comunas con
  red y resuelve NSE en el 96,8 %; `zona_demanda` tiene NSE en 4.561 de sus 4.577 zonas y viajes EOD
  sólo en 3.030, porque la EOD cubre 15 conurbaciones y no el país.
- De las 18 ciudades con EOD, **15 permiten reconstruir la bicicleta y sólo 8 tienen un índice
  oficial utilizable** contra el cual contrastarla.

## Qué cambió respecto de la versión anterior

La ficha anterior fue escrita mirando este banco desde fuera. Contrastadas sus cifras una a una:

**Se confirma, y es lo que da confianza al banco entero.** Los 156,8 km construidos del Gran
Concepción reproducen exactamente mi medición geométrica, y su cartera de 149,7 km coincide dígito a
dígito con la suma geométrica de las tres etapas (83,3 + 51,8 + 14,6). Los 13 contadores, las tres
comunas con cero kilómetros —Florida, Penco y Santa Juana—, los cuatro valores de `ETAPA` con sus
conteos nacionales, la ausencia de serie en los contadores y el carácter comunal del índice de
ciclo-inclusión: todo se reproduce.

**Discrepa, y queda declarado sin resolver.** La ficha anterior reporta **77 componentes conexas** en
el Gran Concepción, de 2,04 km de promedio, con un itinerario mayor de 16,2 km equivalente al 10,3 %
de la red. Mi medición da **49 componentes**, de 3,20 km de promedio, con la mayor en 20,8 km y
13,3 %. La diferencia es de método —aquella nodifica con `unary_union`, ésta une geometrías que
quedan a menos de 20 m— y ninguna de las dos es incorrecta: la primera es más estricta y la segunda
más permisiva. **Las dos cifras se conservan**; antes de citar una hay que decir con qué criterio se
obtuvo. La ficha anterior tampoco reporta los 75 vacíos de menos de 300 m, que este banco no tiene
calculados.

**Lo que la ficha anterior no sabía**, por no conocer el proyecto desde dentro: que el archivo
canónico para analizar es el panel normalizado y no la descarga cruda; que `cut_com` viene sin
relleno de ceros y que filtrar por él sobre el crudo devuelve cero resultados; que `CUT_REG` está
mal en cinco registros; que `s_i` es un pseudo-valor que llega al 68,9 % de un campo; que `smp`
significa senda multipropósito; que la calidad del registro varía de 34 % a 84 % entre regiones; que
la serie de cortes no mide construcción; y que el banco incorpora demanda —Censo 2024 por manzana,
15 EOD reconstruidas y 13.357 siniestros con ciclista— que la versión anterior no menciona.

## Quién la consume

- La habilidad **`diagnostica-ciclovias`**, que lee `data/analisis/` y publica la capa
  `ciclo_red_nodificada`.
- El **visor publicado** en <https://romedinag-tech.github.io/ciclovias/>, a través de
  `scripts/prepara_payload.py`.
- Los generadores `scripts/genera_catalogo.py` y `scripts/genera_analisis.py`, que producen
  `FUENTES.md` y `ANALISIS.md` leyendo el dato en el momento.

**`data/analisis/` es un contrato**: renombrar o borrar una columna rompe la habilidad de
diagnóstico sin previo aviso. Agregar columnas es seguro.
