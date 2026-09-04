# -*- coding: utf-8 -*-
"""
Descarga completa de capas ArcGIS REST a GeoJSON crudo + Parquet.

Estrategia de paginacion: se piden PRIMERO todos los OBJECTID
(returnIdsOnly=true) y luego se consultan por bloques con
`where <oid> IN (...)`. Es mas robusto que resultOffset porque no depende de
que el servidor soporte paginacion ni de que el orden sea estable, y ademas
da una cota independiente contra la cual verificar cuantos registros llegaron.

Uso:
    python -X utf8 scripts/descarga_arcgis.py            # todas las fuentes
    python -X utf8 scripts/descarga_arcgis.py <slug> ... # solo algunas
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fuentes import DOCUMENTOS, FUENTES  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_PARQUET = RAIZ / "data" / "parquet"
DIR_DOCS = RAIZ / "docs" / "fuentes"
MANIFIESTO = RAIZ / "data" / "MANIFIESTO.json"

UA = {"User-Agent": "Mozilla/5.0 (analisis-rmg-ciclovias)"}
BLOQUE_IDS = 400          # ids por request; conservador para URLs largas
PAUSA = 0.25              # segundos entre requests, para no castigar el servicio


# --------------------------------------------------------------------------- #
# Utilidades HTTP
# --------------------------------------------------------------------------- #
def _get(url, params, reintentos=4, post=False):
    """Consulta al servicio.

    `post=True` envia los parametros en el cuerpo. Es obligatorio para las
    consultas por lista de OBJECTID: con bloques grandes la query string supera
    el limite del servidor y ArcGIS responde **404**, no 414, de modo que el
    error se lee como 'capa inexistente' cuando en realidad es 'URL muy larga'.
    """
    q = urllib.parse.urlencode(params)
    ultimo = None
    for intento in range(reintentos):
        try:
            if post:
                req = urllib.request.Request(
                    url, data=q.encode("utf-8"),
                    headers={**UA,
                             "Content-Type": "application/x-www-form-urlencoded"})
            else:
                req = urllib.request.Request(f"{url}?{q}", headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            if isinstance(d, dict) and "error" in d:
                raise RuntimeError(d["error"].get("message", d["error"]))
            return d
        except Exception as e:                      # noqa: BLE001
            ultimo = e
            time.sleep(1.5 * (intento + 1))
    raise RuntimeError(f"fallo tras {reintentos} intentos: {url} -> {ultimo}")


# --------------------------------------------------------------------------- #
# Conversion de geometria Esri -> Shapely
# --------------------------------------------------------------------------- #
def _esri_a_shapely(g, tipo):
    if not g:
        return None
    if tipo == "esriGeometryPoint":
        if g.get("x") is None:
            return None
        return Point(g["x"], g["y"])
    if tipo == "esriGeometryPolyline":
        paths = [p for p in g.get("paths", []) if len(p) >= 2]
        if not paths:
            return None
        lineas = [LineString([(c[0], c[1]) for c in p]) for p in paths]
        return lineas[0] if len(lineas) == 1 else MultiLineString(lineas)
    if tipo == "esriGeometryPolygon":
        anillos = [r for r in g.get("rings", []) if len(r) >= 4]
        if not anillos:
            return None
        # Esri: anillo exterior en sentido horario, agujeros en antihorario.
        def _area_firmada(r):
            return sum((r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1])
                       for i in range(len(r) - 1)) / 2.0

        exteriores, agujeros = [], []
        for r in anillos:
            coords = [(c[0], c[1]) for c in r]
            (exteriores if _area_firmada(r) < 0 else agujeros).append(coords)
        if not exteriores:                    # todos dieron el mismo signo
            exteriores, agujeros = [[(c[0], c[1]) for c in r] for r in anillos], []
        polis = []
        for ext in exteriores:
            p = Polygon(ext)
            dentro = [h for h in agujeros if p.contains(Polygon(h).representative_point())]
            polis.append(Polygon(ext, dentro) if dentro else p)
        return polis[0] if len(polis) == 1 else MultiPolygon(polis)
    raise ValueError(f"geometria no soportada: {tipo}")


# --------------------------------------------------------------------------- #
# Descarga de una capa
# --------------------------------------------------------------------------- #
def descarga_capa(fuente):
    url = f"{fuente['base']}/{fuente['layer']}"
    meta = _get(url, {"f": "json"})
    oid_field = meta.get("objectIdField") or "OBJECTID"
    tipo_geom = meta.get("geometryType")

    n_declarado = _get(f"{url}/query",
                       {"where": "1=1", "returnCountOnly": "true", "f": "json"})["count"]
    ids = _get(f"{url}/query",
               {"where": "1=1", "returnIdsOnly": "true", "f": "json"}).get("objectIds") or []
    ids = sorted(set(ids))

    print(f"  capa '{meta.get('name')}' | oid={oid_field} | {tipo_geom}")
    print(f"  count declarado={n_declarado} | ids recuperados={len(ids)}")

    filas, geoms = [], []
    for i in range(0, len(ids), BLOQUE_IDS):
        bloque = ids[i:i + BLOQUE_IDS]
        d = _get(f"{url}/query", {
            "where": f"{oid_field} IN ({','.join(str(x) for x in bloque)})",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "json",
        }, post=True)
        for feat in d.get("features", []):
            filas.append(feat.get("attributes", {}))
            geoms.append(_esri_a_shapely(feat.get("geometry"), tipo_geom))
        print(f"    {min(i + BLOQUE_IDS, len(ids))}/{len(ids)}", end="\r")
        time.sleep(PAUSA)
    print(" " * 40, end="\r")

    gdf = gpd.GeoDataFrame(pd.DataFrame(filas), geometry=geoms, crs="EPSG:4326")

    # --- verificaciones duras -------------------------------------------- #
    problemas = []
    if len(gdf) != n_declarado:
        problemas.append(f"registros {len(gdf)} != count declarado {n_declarado}")
    sin_geom = int(gdf.geometry.isna().sum())
    if sin_geom:
        problemas.append(f"{sin_geom} registros sin geometria")
    if len(gdf) and not gdf.geometry.isna().all():
        minx, miny, maxx, maxy = gdf.total_bounds
        if not (-110 < minx < -60 and -60 < miny < -15):
            problemas.append(f"bbox fuera de Chile: {minx:.3f},{miny:.3f},{maxx:.3f},{maxy:.3f}")

    return gdf, meta, n_declarado, sin_geom, problemas


def _fechas_esri_a_texto(gdf, meta):
    """Los campos Date de Esri llegan como epoch ms. Se agrega una columna
    legible al lado, sin borrar el valor original."""
    campos = [f["name"] for f in meta.get("fields", [])
              if f.get("type") == "esriFieldTypeDate" and f["name"] in gdf.columns]
    for c in campos:
        gdf[f"{c}_iso"] = pd.to_datetime(gdf[c], unit="ms", errors="coerce", utc=True)
    return gdf, campos


def main(slugs=None):
    for d in (DIR_RAW, DIR_PARQUET, DIR_DOCS):
        d.mkdir(parents=True, exist_ok=True)

    objetivo = [f for f in FUENTES if not slugs or f["slug"] in slugs]
    registro, fallidas = [], []

    for f in objetivo:
        print(f"\n[{f['slug']}] {f['titulo']}")
        try:
            gdf, meta, n_dec, sin_geom, problemas = descarga_capa(f)
        except Exception as e:                      # noqa: BLE001
            print(f"  !! FALLO: {e}")
            fallidas.append({"slug": f["slug"], "error": str(e)})
            continue

        gdf, campos_fecha = _fechas_esri_a_texto(gdf, meta)

        p_pq = DIR_PARQUET / f"{f['slug']}.parquet"

        if f.get("solo_atributos"):
            # La geometria de estas capas es la division comunal, que el repo ya
            # tiene a nivel nacional. Guardarla aqui la duplicaria cinco veces
            # (cada capa ICC repite los mismos poligonos con otro set de
            # indicadores) por decenas de MB. Se guarda la tabla y se une por
            # `cod_comuna` -> `cut_com`.
            mb_geom = gdf.memory_usage(deep=True).get("geometry", 0) / 1e6
            df = pd.DataFrame(gdf.drop(columns="geometry"))
            df.to_parquet(p_pq, index=False)
            p_geo = None
            print(f"  -> {len(df)} registros | SOLO ATRIBUTOS "
                  f"(geometria comunal omitida, ~{mb_geom:.0f} MB en memoria) "
                  f"| parquet {p_pq.stat().st_size/1e6:.1f} MB")
        else:
            p_geo = DIR_RAW / f"{f['slug']}.geojson"
            gdf.to_file(p_geo, driver="GeoJSON")
            gdf.to_parquet(p_pq, index=False)
            print(f"  -> {len(gdf)} registros | geojson "
                  f"{p_geo.stat().st_size/1e6:.1f} MB"
                  f" | parquet {p_pq.stat().st_size/1e6:.1f} MB")
        for p in problemas:
            print(f"  [!] {p}")

        registro.append({
            "slug": f["slug"],
            "titulo": f["titulo"],
            "organismo": f["organismo"],
            "grupo": f["grupo"],
            "corte": f.get("corte"),
            "vigente": f.get("vigente"),
            "nota": f.get("nota"),
            "servicio": f"{f['base']}/{f['layer']}",
            "capa_nombre": meta.get("name"),
            "geometria": meta.get("geometryType"),
            "n_registros": len(gdf),
            "n_declarado_servicio": n_dec,
            "n_sin_geometria": sin_geom,
            "campos_fecha_epoch_ms": campos_fecha,
            "campos": [c for c in gdf.columns if c != "geometry"],
            "problemas": problemas,
            "solo_atributos": bool(f.get("solo_atributos")),
            "geojson_mb": round(p_geo.stat().st_size / 1e6, 3) if p_geo else None,
            "parquet_mb": round(p_pq.stat().st_size / 1e6, 3),
            "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })

    # documentos de respaldo
    docs = []
    for d in DOCUMENTOS:
        destino = DIR_DOCS / f"{d['slug']}.pdf"
        try:
            req = urllib.request.Request(d["url"], headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                destino.write_bytes(r.read())
            ok = destino.stat().st_size
            print(f"\n[doc] {d['slug']} -> {ok/1e6:.2f} MB")
            docs.append({**d, "archivo": str(destino.relative_to(RAIZ)).replace("\\", "/"),
                         "bytes": ok})
        except Exception as e:                      # noqa: BLE001
            print(f"\n[doc] {d['slug']} FALLO: {e}")
            fallidas.append({"slug": d["slug"], "error": str(e)})

    if slugs and MANIFIESTO.exists():               # descarga parcial: fusiona
        previo = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
        idx = {c["slug"]: c for c in previo.get("capas", [])}
        idx.update({c["slug"]: c for c in registro})
        registro = list(idx.values())

    MANIFIESTO.write_text(json.dumps({
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "capas": registro,
        "documentos": docs,
        "fallidas": fallidas,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n=== {len(registro)} capas | "
          f"{sum(c['n_registros'] for c in registro):,} registros | "
          f"{len(fallidas)} fallos ===")
    if fallidas:
        for x in fallidas:
            print("  FALLO:", x["slug"], "->", x["error"][:150])


if __name__ == "__main__":
    main(sys.argv[1:] or None)
