# Benchmark metodológico — Análisis de contadores de ciclovías, MINVU 2018

Extraído de `docs/fuentes/minvu_2018_analisis_contadores.pdf`. Se mantiene fuera
del `CLAUDE.md` por presupuesto de tamaño; desde allí se referencia este archivo.

Es un análisis **descriptivo** sobre 48 ejes en 23 sistemas y 19 ciudades con más
de 9 meses de contador. Sus cifras son la referencia contra la cual validar
cálculos propios sobre los contadores. Área de influencia usada: **694 m medidos
por la red vial**.

## Efectos reportados sobre pasadas promedio diarias

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

## Dos advertencias que hay que arrastrar al citar estas cifras

La relación con equipamientos que el propio informe reporta —`y = 0,5957x +
175,1`, es decir +5,9 pasadas por cada 10 equipamientos— tiene **R² = 0,096**:
explica menos del 10 % de la varianza y no sostiene una afirmación causal ni
predictiva.

El informe declara explícitamente que los resultados son descriptivos y no
permiten inferir causalidad. El signo negativo de la iluminación es el caso que
más claramente delata variable omitida —probablemente ciclovías nuevas y mejor
iluminadas en ejes de menor demanda—. Citar estos números como correlaciones
observadas, nunca como elasticidades de diseño.

## Contexto de partición modal

ECVU 2015, citada en el mismo informe: **3,2 %** de los desplazamientos al
trabajo en bicicleta, y **49 %** de la población de ciudades sobre 20.000
habitantes considera que no hay ciclovías en su comuna o que son de mala calidad
(sube a **63 %** en ciudades intermedias menores).

Ese 3,2 % coincide con lo que arroja el Censo 2024 para Concepción, calculado de
forma independiente en este proyecto. Es una validación cruzada útil, no una
cifra a citar dos veces como si fueran dos fuentes.
