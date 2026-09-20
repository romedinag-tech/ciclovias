# SALIDAS — Ciclovias

> Contrato de salidas autogenerado desde `_diagnostico_kit/catalogo.json`.
> No editar a mano: corre `python _diagnostico_kit/lib_diagnostico.py --regenerar`.

**Tema:** Movilidad activa: infraestructura ciclista y uso de la bicicleta  
**Cobertura:** Chile, 16 regiones; 246 comunas con tramos catastrados, 221 con red existente · Catastro 2024-09, 2024-11, 2025-07 y 2026-07; contadores 2015-12 a 2024-11; Censo 2024  
**Llave territorial:** cut_com (comuna INE, 5 digitos); manzana via MANZENT; zona censal via ID_ZONA  
**Granularidades:** comuna, manzana censal, zona censal, tramo de ciclovia, componente conexa de red, punto (contador, establecimiento)  
**Estado:** operativo (publicado en GitHub Pages) · **Privacidad:** Todo agregado (manzana, zona, comuna) o infraestructura y equipamiento publico. Sin microdato individual, sin roles ni coordenadas de personas.

## Salidas reutilizables

- **`data/parquet/catastro_panel.parquet`** (parquet · 16001 filas)
  - granularidad: tramo x corte · llave: `identifica + corte; cut_com, cut_reg`
  - indicadores: km, km_geom, etapa, existente, tipo, carac_func, emplaza_txt, year_ejecucion, cartera, bip_pmu
  - TABLA CLAVE: los cuatro cortes del catastro nacional con campos homogeneizados y CUT_COM normalizado a 5 digitos. OJO: filtrar etapa=='existentes' para hablar de red construida (2.827,7 km de 7.064,1 km catastrados).
- **`data/analisis/manzana_cobertura.parquet`** (parquet · 197168 filas)
  - granularidad: manzana censal · llave: `MANZENT; cut_com; zona (ID_ZONA)`
  - indicadores: dist_existente_m, dist_total_m, cub_150/300/500/694/1000, n_per, n_transporte_bicicleta, nse_score, prom_escolaridad18
  - TABLA CLAVE reutilizable: distancia de cada manzana del pais con red al tramo de ciclovia mas cercano, mas el perfil censal y el NSE de su zona. Sirve para cualquier analisis de cobertura a cualquier umbral.
- **`data/analisis/cobertura_comuna.parquet`** (parquet · 221 filas)
  - granularidad: comuna · llave: `cut_com`
  - indicadores: pob, bici, pct_pob_300, pct_bici_300, nse_score_pob
  - Cobertura poblacional agregada por comuna.
- **`data/analisis/conectividad_comuna.parquet`** (parquet · 222 filas)
  - granularidad: comuna · llave: `cut_com`
  - indicadores: n_componentes, km_componente_mayor, pct_km_componente_mayor
  - Fragmentacion de la red: componentes conexas a tolerancia de 20 m.
- **`data/analisis/equipamiento_cobertura.parquet`** (parquet · 12576 filas)
  - granularidad: establecimiento educacional · llave: `id (RBD o COD_INST); cut_com`
  - indicadores: clase, matricula, dist_existente_m, dist_total_m
  - Colegios (MINEDUC) y sedes de educacion superior con su distancia a la red.
- **`data/parquet/minvu_contadores.parquet`** (parquet · 185 filas)
  - granularidad: punto (contador) · llave: `ID_CONTADOR; CUT_COM`
  - indicadores: Media_diaria, Media_semanal, Media_Mensual, Promedio_dia_de_semana, Promedio_fin_de_semana, Max_diaria
  - Unica serie de FLUJO CICLISTA observado del pais. OJO: el campo COMUNA trae el codigo CUT, no el nombre.
- **`index.html`** (html · - filas)
  - granularidad: comuna / tramo / punto · llave: `cut_com`
  - indicadores: cobertura 300 m, km por etapa, fragmentacion, brecha NSE
  - Visor autocontenido publicado en https://romedinag-tech.github.io/ciclovias/
- **`data/analisis/conectividad_sensibilidad.parquet`** (parquet · 6 filas)
  - granularidad: tolerancia de unión · llave: `tolerancia_m`
  - indicadores: tolerancia_m, n_componentes, km_componente_mayor
  - Sensibilidad de la fragmentación a la tolerancia de unión. Se consulta ANTES de citar cualquier cifra de conectividad.
- **`data/analisis/componentes.parquet`** (parquet · 733 filas)
  - granularidad: componente conexa de red · llave: `componente`
  - indicadores: km, n_tramos, comunas, comuna_principal
  - Cada fragmento continuo de la red existente, con su kilometraje y cuántas comunas cruza.
- **`data/analisis/tramo_componente.parquet`** (parquet · 1971 filas)
  - granularidad: tramo · llave: `identifica; componente; cut_com`
  - indicadores: componente, km
  - A qué componente pertenece cada tramo. Necesario para contar componentes en un recorte SIN sobrecontar las que cruzan límites.
- **`data/analisis/zona_demanda.parquet`** (parquet · 4577 filas)
  - granularidad: zona censal · llave: `zona (CUT+distrito+zona)`
  - indicadores: pob, bici, bici_pct, cob_pct, dist_m, nse_score, sin_bici, eod_bici_gen, eod_bici_atr, eod_n_gen, eod_n_atr
  - Zona censal con demanda, cobertura, NSE, siniestros y viajes EOD, cada uno con su respaldo muestral. Es la unidad del mapa del visor.
- **`data/analisis/demanda_comuna.parquet`** (parquet · 334 filas)
  - granularidad: comuna · llave: `cut_com`
  - indicadores: n_transporte_bicicleta, viajes_modo, bici_pct
  - Personas que declaran la bicicleta como modo principal al trabajo o al estudio (Censo 2024).
- **`data/analisis/siniestros_bici.parquet`** (parquet · 13357 filas)
  - granularidad: punto (siniestro) · llave: `id_accidente; cut_com`
  - indicadores: anio, lat, lon, fallecidos, graves, tipo_final, causa_final
  - Siniestros con participación de bicicleta georreferenciados, 2020-2024 (CONASET).
- **`data/analisis/demanda_eod_ciudad.parquet`** (parquet · 18 filas)
  - granularidad: ciudad-año EOD · llave: `ciudad + anio`
  - indicadores: bici_pct, caminata_exp, n_registros_bici, indice_consistente
  - Reconstrucción validada de la bicicleta en cada EOD, separándola del grupo no motorizado.
- **`data/analisis/demanda_eod_perfil.parquet`** (parquet · 402 filas)
  - granularidad: ciudad x dimensión · llave: `ciudad + dim + valor`
  - indicadores: viajes
  - Viajes en bicicleta por propósito, período y hora.
- **`data/analisis/demanda_eod_zona.parquet`** (parquet · 3639 filas)
  - granularidad: zona EOD · llave: `ciudad + zona + lado`
  - indicadores: viajes, n
  - Viajes en bicicleta por zona EOD, con el número de viajes ENCUESTADOS detrás.
- **`data/analisis/eod_cruces.parquet`** (parquet · 1552 filas)
  - granularidad: ciudad x dimensión · llave: `ciudad + dim + valor`
  - indicadores: bici, total, part
  - Participación de la bicicleta por sexo, edad, quintil, propósito, período y hora x propósito.
- **`data/analisis/eod_distancias.parquet`** (parquet · 297 filas)
  - granularidad: ciudad x modo x tramo · llave: `ciudad + modo + tramo`
  - indicadores: pct, acum
  - Distribución de distancias del viaje, bicicleta contra todos los modos.
- **`data/analisis/eod_distancias_resumen.parquet`** (parquet · 33 filas)
  - granularidad: ciudad x modo · llave: `ciudad + modo`
  - indicadores: dist_media_km, dist_mediana_km
  - Media y mediana de distancia sin binear.
- **`data/analisis/eod_kpi.parquet`** (parquet · 18 filas)
  - granularidad: ciudad-año EOD · llave: `ciudad`
  - indicadores: viajes, viajes_persona, pct_publico, pct_privado, cam_pct_propio, bici_pct_propio, tiempo_med_bici_min, dist_media_bici_km
  - KPI por ciudad. La caminata y la bicicleta son reconstrucción propia: los campos del índice arrastran un defecto de homologación.

## Consulta de ejemplo

```
import pandas as pd; m = pd.read_parquet('Ciclovias/data/analisis/manzana_cobertura.parquet'); m.groupby('cut_com').apply(lambda d: 100*d.loc[d.dist_existente_m<=300,'n_per'].sum()/d.n_per.sum())
```

## Trampas (no tropezar)

- El catastro cubre TODO el ciclo de vida: de 7.064,1 km solo 2.827,7 estan en etapa existentes. Usar el total infla la red al doble.
- La serie de cortes NO mide construccion: de los 441,1 km que crece la red entre 2024-11 y 2025-07, solo 18,6 km declaran ejecucion 2025 o posterior; el resto es mejora de catastro. La construccion anual se lee de year_ejecucion dentro de un corte.
- CUT_COM viene sin relleno de ceros en las regiones 1 a 9 (2.496 de 4.850 registros del corte vigente): aplicar zfill(5) antes de cruzar.
- CUT_REG contradice a la comuna en 29 registros del panel: derivar la region de los dos primeros digitos del CUT_COM.
- minvu_contadores.COMUNA trae el codigo CUT, no el nombre de la comuna.
- La conectividad se mide uniendo geometrias, no extremos: el 11,9% de los extremos cae sobre el interior de otro tramo (empalmes en T) y un grafo por extremos sobreestima la fragmentacion (56,4 km contra 311,8 km en la componente mayor).

## Como regenerar

`cd Ciclovias && python -X utf8 scripts/descarga_arcgis.py && python -X utf8 scripts/normaliza.py && python -X utf8 scripts/analisis_cobertura.py && python -X utf8 scripts/analisis_conectividad.py && python -X utf8 scripts/analisis_demanda.py && python -X utf8 scripts/analisis_eod_cruces.py && python -X utf8 scripts/analisis_eod_distancias.py && python -X utf8 scripts/analisis_eod_kpi.py && python -X utf8 scripts/analisis_zonas.py && python -X utf8 scripts/cruza_eod_zonas_censales.py && python -X utf8 scripts/genera_catalogo.py && python -X utf8 scripts/genera_analisis.py && python -X utf8 scripts/prepara_payload.py && python -X utf8 scripts/genera_visor.py`

## Docs clave

`Ciclovias/CLAUDE.md`, `Ciclovias/FUENTES.md`, `Ciclovias/ANALISIS.md`, `Ciclovias/docs/fuentes/minvu_2018_analisis_contadores.pdf`
