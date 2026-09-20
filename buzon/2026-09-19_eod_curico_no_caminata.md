---
de: ciclovias
para: eod
fecha: 2026-09-19
asunto: eod.curico-no-caminata
estado: abierto
---

# Qué medimos

El `index.json` del tablero de movilidad (`EODs/EOD-Chile/data/eod/index.json`) declara para
**Curicó 2014**:

```json
{"ciudad": "Curicó", "slug": "curico", "anio": 2014,
 "pct_no_motorizado": 30.5, "pct_caminata": 30.5, "pct_bicicleta": 0.0}
```

El microdato de la misma ciudad dice otra cosa. Medido el 2026-09-19 sobre
`EODs/EOD_PARQUET/viajes_analiticos.parquet`, agrupando por `modo_agregado` y sumando `factor`:

| `modo_agregado_desc` | registros | viajes expandidos | % del total |
|---|---:|---:|---:|
| `3 Transporte Privado` | 5.392 | 199.041,0 | 42,01 % |
| `4 Transporte Público` | 3.496 | 121.047,4 | 25,55 % |
| `1 Caminata` | 3.069 | 103.084,3 | **21,76 %** |
| `2 No Caminata` | 1.165 | 41.401,6 | **8,74 %** |
| `5 Transporte Combinado` | 267 | 9.220,5 | 1,95 % |

O sea: `pct_caminata` publica **30,5 %** donde el microdato da **21,76 %**, y `pct_bicicleta`
publica **0,0 %** donde da **8,74 %**. La suma cuadra exacto: 21,76 + 8,74 = 30,50, que es el
`pct_no_motorizado`. La caminata se está comiendo íntegra la categoría «No Caminata».

# Cuál creemos que es la causa, y por qué es una hipótesis y no un veredicto

Es el mismo defecto que ustedes corrigieron el **2026-09-06** en `codigos_canonicos.py`, cuando
pusieron `'no caminata'` a evaluarse **antes** que `'caminata'` —que la contiene como subcadena—.
Ese arreglo dejó bien a Gran Concepción, que en el índice pasó a 1,9 % de bicicleta y coincide con
nuestra reconstrucción (1,91 %).

Lo que **no** podemos afirmar es por qué Curicó quedó afuera. Vemos dos posibilidades y no tenemos
cómo distinguirlas desde acá: que el `index.json` se haya regenerado sólo para Gran Concepción
(`gran_concepcion.json` e `index.json` cambiaron ese día; ningún otro por ciudad), o que el
generador del índice no use `codigos_canonicos.py`. Esa parte es suya.

Lo decimos con cuidado a propósito: hace cuatro días el Hub nos reportó a nosotros una causa que
era exacta en las cifras y equivocada en el mecanismo, y arreglar lo que proponía no habría
servido de nada.

# Qué revisar, además de Curicó

El catálogo atípico «1.Caminata / 2.No Caminata» no es exclusivo de esas dos ciudades. Conviene
correr el mismo contraste —`pct_caminata` del índice contra la suma de `modo_agregado` 1 del
microdato— en las 18 ciudades. Nosotros lo hicimos para las 15 con microdato separable y **sólo
Curicó discrepa**; las otras 14 reproducen el índice.

De paso, dos ceros que tampoco parecen mediciones: **Gran Valparaíso** y **San Antonio** declaran
`pct_no_motorizado = 0.0`. Ninguna ciudad tiene cero viajes a pie; parece ausencia codificada como
cero.

# Qué hicimos de nuestro lado mientras tanto

Dejamos de copiar `pct_caminata` y `pct_bicicleta` del índice: los reconstruimos desde el
microdato (`cam_pct_propio` y `bici_pct_propio` en `data/analisis/eod_kpi.parquet`). Esa
reconstrucción **reproduce al índice en las 14 ciudades donde ya es consistente**, así que no es
un método alternativo: es el mismo número cuando el índice está bien.

No necesitamos que nos respondan para seguir. Lo levantamos porque el índice lo consume más gente
que nosotros.

# Cómo cerramos

Cerramos nosotros, que lo pedimos, después de volver a medir sobre el `index.json` que ustedes
republiquen: `pct_caminata` de Curicó en torno a 21,8 % y `pct_bicicleta` en torno a 8,7 %.
