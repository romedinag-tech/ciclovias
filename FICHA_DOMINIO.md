# Ficha de dominio · CICLOVÍAS

> Qué hay en este banco y cómo se usa, para no tener que volver a analizarlo cada vez.
> Cifras **medidas sobre los archivos**, no recordadas. Medido el 4-09-2026.

## Cuál es el archivo canónico

**`data/parquet/sectra_ciclovias_nac_2026_07.parquet`** — 4.850 tramos, catastro nacional de SECTRA,
corte julio 2026. Es la capa que alimenta el Visor de Ciclovías de Chile.

Las versiones `2024_09`, `2024_11`, `2025_07` y `local_capa2` se conservan como historial y **no son
vigentes**.

## Llave, grano y geometría

- **Llave `CUT_COM`** (código INE de comuna). Grano atómico: el arco.
- **Es un dominio de grafo.** Se evalúa **con buffer y sin recortar**: un arco cortado en el borde
  del área deja de ser un arco, y la conectividad calculada sobre una red recortada es un artefacto
  del recorte.
- **La conectividad no se agrega.** Sumar kilómetros de dos áreas no da la conectividad de la unión.

## El campo que resuelve la pregunta que todos hacen

**`ETAPA`** separa lo construido de lo proyectado, con cuatro valores en todo el país:
`existentes` (1.971 tramos) · `diseño` (1.362) · `planificadas` (1.310) · `ejecución` (207).

Eso hace innecesario buscar el documento del Plan Maestro para distinguir red construida de cartera.

## Las otras capas

| Capa | Qué aporta |
|---|---|
| `sectra_icc_comunas` | Índice de ciclo-inclusión de las 346 comunas, con km de red vial y de ciclovía, población y equipamiento cubiertos a 300 m, e índices normalizados |
| `sectra_icc_comunas_planes` | El mismo índice **incorporando la cartera planificada**: permite responder cuánto mejoraría cada comuna si se ejecutara |
| `sectra_icc_red_ciclov` | La red que usa el índice: 1.831 tramos |
| `minvu_contadores` | 185 contadores automáticos de flujo ciclista |
| `minvu_ciclovias_medida_presidencial` · `_otras_medidas` | Red MINVU |
| `sectra_mediciones_antofagasta_talca` | 128 puntos de conteo, **solo Antofagasta y Talca** |

## Trampas medidas

**Los contadores del MINVU no traen serie temporal.** Entregan estadísticas agregadas: media diaria,
semanal y mensual, promedio de día hábil y de fin de semana, mínimo, máximo y ventana de observación.
**No permiten un perfil estacional mes a mes.** Lo que sí dan, y vale, es la **razón entre día hábil
y fin de semana**, que separa el contador de viaje utilitario del de uso recreativo. La ventana
termina en noviembre de 2024 en la mayoría de los puntos.

**El índice de ciclo-inclusión está calculado sobre la comuna completa.** No sirve para un área
menor: para un polígono hay que re-aplicar la receta, no tomar el valor publicado.

**La conectividad se mide sobre la red nodificada.** Unir tramos solo por sus extremos deja
desconectadas dos ciclovías que se cruzan a media cuadra y **exagera la fragmentación**: en el Gran
Concepción daba 103 componentes en vez de 77. Hay que aplicar `unary_union` antes de construir el
grafo.

**La tolerancia de unión se declara y se sensibiliza.** Un digitalizado con milímetros de separación
inventa cortes. Reportar el resultado para tres tolerancias: si sobrevive a 5, 10 y 25 m, no depende
del umbral.

**El atributo `KM` no coincide exactamente con la geometría.** En el Gran Concepción declara 159,9 km
y la medición sobre la línea da 156,8. Medir sobre la geometría y declarar cuál se usa.

## Contraste de referencia · Gran Concepción, 12 comunas

156,8 km construidos · 149,7 km en cartera (83,3 diseño + 51,8 planificadas + 14,6 ejecución) ·
**77 componentes conexos** de 2,04 km de promedio · itinerario continuo mayor de 16,2 km, el 10,3 %
de la red · **75 vacíos de menos de 300 m** que suman 5,07 km de obra y llevarían el itinerario mayor
a 67,7 km · 13 contadores MINVU · Florida, Penco y Santa Juana con **cero** kilómetros construidos.

Sirve para comprobar que una consulta nueva sobre este banco da lo mismo.

## Quién la consume

La habilidad `diagnostica-ciclovias` (`~/.claude/skills/`), que publica la capa canónica
`ciclo_red_nodificada`: la red partida en sus intersecciones reales, con el componente conexo al que
pertenece cada segmento. Es lo que permite preguntar si dos puntos están conectados sin volver a
abrir este banco.
