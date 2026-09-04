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
- **`data/analisis/conectividad_comuna.parquet`** (parquet · 221 filas)
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

`cd Ciclovias && python -X utf8 scripts/descarga_arcgis.py && python -X utf8 scripts/normaliza.py && python -X utf8 scripts/analisis_cobertura.py && python -X utf8 scripts/analisis_conectividad.py && python -X utf8 scripts/genera_catalogo.py && python -X utf8 scripts/genera_analisis.py && python -X utf8 scripts/genera_visor.py`

## Docs clave

`Ciclovias/CLAUDE.md`, `Ciclovias/FUENTES.md`, `Ciclovias/ANALISIS.md`, `Ciclovias/docs/fuentes/minvu_2018_analisis_contadores.pdf`
