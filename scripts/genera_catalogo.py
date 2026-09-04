# -*- coding: utf-8 -*-
"""
Genera FUENTES.md leyendo data/MANIFIESTO.json.

Ninguna cifra del catalogo se escribe a mano: todas salen del manifiesto que
produjo la descarga. Si un numero no esta ahi, no se publica.

Uso:  python -X utf8 scripts/genera_catalogo.py
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MANIFIESTO = RAIZ / "data" / "MANIFIESTO.json"
SALIDA = RAIZ / "FUENTES.md"

TITULOS_GRUPO = {
    "catastro_nacional": "A. Catastro Nacional de Ciclovías (SECTRA / MTT)",
    "indice_comunal": "B. Índice de ciclo-inclusión comunal — ICC (SECTRA / MTT)",
    "mediciones": "C. Mediciones de flujo ciclista (SECTRA / MTT)",
    "contadores": "D. Contadores automáticos de flujo (MINVU)",
    "minvu_red": "E. Red de ciclovías MINVU",
    "minvu_entorno": "F. Entorno de las ciclovías MINVU",
}
ORDEN = list(TITULOS_GRUPO)


def fmt(n):
    return f"{n:,}".replace(",", ".")


def main():
    m = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    capas = m["capas"]
    total_reg = sum(c["n_registros"] for c in capas)
    total_mb = sum(c["parquet_mb"] for c in capas)

    L = []
    L.append("# Catálogo de fuentes — banco de datos de movilidad activa\n")
    L.append("> Archivo **generado**. No editar a mano: correr\n"
             "> `python -X utf8 scripts/genera_catalogo.py`.\n")
    L.append(f"Descarga registrada en `data/MANIFIESTO.json` "
             f"({m['generado_utc']} UTC).\n")
    L.append(f"**{len(capas)} capas · {fmt(total_reg)} registros · "
             f"{total_mb:.1f} MB en Parquet**\n")

    # ------------------------------------------------------------------ #
    problemas = [(c["slug"], p) for c in capas for p in c.get("problemas") or []]
    L.append("## Verificación de integridad\n")
    if problemas:
        L.append("Discrepancias detectadas al descargar "
                 "(se dejan visibles, no se corrigen en silencio):\n")
        for slug, p in problemas:
            L.append(f"- `{slug}`: {p}")
        L.append("")
    else:
        L.append("Todas las capas cuadran: el número de registros descargados "
                 "coincide con el `count` declarado por cada servicio, no hay "
                 "registros sin geometría y todas las extensiones caen dentro "
                 "de Chile.\n")
    if m.get("fallidas"):
        L.append("Descargas fallidas:\n")
        for f in m["fallidas"]:
            L.append(f"- `{f['slug']}`: {f['error'][:200]}")
        L.append("")

    # ------------------------------------------------------------------ #
    grupos = {}
    for c in capas:
        grupos.setdefault(c["grupo"], []).append(c)

    for g in ORDEN + [k for k in grupos if k not in ORDEN]:
        if g not in grupos:
            continue
        L.append(f"## {TITULOS_GRUPO.get(g, g)}\n")
        for c in sorted(grupos[g], key=lambda x: (not x.get("vigente"),
                                                  x.get("corte") or "",
                                                  x["slug"]), reverse=False):
            marca = "vigente" if c.get("vigente") else "histórica / no vigente"
            L.append(f"### `{c['slug']}`\n")
            L.append(f"**{c['titulo']}**  ")
            L.append(f"{c['organismo']} · {marca}"
                     + (f" · corte declarado {c['corte']}" if c.get("corte") else "")
                     + "  ")
            L.append(f"{fmt(c['n_registros'])} registros · "
                     f"{c['geometria'].replace('esriGeometry','')} · "
                     f"{c['parquet_mb']} MB\n")
            if c.get("nota"):
                L.append(f"{c['nota']}\n")
            L.append(f"- Servicio: `{c['servicio']}`")
            L.append(f"- Capa de origen: `{c['capa_nombre']}`")
            L.append(f"- Archivo: `data/parquet/{c['slug']}.parquet`")
            if c.get("campos_fecha_epoch_ms"):
                L.append(f"- Campos de fecha en epoch ms (con columna `_iso` "
                         f"añadida): {', '.join(c['campos_fecha_epoch_ms'])}")
            L.append(f"- Campos: {', '.join('`%s`' % x for x in c['campos'])}\n")

    # ------------------------------------------------------------------ #
    if m.get("documentos"):
        L.append("## Documentos de respaldo\n")
        for d in m["documentos"]:
            L.append(f"### `{d['slug']}`\n")
            L.append(f"**{d['titulo']}**  ")
            L.append(f"{d['organismo']} · {d.get('fecha','')} · "
                     f"{d['bytes']/1e6:.2f} MB  ")
            L.append(f"`{d['archivo']}`\n")
            if d.get("nota"):
                L.append(f"{d['nota']}\n")
            L.append(f"- Origen: {d['url']}\n")

    SALIDA.write_text("\n".join(L), encoding="utf-8")
    print(f"FUENTES.md escrito: {len(capas)} capas, {fmt(total_reg)} registros, "
          f"{len(problemas)} problemas registrados")


if __name__ == "__main__":
    main()
