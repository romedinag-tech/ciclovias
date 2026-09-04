# Hallazgos — red de ciclovías, población y territorio

> Archivo **generado**. No editar a mano: correr
> `python -X utf8 scripts/genera_analisis.py`.

Todas las cifras salen de leer `data/analisis/` y `data/parquet/` en el momento de generar el documento.

## 1. Qué red se está midiendo

El catastro nacional vigente (corte 2026-07) tiene **4.850 tramos y 7.064,1 km**, pero sólo **1.971 tramos y 2.827,7 km están en etapa `existentes`**. Todo lo que sigue mide la red construida; la cartera en diseño y planificada se usa sólo como escenario de comparación.

| Etapa | km | tramos |
|---|---:|---:|
| existentes | 2.827,7 | 1.971 |
| diseño | 2.026,7 | 1.362 |
| planificadas | 1.861,8 | 1.310 |
| ejecución | 347,9 | 207 |

## 2. A quién alcanza la red

El universo son las **221 comunas que tienen al menos un tramo existente**, con 15.255.898 habitantes. De ellos, 213.106 personas declaran en el Censo 2024 la bicicleta como modo principal de transporte al trabajo o al estudio.

En vez de fijar un radio, se midió para cada manzana censal la distancia al tramo existente más cercano, de modo que la cobertura pueda leerse a cualquier umbral. Los dos umbrales con respaldo institucional son los 300 m que usa el propio índice de ciclo-inclusión de SECTRA y los 694 m que el estudio MINVU 2018 midió por la red vial.

| Umbral | Población cubierta | % | Ciclistas cubiertos | % |
|---:|---:|---:|---:|---:|
| 150 m | 2.755.076 | 18,1 % | 49.809 | 23,4 % |
| 300 m | 5.418.932 | 35,5 % | 91.697 | 43,0 % |
| 500 m | 7.908.052 | 51,8 % | 127.988 | 60,1 % |
| 694 m | 9.589.749 | 62,9 % | 149.062 | 69,9 % |
| 1.000 m | 11.366.084 | 74,5 % | 171.184 | 80,3 % |

La red está mejor alineada con la demanda que con la población en general: a 300 m vive el **35,5 %** de la población pero el **43,0 %** de quienes ya andan en bicicleta. La dirección de esa relación no puede establecerse con este dato: la ciclovía puede haber atraído a los ciclistas o haberse construido donde ya pedaleaban.

## 3. La cobertura es socialmente regresiva

Sobre las 145.473 manzanas urbanas con nivel socioeconómico resuelto, la cobertura sube de forma monótona con el NSE mientras el uso de la bicicleta baja. Es decir, **la infraestructura está donde menos se pedalea**.

| Quintil de NSE | Población | Cubierta a 300 m | Bicicleta como modo |
|---|---:|---:|---:|
| Q1 (más bajo) | 2.710.467 | 30,3 % | 4,6 % |
| Q2 | 2.723.131 | 31,3 % | 3,9 % |
| Q3 | 2.789.661 | 33,5 % | 4,0 % |
| Q4 | 2.776.686 | 35,9 % | 3,3 % |
| Q5 (más alto) | 3.931.824 | 45,1 % | 3,0 % |

La brecha entre el quintil más bajo y el más alto es de **14,8 puntos porcentuales** de cobertura, mientras el uso de la bicicleta corre en sentido contrario: 4,6 % en el quintil bajo contra 3,0 % en el alto.

**El resultado no es un artefacto de qué comunas tienen red.** Una objeción razonable es que las comunas de mayor ingreso simplemente tengan más kilómetros, y que el gradiente sea eso y no una desigualdad interna. Para descartarlo se recalculó el quintil de NSE **dentro de cada comuna**, sobre las 160 comunas con suficiente variación interna. El gradiente se atenúa pero no desaparece: la cobertura pasa de **32,5 %** en el quintil más bajo de la comuna a **41,8 %** en el más alto, **9,3 puntos** de diferencia entre vecinos de un mismo municipio.

## 4. La red sirve a la universidad, no al colegio

| Tipo | Establecimientos | < 300 m | < 694 m | < 1.000 m |
|---|---:|---:|---:|---:|
| Escolares | 9.336 | 32 % | 55 % | 64 % |
| Educación superior | 1.282 | 69 % | 85 % | 90 % |

La diferencia es grande y va en la dirección menos deseable. Dentro de las mismas comunas, **69 % de las sedes de educación superior** tiene una ciclovía a menos de 300 m, contra apenas **32 % de los establecimientos escolares**. La red acompaña la geografía del centro urbano y de los campus, no la de los colegios, que es donde se distribuye la población en edad escolar. Si el objetivo declarado incluye el viaje al estudio, ese es el déficit más nítido que muestran estos datos.

Ponderando por matrícula, los 9.336 establecimientos escolares con matrícula declarada suman 3.346.229 estudiantes, de los cuales **1.361.889 (41 %)** estudian a menos de 300 m de una ciclovía.

## 5. Kilómetros no son red: la fragmentación

Un indicador de kilometraje no distingue entre una red que permite cruzar la ciudad y un conjunto de tramos sueltos. Para separarlos se construyó el grafo de la red existente uniendo tramos cuyas geometrías quedan a menos de una tolerancia, y se contaron las componentes conexas.

La tolerancia importa, así que se recorrió un rango en vez de fijarla:

| Tolerancia | Componentes | km de la mayor | % de la red | % componentes de un solo tramo |
|---:|---:|---:|---:|---:|
| 1 m | 910 | 245,7 | 8,6 % | 72,5 % |
| 5 m | 828 | 297,6 | 10,5 % | 69,1 % |
| 10 m | 786 | 297,6 | 10,5 % | 66,9 % |
| 20 m | 733 | 311,8 | 11,0 % | 65,2 % |
| 35 m | 701 | 312,6 | 11,0 % | 65,5 % |
| 50 m | 682 | 314,1 | 11,0 % | 64,7 % |

Se adopta **20 m**, que es donde la curva se aplana: pasar de 20 a 50 m apenas mueve la componente mayor, de modo que lo que queda separado a 20 m lo está por distancia real y no por imprecisión del trazado.

A esa tolerancia la red existente se parte en **733 componentes**. La mayor reúne 311,8 km, apenas el **11,0 % de la red**, y la mitad de las componentes no pasa de **1,26 km** — menos que la distancia de un viaje urbano corriente. El **65 %** de las componentes es un tramo único que no empalma con nada.

Conviene subrayar que esto es una **cota inferior de la fragmentación**: el grafo une dos ciclovías que se cruzan aunque el cruce no esté habilitado para el viraje, de modo que la red real está al menos tan partida como aquí se reporta.

Las doce comunas con más kilómetros, y qué tan integrada está esa red:

| Comuna | km | Componentes | km de la mayor | % en la mayor |
|---|---:|---:|---:|---:|
| Temuco | 75,6 | 5 | 58,2 | 77 % |
| Rancagua | 73,8 | 25 | 52,1 | 71 % |
| Talca | 73,7 | 24 | 32,1 | 44 % |
| Puerto Varas | 69,0 | 3 | 66,1 | 96 % |
| Santiago | 61,5 | 3 | 58,8 | 96 % |
| Los Ángeles | 61,5 | 9 | 28,5 | 46 % |
| Paine | 61,2 | 7 | 25,2 | 41 % |
| Valdivia | 57,6 | 12 | 19,1 | 33 % |
| Las Condes | 56,2 | 8 | 40,2 | 72 % |
| Río Bueno | 55,0 | 5 | 37,6 | 68 % |
| Concepción | 51,2 | 11 | 20,8 | 41 % |
| Puerto Montt | 46,1 | 15 | 16,0 | 35 % |

La lectura no es que unas comunas estén bien y otras mal, sino que **el kilometraje y la integración son dos cosas distintas**: hay comunas con red comparable donde una concentra casi todo en un solo eje continuo y otra reparte lo mismo en decenas de fragmentos.

## 6. Qué NO se puede afirmar con esto

- **No hay causalidad.** La asociación entre cercanía a la ciclovía y uso de la bicicleta admite las dos direcciones, y este dato no permite separarlas. Todo lo anterior son asociaciones observadas.

- **La cobertura es euclidiana, no de red.** La distancia se mide en línea recta desde el centroide de la manzana, no caminando o pedaleando por la vialidad. En trama urbana regular el sesgo es modesto, pero donde hay barreras —un río, una línea férrea, una autopista— la cercanía aparente sobrestima el acceso real.

- **El NSE es del territorio, no de la persona.** Es un índice de área pequeña por zona censal; atribuirlo a un individuo sería una falacia ecológica.

- **El modo de transporte del Censo es el principal**, declarado al trabajo o al estudio, no el total de viajes. No es comparable sin más con la partición modal de una encuesta origen–destino.
