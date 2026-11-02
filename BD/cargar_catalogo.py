# -*- coding: utf-8 -*-
"""Carga el catalogo comun en PostgreSQL (idempotente: se puede ejecutar varias veces).

Fuentes:
  1. datos/soa_gestitel.xlsx      -> 142 controles de la SOA de GESTITEL
                                     (93 ISO 27001:2022 + 49 ISO 27701:2025 A.1/A.2)
                                     y, por su columna "Equivalencia", los 29 controles A.3.
  2. Skill del Entregable 1        -> clausulas 4-10 y criterio de evidencia esperada.
  3. datos/expedientes_guia.json   -> expedientes D01-D37 y su relacion con cada requisito.
  4. datos/programa_seguridad_6_1_3c.json -> controles 27001 sin equivalente A.3: van al
                                     programa de seguridad de 6.1.3 c) (expediente D16).
  5. datos/requisitos_brecha_gestitel.json -> los 69 requisitos de las clausulas 4-10 del
                                     analisis de brecha de GESTITEL (core_gaprequirement).

Antes de cargar verifica contra Entregable-1/ISOS/texto/ISO 27701-2025.md que cada
referencia de la guia y de la skill existe en la norma y que los 15 temas de
6.1.3 c) aparecen literalmente; si algo no cuadra, se detiene sin cargar.

Uso:  python cargar_catalogo.py [--soa RUTA_EXCEL]
"""

import argparse
import json
import os
import re
import sys

import openpyxl

from db import conectar

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SOA_XLSX = os.path.join(AQUI, "datos", "soa_gestitel.xlsx")
GUIA_JSON = os.path.join(AQUI, "datos", "expedientes_guia.json")
SKILL_JSON = os.path.join(RAIZ, "Entregable-1", "02-skill", "evidencia-auditoria-pims",
                          "references", "controles_27701.json")

BRECHA_JSON = os.path.join(AQUI, "datos", "requisitos_brecha_gestitel.json")
PROGRAMA_JSON = os.path.join(AQUI, "datos", "programa_seguridad_6_1_3c.json")
NORMA_MD = os.path.join(RAIZ, "Entregable-1", "ISOS", "texto", "ISO 27701-2025.md")

NOMBRES_GRUPO_A3 = "Controles de seguridad comunes (A.3)"


def leer_norma(ruta):
    """(conjunto de referencias con seccion propia, texto de la clausula 6.1.3)."""
    encabezados, seccion, actual = set(), [], None
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            m = re.match(r"^## ((?:[A-F]\.)?\d+(?:\.\d+)*)\b", linea)
            if m:
                actual = m.group(1)
                encabezados.add(actual)
                continue
            if actual == "6.1.3":
                seccion.append(linea)
    return encabezados, "".join(seccion)


def leer_soa(ruta):
    """Devuelve las filas de la SOA como diccionarios {encabezado: valor}."""
    ws = openpyxl.load_workbook(ruta, read_only=True, data_only=True).worksheets[0]
    filas = list(ws.iter_rows(values_only=True))
    i_enc = next(i for i, f in enumerate(filas) if f and f[0] == "Id")
    enc = [str(c).strip() if c is not None else "" for c in filas[i_enc]]
    datos = []
    for f in filas[i_enc + 1:]:
        if not f or f[1] is None:
            continue
        datos.append({enc[j]: f[j] for j in range(len(enc))})
    return datos


def clausula_de(codigo, clausulas):
    """'4.2.a' -> '4.2', '9.2.1' -> '9.2', '9.3.2.a' -> '9.3': la clausula del catalogo que lo contiene."""
    partes = codigo.split(".")
    while partes:
        if ".".join(partes) in clausulas:
            return ".".join(partes)
        partes.pop()
    return None


def si_no(valor):
    if valor is None:
        return None
    return str(valor).strip().lower() in ("sí", "si", "true", "1", "aplica")


def texto(valor):
    if valor is None:
        return None
    s = str(valor).strip()
    return s or None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--soa", default=SOA_XLSX, help="Excel exportado de la SOA de GESTITEL")
    args = ap.parse_args()

    soa = leer_soa(args.soa)
    guia = json.load(open(GUIA_JSON, encoding="utf-8"))
    programa = json.load(open(PROGRAMA_JSON, encoding="utf-8"))
    skill = {c["ref"]: c for c in json.load(open(SKILL_JSON, encoding="utf-8"))["controles"]}
    encabezados, texto_613 = leer_norma(NORMA_MD)

    # --- Verificacion contra el texto de ISO/IEC 27701:2025 ---
    texto_613 = re.sub(r"\s+", " ", texto_613.lower())
    temas_ausentes = [t for t in programa["temas"] if t not in texto_613]
    if temas_ausentes:
        sys.exit("Temas que no aparecen en 6.1.3 c) de la norma: %s" % temas_ausentes)
    refs_27701 = sorted({r for r in guia["requisito_expediente"]} | set(skill))
    no_en_norma = [r for r in refs_27701 if r not in encabezados]
    if no_en_norma:
        sys.exit("Requisitos de la guia/skill que no existen en la norma: %s" % no_en_norma)

    # Controles A.3 a partir de la columna Equivalencia ("A.3.14 Proteccion de registros")
    a3 = {}
    for f in soa:
        eq = texto(f.get("Equivalencia"))
        if not eq:
            continue
        m = re.match(r"^(A\.3\.\d+)\s+(.*)$", eq)
        if m:
            a3[m.group(1)] = {"nombre": m.group(2).strip(), "cubierto_por": f["Código de control"]}

    with conectar() as cx, cx.cursor() as cur:
        # 1) Expedientes
        for e in guia["expedientes"]:
            cur.execute(
                """INSERT INTO expedientes (codigo, nombre, marca, referencias, fase, accion,
                                            responsable_propuesto, contenido, se_revisa_cuando)
                   VALUES (%(codigo)s, %(nombre)s, %(marca)s, %(referencias)s, %(fase)s, %(accion)s,
                           %(responsable_propuesto)s, %(contenido)s, %(se_revisa_cuando)s)
                   ON CONFLICT (codigo) DO UPDATE SET
                     nombre = EXCLUDED.nombre, marca = EXCLUDED.marca, referencias = EXCLUDED.referencias,
                     fase = EXCLUDED.fase, accion = EXCLUDED.accion,
                     responsable_propuesto = EXCLUDED.responsable_propuesto,
                     contenido = EXCLUDED.contenido, se_revisa_cuando = EXCLUDED.se_revisa_cuando""",
                e,
            )

        sql_req = """
            INSERT INTO requisitos (codigo, tipo, norma, nombre, grupo, nombre_grupo, rol_aplicable,
                                    descripcion, cubierto_por, en_gestitel, gestitel_id,
                                    ley29733_aplica, ley29733_articulos, ley29733_explicacion,
                                    evidencia_esperada, evidencia_minima)
            VALUES (%(codigo)s, %(tipo)s, %(norma)s, %(nombre)s, %(grupo)s, %(nombre_grupo)s, %(rol)s,
                    %(descripcion)s, %(cubierto_por)s, %(en_gestitel)s, %(gestitel_id)s,
                    %(ley_aplica)s, %(ley_art)s, %(ley_exp)s, %(ev_esperada)s, %(ev_minima)s)
            ON CONFLICT (codigo) DO UPDATE SET
              tipo = EXCLUDED.tipo, norma = EXCLUDED.norma, nombre = EXCLUDED.nombre,
              grupo = EXCLUDED.grupo, nombre_grupo = EXCLUDED.nombre_grupo,
              rol_aplicable = EXCLUDED.rol_aplicable, descripcion = EXCLUDED.descripcion,
              cubierto_por = EXCLUDED.cubierto_por, en_gestitel = EXCLUDED.en_gestitel,
              gestitel_id = EXCLUDED.gestitel_id, ley29733_aplica = EXCLUDED.ley29733_aplica,
              ley29733_articulos = EXCLUDED.ley29733_articulos,
              ley29733_explicacion = EXCLUDED.ley29733_explicacion,
              evidencia_esperada = EXCLUDED.evidencia_esperada,
              evidencia_minima = EXCLUDED.evidencia_minima"""

        def criterio(codigo):
            c = skill.get(codigo) or {}
            return c.get("evidencia_esperada"), c.get("minimo")

        # 2) Los 142 controles de GESTITEL
        for f in soa:
            cod = f["Código de control"]
            ev, mi = criterio(cod)
            cur.execute(sql_req, {
                "codigo": cod, "tipo": "control", "norma": texto(f.get("Norma de origen")),
                "nombre": texto(f.get("Nombre del control")), "grupo": texto(f.get("Grupo")),
                "nombre_grupo": texto(f.get("Nombre del grupo")), "rol": texto(f.get("Rol aplicable")),
                "descripcion": texto(f.get("Descripción")), "cubierto_por": None,
                "en_gestitel": True, "gestitel_id": f.get("Id"),
                "ley_aplica": si_no(f.get("Ley 29733 – Aplica")),
                "ley_art": texto(f.get("Ley 29733 – Artículos")),
                "ley_exp": texto(f.get("Ley 29733 – Explicación")),
                "ev_esperada": ev, "ev_minima": mi,
            })

        # 3) Los 29 controles A.3 (no estan en GESTITEL; apuntan a su equivalente 27001)
        for cod, d in a3.items():
            ev, mi = criterio(cod)
            cur.execute(sql_req, {
                "codigo": cod, "tipo": "control", "norma": "ISO/IEC 27701:2025",
                "nombre": d["nombre"], "grupo": "A.3", "nombre_grupo": NOMBRES_GRUPO_A3, "rol": "Todos",
                "descripcion": None, "cubierto_por": d["cubierto_por"], "en_gestitel": False,
                "gestitel_id": None, "ley_aplica": None, "ley_art": None, "ley_exp": None,
                "ev_esperada": ev, "ev_minima": mi,
            })

        # 4) Clausulas 4-10 (de la skill del Entregable 1)
        n_cla = 0
        for cod, c in skill.items():
            if c.get("grupo") != "clausula":
                continue
            n_cla += 1
            cur.execute(sql_req, {
                "codigo": cod, "tipo": "clausula", "norma": "ISO/IEC 27701:2025", "nombre": c["titulo"],
                "grupo": "clausula", "nombre_grupo": f"Cláusula {cod.split('.')[0]}", "rol": "Todos",
                "descripcion": None, "cubierto_por": None, "en_gestitel": False, "gestitel_id": None,
                "ley_aplica": None, "ley_art": None, "ley_exp": None,
                "ev_esperada": c.get("evidencia_esperada"), "ev_minima": c.get("minimo"),
            })

        # 4b) Requisitos de brecha de GESTITEL (clausulas desglosadas)
        clausulas = {cod for cod, c in skill.items() if c.get("grupo") == "clausula"}
        brecha = json.load(open(BRECHA_JSON, encoding="utf-8"))["requisitos"]
        sin_clausula = [b["codigo"] for b in brecha if not clausula_de(b["codigo"], clausulas)]
        if sin_clausula:
            sys.exit("Requisitos de brecha sin cláusula en el catálogo: %s" % sin_clausula)
        cur.execute("DELETE FROM requisitos_brecha WHERE codigo <> ALL(%s)", ([b["codigo"] for b in brecha],))
        for b in brecha:
            cur.execute(
                """INSERT INTO requisitos_brecha (codigo, gestitel_id, clausula_soa, titulo, descripcion, requisito)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT (codigo) DO UPDATE SET gestitel_id = EXCLUDED.gestitel_id,
                       clausula_soa = EXCLUDED.clausula_soa, titulo = EXCLUDED.titulo,
                       descripcion = EXCLUDED.descripcion, requisito = EXCLUDED.requisito""",
                (b["codigo"], b["gestitel_id"], b["clausula_soa"], b["titulo"], b["descripcion"],
                 clausula_de(b["codigo"], clausulas)))

        # 5) Requisito -> expediente
        cur.execute("DELETE FROM requisito_expediente")
        sql_rel = "INSERT INTO requisito_expediente VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING"
        rel = guia["requisito_expediente"]
        for req, exps in rel.items():
            for e in exps:
                cur.execute(sql_rel, (req, e, "guia", "Guía de documentos ISO 27701:2025, tabla de %s" % e))
        # Controles 27001 que cubren un A.3 heredan sus expedientes
        for cod, d in a3.items():
            for e in rel.get(cod, []):
                cur.execute(sql_rel, (d["cubierto_por"], e, "equivalencia",
                                      "Cubre %s (equivalencia mostrada en la SOA de GESTITEL)" % cod))
        # El resto de controles 27001: programa de seguridad de 6.1.3 c) -> D16
        cur.execute("""SELECT codigo FROM requisitos r WHERE norma = 'ISO/IEC 27001:2022'
                       AND NOT EXISTS (SELECT 1 FROM requisito_expediente x WHERE x.requisito = r.codigo)
                       ORDER BY gestitel_id""")
        sin_rel = [r["codigo"] for r in cur.fetchall()]
        faltan = [c for c in sin_rel if c not in programa["controles"]]
        sobran = [c for c in programa["controles"] if c not in sin_rel]
        if faltan or sobran:
            sys.exit("programa_seguridad_6_1_3c.json no cuadra con la SOA. Sin tema: %s. Sobran: %s"
                     % (faltan, sobran))
        for cod in sin_rel:
            tema = programa["controles"][cod]
            cur.execute("UPDATE requisitos SET tema_programa = %s WHERE codigo = %s",
                        (programa["temas"][tema], cod))
            cur.execute(sql_rel, (cod, programa["expediente"], "norma",
                                  'ISO/IEC 27701:2025, 6.1.3 c): programa de seguridad, tema "%s"' % tema))

        cur.execute("SELECT norma, tipo, count(*) AS n FROM requisitos GROUP BY 1, 2 ORDER BY 1, 2")
        resumen = cur.fetchall()
        cur.execute("SELECT fuente, count(*) AS n FROM requisito_expediente GROUP BY 1 ORDER BY 1")
        rel_res = cur.fetchall()

    faltan_a3 = sorted(set(f"A.3.{i}" for i in range(3, 32)) - set(a3), key=lambda s: int(s.split(".")[2]))
    print(f"Expedientes: {len(guia['expedientes'])} | requisitos de brecha GESTITEL: {len(brecha)}")
    print(f"Controles en la SOA de GESTITEL: {len(soa)} | A.3 por equivalencia: {len(a3)} | cláusulas: {n_cla}")
    for r in resumen:
        print(f"  {r['norma']:<20} {r['tipo']:<9} {r['n']}")
    print("Relaciones requisito-expediente:", ", ".join(f"{r['fuente']}={r['n']}" for r in rel_res))
    print(f"Verificado contra la norma: {len(refs_27701)} referencias de la guía/skill existen en el texto; "
          f"los {len(programa['temas'])} temas de 6.1.3 c) aparecen literalmente.")
    if faltan_a3:
        print("AVISO: controles A.3 sin equivalencia en la SOA:", ", ".join(faltan_a3), file=sys.stderr)


if __name__ == "__main__":
    main()
