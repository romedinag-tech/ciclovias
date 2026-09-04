# -*- coding: utf-8 -*-
"""
Registro declarativo de las fuentes de datos de movilidad activa (bicicleta).

Cada entrada describe UNA capa de un servicio ArcGIS que se descarga tal cual
viene del origen. La normalizacion NO ocurre aqui: este archivo es el inventario
trazable de que se bajo, de donde y cuando.

Convenciones:
  slug       nombre del archivo de salida (sin extension)
  base       URL del FeatureServer (sin /<id>)
  layer      id numerico de la capa dentro del FeatureServer
  organismo  institucion responsable del dato
  corte      fecha declarada del catastro (la del NOMBRE de la capa, no la de
             descarga); None cuando la fuente no la declara
  vigente    True  -> version que se usa para analisis
             False -> version historica, se guarda para la serie temporal
"""

SERVICIOS = {
    "SECTRA": "https://services6.arcgis.com/feQ9HId8vmgonvvD/arcgis/rest/services",
    "MINVU": "https://geoide.minvu.cl/server/rest/services/Planes_Programas",
}

FUENTES = [
    # ------------------------------------------------------------------ #
    # A. Catastro Nacional de Ciclovias (SECTRA / MTT) - serie temporal   #
    # ------------------------------------------------------------------ #
    dict(
        slug="sectra_ciclovias_nac_2026_07",
        base=f"{SERVICIOS['SECTRA']}/CICLOV_validVisor_WFL1/FeatureServer",
        layer=0,
        titulo="Catastro Nacional de Ciclovias - CICLOVIA_jul2026",
        organismo="SECTRA / Programa de Vialidad y Transporte Urbano - MTT",
        corte="2026-07",
        vigente=True,
        grupo="catastro_nacional",
        nota="Capa que alimenta el 'Visor de Ciclovias Chile'. Version mas reciente.",
    ),
    dict(
        slug="sectra_ciclovias_nac_local_capa2",
        base=f"{SERVICIOS['SECTRA']}/CICLOV_validVisor_WFL1/FeatureServer",
        layer=1,
        titulo="Catastro Nacional de Ciclovias - CICLOVIA_LOCAL_CAPA2",
        organismo="SECTRA / Programa de Vialidad y Transporte Urbano - MTT",
        corte=None,
        vigente=False,
        grupo="catastro_nacional",
        nota="Segunda capa del mismo servicio, con menos registros que la capa 0. "
             "Se conserva sin interpretar: falta confirmar con SECTRA si es un "
             "respaldo previo o un subconjunto editable.",
    ),
    dict(
        slug="sectra_ciclovias_nac_2025_07",
        base=f"{SERVICIOS['SECTRA']}/ICC1_planes_WFL1/FeatureServer",
        layer=1,
        titulo="Catastro Nacional de Ciclovias - CICLOVnac_jul25",
        organismo="SECTRA / MTT",
        corte="2025-07",
        vigente=False,
        grupo="catastro_nacional",
    ),
    dict(
        slug="sectra_ciclovias_nac_2024_11",
        base=f"{SERVICIOS['SECTRA']}/CICLOVnac_07112024/FeatureServer",
        layer=0,
        titulo="Catastro Nacional de Ciclovias - CICLOVnac_07112024",
        organismo="SECTRA / MTT",
        corte="2024-11",
        vigente=False,
        grupo="catastro_nacional",
    ),
    dict(
        slug="sectra_ciclovias_nac_2024_09",
        base=f"{SERVICIOS['SECTRA']}/CICLOVnac_sep24_WFL1/FeatureServer",
        layer=27,
        titulo="Catastro Nacional de Ciclovias - CICLOVnac_160924",
        organismo="SECTRA / MTT",
        corte="2024-09",
        vigente=False,
        grupo="catastro_nacional",
    ),

    # ------------------------------------------------------------------ #
    # B. Indice de Ciclo-inclusion Comunal (ICC) - SECTRA                 #
    # ------------------------------------------------------------------ #
    dict(
        slug="sectra_icc_comunas",
        solo_atributos=True,
        base=f"{SERVICIOS['SECTRA']}/ICC_1_WFL1/FeatureServer",
        layer=4,
        titulo="Indicadores de ciclo-inclusion por comuna (universo nacional)",
        organismo="SECTRA / MTT",
        corte=None,
        vigente=True,
        grupo="indice_comunal",
        nota="346 comunas con km de red vial, km de ciclovia, nodos, poblacion "
             "cubierta a 300 m, equipamientos cubiertos e indices normalizados.",
    ),
    dict(
        slug="sectra_icc_comunas_urbanas",
        solo_atributos=True,
        base=f"{SERVICIOS['SECTRA']}/ICC_1_WFL1/FeatureServer",
        layer=3,
        titulo="Indicadores de ciclo-inclusion - comunas urbanas",
        organismo="SECTRA / MTT",
        corte=None,
        vigente=True,
        grupo="indice_comunal",
    ),
    dict(
        slug="sectra_icc_comunas_mixtas",
        solo_atributos=True,
        base=f"{SERVICIOS['SECTRA']}/ICC_1_WFL1/FeatureServer",
        layer=2,
        titulo="Indicadores de ciclo-inclusion - comunas mixtas",
        organismo="SECTRA / MTT",
        corte=None,
        vigente=True,
        grupo="indice_comunal",
    ),
    dict(
        slug="sectra_icc_comunas_rurales",
        solo_atributos=True,
        base=f"{SERVICIOS['SECTRA']}/ICC_1_WFL1/FeatureServer",
        layer=1,
        titulo="Indicadores de ciclo-inclusion - comunas rurales",
        organismo="SECTRA / MTT",
        corte=None,
        vigente=True,
        grupo="indice_comunal",
    ),
    dict(
        slug="sectra_icc_comunas_planes",
        solo_atributos=True,
        base=f"{SERVICIOS['SECTRA']}/ICC_2_WFL1/FeatureServer",
        layer=5,
        titulo="Indicadores de ciclo-inclusion incorporando ciclovias planificadas",
        organismo="SECTRA / MTT",
        corte=None,
        vigente=True,
        grupo="indice_comunal",
        nota="Escenario con cartera planificada; se compara contra sectra_icc_comunas.",
    ),
    dict(
        slug="sectra_icc_red_ciclov",
        base=f"{SERVICIOS['SECTRA']}/ICC_1_WFL1/FeatureServer",
        layer=0,
        titulo="RedCiclov - red usada para el calculo del ICC",
        organismo="SECTRA / MTT",
        corte=None,
        vigente=True,
        grupo="indice_comunal",
        nota="Subconjunto de la red (1.831 tramos) efectivamente usado en el indice.",
    ),

    # ------------------------------------------------------------------ #
    # C. Mediciones de flujo ciclista (SECTRA)                            #
    # ------------------------------------------------------------------ #
    dict(
        slug="sectra_mediciones_antofagasta_talca",
        base=f"{SERVICIOS['SECTRA']}/Mediciones_Antofagasta___Talca/FeatureServer",
        layer=0,
        titulo="Mediciones de flujo ciclista - Antofagasta y Talca",
        organismo="SECTRA / MTT",
        corte=None,
        vigente=True,
        grupo="mediciones",
        nota="128 puntos de conteo con totales por periodo (PM/PT/PMD), total de "
             "ciclos y factores de expansion de ciclos y vehiculos.",
    ),

    # ------------------------------------------------------------------ #
    # D. Visor de Ciclovias MINVU                                         #
    # ------------------------------------------------------------------ #
    dict(
        slug="minvu_contadores",
        base=f"{SERVICIOS['MINVU']}/Ciclov%C3%ADas_Minvu/FeatureServer",
        layer=0,
        titulo="Contadores automaticos de flujo de bicicletas",
        organismo="MINVU - DDU / Departamento de Obras Urbanas",
        corte=None,
        vigente=True,
        grupo="contadores",
        nota="185 contadores con estadisticas agregadas: media diaria, semanal y "
             "mensual, promedio dia habil vs fin de semana, minimo y maximo "
             "diario, y ventana de observacion (primera y ultima fecha).",
    ),
    dict(
        slug="minvu_ciclovias_medida_presidencial",
        base=f"{SERVICIOS['MINVU']}/Ciclov%C3%ADas_Minvu/FeatureServer",
        layer=1,
        titulo="Ciclovias de la medida presidencial",
        organismo="MINVU - DDU",
        corte=None,
        vigente=True,
        grupo="minvu_red",
    ),
    dict(
        slug="minvu_ciclovias_otras_medidas",
        base=f"{SERVICIOS['MINVU']}/Ciclov%C3%ADas_Minvu/FeatureServer",
        layer=2,
        titulo="Ciclovias de otras medidas (existentes o en construccion)",
        organismo="MINVU - DDU",
        corte=None,
        vigente=True,
        grupo="minvu_red",
    ),
    dict(
        slug="minvu_equipamientos",
        base=f"{SERVICIOS['MINVU']}/Ciclov%C3%ADas_Minvu/FeatureServer",
        layer=3,
        titulo="Equipamientos cercanos a ciclovias",
        organismo="MINVU - DDU",
        corte=None,
        vigente=True,
        grupo="minvu_entorno",
    ),
    dict(
        slug="minvu_manzanas_poblacion_beneficiada",
        base=f"{SERVICIOS['MINVU']}/Ciclov%C3%ADas_Minvu/FeatureServer",
        layer=4,
        titulo="Manzanas con poblacion beneficiada por ciclovias",
        organismo="MINVU - DDU",
        corte=None,
        vigente=True,
        grupo="minvu_entorno",
        nota="33.232 manzanas dentro del area de influencia de las ciclovias, con "
             "poblacion por tramo etario, sexo, viviendas y hogares. "
             "El area de influencia MINVU es de 694 m medidos por la red vial "
             "(ver docs/fuentes/minvu_2018_analisis_contadores.pdf).",
    ),
]

# Documentos de respaldo (no son capas)
DOCUMENTOS = [
    dict(
        slug="minvu_2018_analisis_contadores",
        url="https://www.minvu.gob.cl/wp-content/uploads/"
            "2018-27-09-Analisis%20Descriptivo-Contadores.pdf",
        titulo="Analisis de Contadores de Ciclovias - Resultados preliminares",
        organismo="MINVU - Comision de Estudios Habitacionales y Urbanos + DOU",
        fecha="2018-09",
        nota="48 ejes en 23 sistemas y 19 ciudades, con mas de 9 meses de "
             "contador. Define el area de influencia de 694 m por red vial y "
             "cruza pasadas contra variables de diseno, entorno y clima.",
    ),
]


def por_slug(slug):
    for f in FUENTES:
        if f["slug"] == slug:
            return f
    raise KeyError(slug)
