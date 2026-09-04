# Catálogo de fuentes — banco de datos de movilidad activa

> Archivo **generado**. No editar a mano: correr
> `python -X utf8 scripts/genera_catalogo.py`.

Descarga registrada en `data/MANIFIESTO.json` (2026-09-04T15:18:20+00:00 UTC).

**17 capas · 63.925 registros · 39.7 MB en Parquet**

## Verificación de integridad

Todas las capas cuadran: el número de registros descargados coincide con el `count` declarado por cada servicio, no hay registros sin geometría y todas las extensiones caen dentro de Chile.

## A. Catastro Nacional de Ciclovías (SECTRA / MTT)

### `sectra_ciclovias_nac_2026_07`

**Catastro Nacional de Ciclovias - CICLOVIA_jul2026**  
SECTRA / Programa de Vialidad y Transporte Urbano - MTT · vigente · corte declarado 2026-07  
4.850 registros · Polyline · 4.093 MB

Capa que alimenta el 'Visor de Ciclovias Chile'. Version mas reciente.

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/CICLOV_validVisor_WFL1/FeatureServer/0`
- Capa de origen: `CICLOVIA_jul2026`
- Archivo: `data/parquet/sectra_ciclovias_nac_2026_07.parquet`
- Campos: `OBJECTID`, `IDENTIFICA`, `REGIÓN`, `COMUNA`, `EJE_VIA`, `INICIO`, `FIN`, `KM`, `TIPO`, `CARAC_FUNC`, `EMPLAZA_TEX`, `EMPLAZA_N`, `URBANA`, `ETAPA`, `Etapa_det`, `CARTERA`, `BIP_o_PMU`, `NOMBRE_PROYECTO_BIP_o_PMU`, `NORMATIVA`, `RESOLUCION`, `COMENTARIO`, `CUT_REG`, `CUT_COM`, `YEAR_EJECUCION`, `FUENTE_ACTUALIZA`, `Shape__Length`

### `sectra_ciclovias_nac_local_capa2`

**Catastro Nacional de Ciclovias - CICLOVIA_LOCAL_CAPA2**  
SECTRA / Programa de Vialidad y Transporte Urbano - MTT · histórica / no vigente  
4.409 registros · Polyline · 4.075 MB

Segunda capa del mismo servicio, con menos registros que la capa 0. Se conserva sin interpretar: falta confirmar con SECTRA si es un respaldo previo o un subconjunto editable.

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/CICLOV_validVisor_WFL1/FeatureServer/1`
- Capa de origen: `CICLOVIA_LOCAL_CAPA2`
- Archivo: `data/parquet/sectra_ciclovias_nac_local_capa2.parquet`
- Campos: `OBJECTID`, `IDENTIFICA`, `REGION`, `COMUNA`, `EJE_VIA`, `INICIO`, `FIN`, `KM`, `TIPO`, `CARAC_FUNC`, `EMPLAZA_TE`, `EMPLAZA_N`, `URBANA`, `ETAPA`, `ETAPA_DET`, `CARTERA`, `BIP_o_PMU`, `NOMBRE_PRO`, `NORMATIVA`, `RESOLUCION`, `CUT_REG`, `CUT_COM`, `YEAR_EJECU`, `FUENTE_ACT`, `Shape_Leng`, `Shape__Length`

### `sectra_ciclovias_nac_2024_09`

**Catastro Nacional de Ciclovias - CICLOVnac_160924**  
SECTRA / MTT · histórica / no vigente · corte declarado 2024-09  
3.423 registros · Polyline · 1.42 MB

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/CICLOVnac_sep24_WFL1/FeatureServer/27`
- Capa de origen: `CICLOVnac_160924`
- Archivo: `data/parquet/sectra_ciclovias_nac_2024_09.parquet`
- Campos: `OBJECTID`, `IDENTIFICA`, `REGION`, `COMUNA`, `EJE_VIA`, `INICIO`, `FIN`, `KM`, `TIPO`, `CARAC_FUNC`, `EMPLAZA_TEX`, `EMPLAZA_N`, `URBANA`, `ETAPA`, `ETAPA_DET`, `CARTERA`, `BIP_PMU`, `NOM_PROYECTO`, `NORMATIVA`, `RESOLUCION`, `COMENTARIO`, `CUT_REG`, `CUT_COM`, `FECHA_EJECUCION`, `FUENTE_UPDATE`, `KM_SUM`, `Shape__Length`

### `sectra_ciclovias_nac_2024_11`

**Catastro Nacional de Ciclovias - CICLOVnac_07112024**  
SECTRA / MTT · histórica / no vigente · corte declarado 2024-11  
3.511 registros · Polyline · 1.434 MB

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/CICLOVnac_07112024/FeatureServer/0`
- Capa de origen: `CICLOVnac_07112024regpm`
- Archivo: `data/parquet/sectra_ciclovias_nac_2024_11.parquet`
- Campos: `OBJECTID`, `IDENTIFICA`, `REGION`, `COMUNA`, `EJE_VIA`, `INICIO`, `FIN`, `ETAPA`, `TIPO`, `CARAC_FUNC`, `EMPLAZA_TEX`, `BIP_PMU`, `NOM_PROYECTO`, `NORMATIVA`, `RESOLUCION`, `COMENTARIO`, `CARTERA`, `KM`, `CUT_REG`, `CUT_COM`, `URBANA`, `EMPLAZA_N`, `ETAPA_DET`, `FUENTE_UPDATE`, `KM_SUM`, `FECHA_EJE_tex`, `Shape__Length`

### `sectra_ciclovias_nac_2025_07`

**Catastro Nacional de Ciclovias - CICLOVnac_jul25**  
SECTRA / MTT · histórica / no vigente · corte declarado 2025-07  
4.217 registros · Polyline · 4.195 MB

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/ICC1_planes_WFL1/FeatureServer/1`
- Capa de origen: `CICLOVnac_jul25`
- Archivo: `data/parquet/sectra_ciclovias_nac_2025_07.parquet`
- Campos: `FID`, `IDENTIFICA`, `REGION`, `COMUNA`, `EJE_VIA`, `INICIO`, `FIN`, `KM`, `TIPO`, `CARAC_FUNC`, `EMPLAZA_TE`, `EMPLAZA_N`, `URBANA`, `ETAPA`, `ETAPA_DET`, `CARTERA`, `BIP_o_PMU`, `NOMBRE_PRO`, `NORMATIVA`, `RESOLUCION`, `CUT_REG`, `CUT_COM`, `YEAR_EJECU`, `FUENTE_ACT`, `Shape_Leng`, `Shape__Length`

## B. Índice de ciclo-inclusión comunal — ICC (SECTRA / MTT)

### `sectra_icc_comunas`

**Indicadores de ciclo-inclusion por comuna (universo nacional)**  
SECTRA / MTT · vigente  
346 registros · Polygon · 0.085 MB

346 comunas con km de red vial, km de ciclovia, nodos, poblacion cubierta a 300 m, equipamientos cubiertos e indices normalizados.

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/ICC_1_WFL1/FeatureServer/4`
- Capa de origen: `comunas_con_indicadores_ICiclo`
- Archivo: `data/parquet/sectra_icc_comunas.parquet`
- Campos: `FID`, `fid_1`, `objectid`, `shape_leng`, `dis_elec`, `cir_sena`, `cod_comuna`, `codregion`, `st_area_sh`, `st_length_`, `Region`, `Comuna`, `Provincia`, `Clasificac`, `COD_REG`, `REGION_1`, `COMUNA_1`, `CLASIF`, `KM_redvial`, `Km_ciclov_`, `nodos_exis`, `POB_TOT`, `POBcob_300`, `EQ_TOTAL`, `EQUIcob_30`, `prop_red`, `conectivid`, `conectiv_1`, `cobpob_`, `cobequipa_`, `ind_red`, `ind_red_n`, `ind_cob`, `ind_cob_n`, `ind_ciclo_`, `ind_cicl_1`, `Shape__Area`, `Shape__Length`

### `sectra_icc_comunas_mixtas`

**Indicadores de ciclo-inclusion - comunas mixtas**  
SECTRA / MTT · vigente  
78 registros · Polygon · 0.038 MB

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/ICC_1_WFL1/FeatureServer/2`
- Capa de origen: `comunas_con_indicadores_ICiclo_mixta`
- Archivo: `data/parquet/sectra_icc_comunas_mixtas.parquet`
- Campos: `OBJECTID`, `fid_1`, `objectid_1`, `shape_leng`, `dis_elec`, `cir_sena`, `cod_comuna`, `codregion`, `st_area_sh`, `st_length_`, `Region`, `Comuna`, `Provincia`, `Clasificac`, `COD_REG`, `REGION_1`, `COMUNA_1`, `CLASIF`, `KM_redvial`, `Km_ciclov_`, `nodos_exis`, `POB_TOT`, `POBcob_300`, `EQ_TOTAL`, `EQUIcob_30`, `prop_red`, `conectivid`, `conectiv_1`, `cobpob_`, `cobequipa_`, `ind_red`, `ind_red_n`, `ind_cob`, `ind_cob_n`, `ind_ciclo_`, `ind_cicl_1`, `Shape__Area`, `Shape__Length`

### `sectra_icc_comunas_planes`

**Indicadores de ciclo-inclusion incorporando ciclovias planificadas**  
SECTRA / MTT · vigente  
346 registros · Polygon · 0.08 MB

Escenario con cartera planificada; se compara contra sectra_icc_comunas.

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/ICC_2_WFL1/FeatureServer/5`
- Capa de origen: `comunas_con_indicadores_ICiclo_planes`
- Archivo: `data/parquet/sectra_icc_comunas_planes.parquet`
- Campos: `OBJECTID`, `fid_1`, `objectid_1`, `shape_leng`, `dis_elec`, `cir_sena`, `cod_comuna`, `codregion`, `st_area_sh`, `st_length_`, `Region`, `Comuna`, `Provincia`, `Clasificac`, `COD_REG`, `REGION_1`, `COMUNA_1`, `CLASIF`, `KM_redvial`, `Km_ciclov_`, `nodos_exis`, `POB_TOT`, `POBcob_300`, `EQ_TOTAL`, `EQUIcob_30`, `prop_red`, `conectivid`, `conectiv_1`, `cobpob_`, `cobequipa_`, `ind_red`, `ind_red_n`, `ind_cob`, `ind_cob_n`, `ind_ciclo_`, `ind_cicl_1`, `Shape__Area`, `Shape__Length`

### `sectra_icc_comunas_rurales`

**Indicadores de ciclo-inclusion - comunas rurales**  
SECTRA / MTT · vigente  
185 registros · Polygon · 0.052 MB

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/ICC_1_WFL1/FeatureServer/1`
- Capa de origen: `comunas_con_indicadores_ICiclo_rural`
- Archivo: `data/parquet/sectra_icc_comunas_rurales.parquet`
- Campos: `OBJECTID`, `fid_1`, `objectid_1`, `shape_leng`, `dis_elec`, `cir_sena`, `cod_comuna`, `codregion`, `st_area_sh`, `st_length_`, `Region`, `Comuna`, `Provincia`, `Clasificac`, `COD_REG`, `REGION_1`, `COMUNA_1`, `CLASIF`, `KM_redvial`, `Km_ciclov_`, `nodos_exis`, `POB_TOT`, `POBcob_300`, `EQ_TOTAL`, `EQUIcob_30`, `prop_red`, `conectivid`, `conectiv_1`, `cobpob_`, `cobequipa_`, `ind_red`, `ind_red_n`, `ind_cob`, `ind_cob_n`, `ind_ciclo_`, `ind_cicl_1`, `Shape__Area`, `Shape__Length`

### `sectra_icc_comunas_urbanas`

**Indicadores de ciclo-inclusion - comunas urbanas**  
SECTRA / MTT · vigente  
82 registros · Polygon · 0.042 MB

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/ICC_1_WFL1/FeatureServer/3`
- Capa de origen: `comunas_con_indicadores_ICiclo_urb`
- Archivo: `data/parquet/sectra_icc_comunas_urbanas.parquet`
- Campos: `OBJECTID`, `fid_1`, `objectid_1`, `shape_leng`, `dis_elec`, `cir_sena`, `cod_comuna`, `codregion`, `st_area_sh`, `st_length_`, `Region`, `Comuna`, `Provincia`, `Clasificac`, `COD_REG`, `REGION_1`, `COMUNA_1`, `CLASIF`, `KM_redvial`, `Km_ciclov_`, `nodos_exis`, `POB_TOT`, `POBcob_300`, `EQ_TOTAL`, `EQUIcob_30`, `prop_red`, `conectivid`, `conectiv_1`, `cobpob_`, `cobequipa_`, `ind_red`, `ind_red_n`, `ind_cob`, `ind_cob_n`, `ind_ciclo_`, `ind_cicl_1`, `Shape__Area`, `Shape__Length`

### `sectra_icc_red_ciclov`

**RedCiclov - red usada para el calculo del ICC**  
SECTRA / MTT · vigente  
1.831 registros · Polyline · 1.057 MB

Subconjunto de la red (1.831 tramos) efectivamente usado en el indice.

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/ICC_1_WFL1/FeatureServer/0`
- Capa de origen: `RedCiclov`
- Archivo: `data/parquet/sectra_icc_red_ciclov.parquet`
- Campos: `FID`, `IDENTIFICA`, `REGION`, `COMUNA`, `EJE_VIA`, `INICIO`, `FIN`, `KM`, `TIPO`, `CARAC_FUNC`, `EMPLAZA_TE`, `EMPLAZA_N`, `URBANA`, `ETAPA`, `ETAPA_DET`, `CARTERA`, `BIP_o_PMU`, `NOMBRE_PRO`, `NORMATIVA`, `RESOLUCION`, `CUT_REG`, `CUT_COM`, `YEAR_EJECU`, `FUENTE_ACT`, `Shape_Leng`, `Shape__Length`

## C. Mediciones de flujo ciclista (SECTRA / MTT)

### `sectra_mediciones_antofagasta_talca`

**Mediciones de flujo ciclista - Antofagasta y Talca**  
SECTRA / MTT · vigente  
128 registros · Point · 0.023 MB

128 puntos de conteo con totales por periodo (PM/PT/PMD), total de ciclos y factores de expansion de ciclos y vehiculos.

- Servicio: `https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services/Mediciones_Antofagasta___Talca/FeatureServer/0`
- Capa de origen: `Mediciones Sectra`
- Archivo: `data/parquet/sectra_mediciones_antofagasta_talca.parquet`
- Campos: `PC`, `X`, `Y`, `FP`, `PM`, `PT`, `PMD`, `Tot_cicl`, `expan_ciclos`, `expan_veh`, `propor_`, `Comuna`, `FID`

## D. Contadores automáticos de flujo (MINVU)

### `minvu_contadores`

**Contadores automaticos de flujo de bicicletas**  
MINVU - DDU / Departamento de Obras Urbanas · vigente  
185 registros · Point · 0.045 MB

185 contadores con estadisticas agregadas: media diaria, semanal y mensual, promedio dia habil vs fin de semana, minimo y maximo diario, y ventana de observacion (primera y ultima fecha).

- Servicio: `https://geoide.minvu.cl/server/rest/services/Planes_Programas/Ciclov%C3%ADas_Minvu/FeatureServer/0`
- Capa de origen: `Contadores ciclovías`
- Archivo: `data/parquet/minvu_contadores.parquet`
- Campos de fecha en epoch ms (con columna `_iso` añadida): Primera_fecha, Ultima_fecha
- Campos: `NOMBRE_CONTADOR`, `ID_CONTADOR`, `EJE`, `Total_acumulado_dias`, `Mes_actual`, `Mes_Anterior`, `Media_diaria`, `Media_semanal`, `Media_Mensual`, `Promedio_dia_de_semana`, `Promedio_fin_de_semana`, `Min_diaria`, `Max_diaria`, `Primera_fecha`, `Ultima_fecha`, `PROVEEDOR`, `REGION`, `PROVINCIA`, `COMUNA`, `CUT_COM`, `Capa`, `OBJECTID`, `Primera_fecha_iso`, `Ultima_fecha_iso`

## E. Red de ciclovías MINVU

### `minvu_ciclovias_medida_presidencial`

**Ciclovias de la medida presidencial**  
MINVU - DDU · vigente  
691 registros · Polyline · 0.098 MB

- Servicio: `https://geoide.minvu.cl/server/rest/services/Planes_Programas/Ciclov%C3%ADas_Minvu/FeatureServer/1`
- Capa de origen: `Ciclovías medida presidencial`
- Archivo: `data/parquet/minvu_ciclovias_medida_presidencial.parquet`
- Campos de fecha en epoch ms (con columna `_iso` añadida): INICIO_OBRA, TERMINO_OBRA
- Campos: `EJE_1`, `PROYECTO_1`, `Capa`, `CUT_2010_2011`, `REGION`, `PROVINCIA`, `COMUNA`, `IDI_1`, `KILOMETROS_1`, `ESTADO_DE_AVANCE`, `CODIGO_CEHU`, `Linea_incluyendo_2016`, `INICIO_OBRA`, `TERMINO_OBRA`, `Sistema`, `OBJECTID`, `INICIO_OBRA_iso`, `TERMINO_OBRA_iso`

### `minvu_ciclovias_otras_medidas`

**Ciclovias de otras medidas (existentes o en construccion)**  
MINVU - DDU · vigente  
907 registros · Polyline · 0.143 MB

- Servicio: `https://geoide.minvu.cl/server/rest/services/Planes_Programas/Ciclov%C3%ADas_Minvu/FeatureServer/2`
- Capa de origen: `Ciclovías de otras medidas`
- Archivo: `data/parquet/minvu_ciclovias_otras_medidas.parquet`
- Campos: `Eje`, `Name`, `REGION`, `PROVINCIA`, `COMUNA`, `CUT_1`, `Capa`, `COD_CEHU_`, `OBJECTID`

## F. Entorno de las ciclovías MINVU

### `minvu_equipamientos`

**Equipamientos cercanos a ciclovias**  
MINVU - DDU · vigente  
5.504 registros · Point · 0.134 MB

- Servicio: `https://geoide.minvu.cl/server/rest/services/Planes_Programas/Ciclov%C3%ADas_Minvu/FeatureServer/3`
- Capa de origen: `Equipamientos cercanos a ciclovías`
- Archivo: `data/parquet/minvu_equipamientos.parquet`
- Campos: `TIPO`, `TIPO_det`, `CIUDAD`, `NOM_REGION`, `PROVINCIA`, `COMUNA`, `CUT_COM`, `OBJECTID`

### `minvu_manzanas_poblacion_beneficiada`

**Manzanas con poblacion beneficiada por ciclovias**  
MINVU - DDU · vigente  
33.232 registros · Polygon · 22.699 MB

33.232 manzanas dentro del area de influencia de las ciclovias, con poblacion por tramo etario, sexo, viviendas y hogares. El area de influencia MINVU es de 694 m medidos por la red vial (ver docs/fuentes/minvu_2018_analisis_contadores.pdf).

- Servicio: `https://geoide.minvu.cl/server/rest/services/Planes_Programas/Ciclov%C3%ADas_Minvu/FeatureServer/4`
- Capa de origen: `Manzanas con población beneficiada por ciclovías `
- Archivo: `data/parquet/minvu_manzanas_poblacion_beneficiada.parquet`
- Campos: `CIUDAD`, `PERSONAS`, `HOMBRES`, `MUJERES`, `DE_0_A_5_ANOS`, `DE_6_A_14_ANOS`, `DE_15_A_64_ANOS`, `DE_65_MAS_ANOS`, `TOTAL_VIVIENDAS`, `TOT_HOGARES`, `DEN_hab_vi`, `COMUNA`, `OBJECTID`

## Documentos de respaldo

### `minvu_2018_analisis_contadores`

**Analisis de Contadores de Ciclovias - Resultados preliminares**  
MINVU - Comision de Estudios Habitacionales y Urbanos + DOU · 2018-09 · 0.26 MB  
`docs/fuentes/minvu_2018_analisis_contadores.pdf`

48 ejes en 23 sistemas y 19 ciudades, con mas de 9 meses de contador. Define el area de influencia de 694 m por red vial y cruza pasadas contra variables de diseno, entorno y clima.

- Origen: https://www.minvu.gob.cl/wp-content/uploads/2018-27-09-Analisis%20Descriptivo-Contadores.pdf
