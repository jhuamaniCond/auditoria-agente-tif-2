"""Genera los diagramas del Entregable 2 (arquitectura y flujo) como SVG.

Uso:  python generar_diagramas.py
Salida: arquitectura_entregable2.svg y flujo_entregable2.svg en esta carpeta.
Para PNG: abrir el SVG en Chrome/Edge headless (ver README.md).
"""
import os
from xml.sax.saxutils import escape

AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTE = "Segoe UI, Arial, Helvetica, sans-serif"

ESTILOS = {
    "det": ("#dae8fc", "#6c8ebf"),
    "ia": ("#fff2cc", "#b8952a"),
    "hitl": ("#f8cecc", "#b85450"),
    "alerta": ("#ffe6cc", "#d79b00"),
    "evento": ("#d5e8d4", "#82b366"),
    "datos": ("#e1d5e7", "#9673a6"),
    "actor": ("#f5f5f5", "#666666"),
    "clave": ("#1f4e79", "#0b2540"),
    "inicio": ("#ffffff", "#333333"),
}


class Lienzo:
    def __init__(self, ancho, alto):
        self.ancho, self.alto = ancho, alto
        self.capas = []   # fondo
        self.flechas = []
        self.nodos = []

    # ---------------------------------------------------------------- primitivas
    def texto(self, x, y, t, tam=13, peso="normal", color="#222", anchor="middle", italica=False, destino=None):
        estilo = ' font-style="italic"' if italica else ""
        (destino if destino is not None else self.nodos).append(
            f'<text x="{x}" y="{y}" font-family="{FUENTE}" font-size="{tam}" font-weight="{peso}" '
            f'fill="{color}" text-anchor="{anchor}"{estilo}>{escape(t)}</text>')

    def marco(self, x, y, w, h, titulo, color="#8a8a8a"):
        self.capas.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#fbfbfb" '
            f'stroke="{color}" stroke-width="1.5" stroke-dasharray="7 5"/>')
        self.texto(x + 14, y + 22, titulo, 15, "bold", "#444", "start", destino=self.capas)

    def caja(self, x, y, w, h, titulo, lineas=(), estilo="det", tam=12, forma="rect"):
        fill, stroke = ESTILOS[estilo]
        color_t = "#ffffff" if estilo == "clave" else "#1a1a1a"
        if forma == "hex":
            d = 16
            pts = f"{x+d},{y} {x+w-d},{y} {x+w},{y+h/2} {x+w-d},{y+h} {x+d},{y+h} {x},{y+h/2}"
            self.nodos.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        elif forma == "rombo":
            cx, cy = x + w / 2, y + h / 2
            pts = f"{cx},{y} {x+w},{cy} {cx},{y+h} {x},{cy}"
            self.nodos.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        elif forma == "pildora":
            self.nodos.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{fill}" '
                              f'stroke="{stroke}" stroke-width="2"/>')
        elif forma == "cilindro":
            e = 12
            self.nodos.append(
                f'<path d="M{x},{y+e} A{w/2},{e} 0 0 1 {x+w},{y+e} L{x+w},{y+h-e} A{w/2},{e} 0 0 1 {x},{y+h-e} Z" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
                f'<path d="M{x},{y+e} A{w/2},{e} 0 0 0 {x+w},{y+e}" fill="none" stroke="{stroke}" stroke-width="2"/>')
            y += e
            h -= e
        else:
            self.nodos.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" '
                              f'stroke="{stroke}" stroke-width="2"/>')
        n = len(lineas)
        alto_bloque = (tam + 3) + n * (tam + 3)
        cy = y + h / 2 - alto_bloque / 2 + tam + 1
        self.texto(x + w / 2, cy, titulo, tam + 1, "bold", color_t)
        for i, l in enumerate(lineas):
            self.texto(x + w / 2, cy + (i + 1) * (tam + 3), l, tam, "normal",
                       "#ffffff" if estilo == "clave" else "#333")

    def flecha(self, puntos, etiqueta=None, pos=None, punteada=False, color="#444", doble=False, tam=11, punta=True):
        d = "M" + " L".join(f"{px},{py}" for px, py in puntos)
        guion = ' stroke-dasharray="6 4"' if punteada else ""
        ini = ' marker-start="url(#pi)"' if doble else ""
        self.flechas.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.7"{guion}{ini}'
                            + (' marker-end="url(#pf)"' if punta else '') + '/>')
        if etiqueta:
            if pos is None:
                (x1, y1), (x2, y2) = puntos[len(puntos) // 2 - 1], puntos[len(puntos) // 2]
                pos = ((x1 + x2) / 2, (y1 + y2) / 2)
            ancho = len(etiqueta) * tam * 0.56 + 10
            self.flechas.append(f'<rect x="{pos[0]-ancho/2}" y="{pos[1]-tam+1}" width="{ancho}" height="{tam+6}" '
                                f'rx="3" fill="#ffffff" fill-opacity="0.95"/>')
            self.texto(pos[0], pos[1] + 3, etiqueta, tam, "normal", "#333", destino=self.flechas, italica=True)

    def leyenda(self, x, y, elementos):
        for i, (estilo, t) in enumerate(elementos):
            fill, stroke = ESTILOS[estilo]
            yy = y + i * 24
            self.nodos.append(f'<rect x="{x}" y="{yy}" width="26" height="16" rx="3" fill="{fill}" '
                              f'stroke="{stroke}" stroke-width="2"/>')
            self.texto(x + 36, yy + 13, t, 12, "normal", "#333", "start")

    def guardar(self, nombre):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.ancho}" height="{self.alto}" '
               f'viewBox="0 0 {self.ancho} {self.alto}">'
               '<defs>'
               '<marker id="pf" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
               'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#444"/></marker>'
               '<marker id="pi" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
               'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#444"/></marker>'
               '</defs>'
               f'<rect width="100%" height="100%" fill="#ffffff"/>'
               + "".join(self.capas) + "".join(self.flechas) + "".join(self.nodos) + "</svg>")
        ruta = os.path.join(AQUI, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(svg)
        print("escrito", ruta)


# ===================================================================== ARQUITECTURA
def arquitectura():
    c = Lienzo(1700, 1360)
    c.texto(850, 38, "Arquitectura del Agente de Evidencia y Auditoría — Entregable 2 (Grupo 6)", 24, "bold")
    c.texto(850, 64, "PIMS multiagente ISO/IEC 27701:2025 (9.1 · 9.2 · A.3.14) aplicado a la UNSA — ejecución 100 % local",
            14, "normal", "#555")

    # ---- Actores
    c.marco(20, 84, 1660, 120, "Actores")
    c.caja(50, 116, 260, 72, "Auditor interno", ["decide hallazgos e informe", "(puertas HITL)"], "actor")
    c.caja(340, 116, 280, 72, "DPO / Oficial de Datos Personales", ["valida el expediente", "de incidentes"], "actor")
    c.caja(800, 116, 330, 72, "Hosts MCP", ["Claude Desktop · Claude Code · IDE", "orquestador del PIMS"], "actor")
    c.caja(1160, 116, 240, 72, "Agentes 1, 2, 3, 5, 7, 8", ["otros grupos del PIMS", "publican evidencia.nueva"], "actor")
    c.caja(1420, 116, 240, 72, "Agente 6 — Incidentes", ["(simulador) · alerta SIEM", "incidente.detectado"], "actor")

    # ---- Capa 1
    c.marco(20, 236, 1660, 190, "1. Presentación y gobernanza")
    c.caja(50, 270, 400, 140, "Panel web Flask — servidor_web.py :5000",
           ["/  → App AUDITA-PIMS (Entregable 1)", "/agente → panel: línea de tiempo en vivo,",
            "aprobación humana, informes y bitácoras", "/api/agente/* → API REST (ejecuciones,",
            "aprobar, incidente, bandeja, bitácora)"], "det")
    c.caja(480, 270, 250, 140, "CLI — cli_agente.py",
           ["auditoria [--rapido]", "incidente \"…\" · bandeja [--auto]", "listar · estado ID",
            "aprobar ID --auditor", "grafo auditoria_interna"], "det")
    c.caja(760, 270, 560, 140, "Orquestador LangGraph — orquestador.py",
           ["StateGraph: auditoria_interna · incidente · bandeja",
            "Puertas HITL con interrupt() → reanuda con la decisión humana",
            "Checkpointer PostgresSaver (SqliteSaver si PIMS_BACKEND=archivos)",
            "Modo rápido sin LLM · iniciar / obtener / listar / aprobar",
            "Al aprobar vuelca auditorías, hallazgos y acciones (GESTITEL)"], "clave")
    c.caja(1380, 270, 280, 140, "Registro de decisiones",
           ["decisiones_humanas", "(auditor / DPO, motivo, actor)", "ejecuciones + instantáneas",
            "por paso del grafo"], "evento")

    # ---- Capa 2
    c.marco(20, 458, 1660, 180, "2. Comunicación y automatización")
    c.caja(50, 492, 520, 130, "Servidor MCP evidencias-pims — servidor_mcp.py",
           ["SDK oficial MCP · stdio o HTTP 127.0.0.1:8765/mcp",
            "11 tools · resources pims://catalogo, norma://control/{ref}",
            "prompt auditoria_interna · informe siempre PRELIMINAR",
            "decidir_pertinencia NO publicada (solo humana)",
            "bitácora MCP encadenada por SHA-256"], "det")
    c.caja(600, 492, 580, 130, "Bus de eventos — coordinacion.py",
           ["Entrada: incidente.detectado · auditoria.solicitada · evidencia.nueva",
            "Salida: aprobacion.requerida · integridad.alterada ·",
            "auditoria.completada · incidente.documentado · evidencia.registrada",
            "Simulador del Agente 6 (Incidentes)",
            "carga mínima: IDs y referencias, nunca PII"], "evento")
    c.caja(1210, 492, 450, 130, "Automatización — bandeja.py",
           ["vigilar(): datos/bandeja_entrada cada 10 s",
            "→ grafo bandeja (auto_registrar opcional)",
            "verificar_periodica(): integridad cada 24 h",
            "→ publica integridad.alterada si hay cambios"], "det")

    # ---- Capa 3
    c.marco(20, 670, 1660, 210, "3. Herramientas (contrato JSON común) y reutilización del Entregable 1")
    c.caja(50, 704, 640, 160, "herramientas.py + nucleo.py",
           ["Deterministas: listar_proyectos · estado_expediente · registrar ·",
            "verificar_integridad · matriz_cobertura · generar_informe · exportar_gestitel",
            "IA local: clasificar · buscar · evaluar_pertinencia ·",
            "redactar_hallazgo · preguntar",
            "Solo humana: decidir_pertinencia",
            "nucleo.py importa la skill y la app E1 sin copiarlas · PIMS_BACKEND"], "det")
    c.caja(720, 704, 460, 160, "Skill E1 — evidencia-auditoria-pims",
           ["scripts/evidencia.py: SHA-256, cadena de custodia,", "integridad, matriz de cobertura",
            "references/controles_27701.json (catálogo)", "references/criterios_evidencia.md",
            "assets/plantilla_hallazgo.md", "Reglas duras: no inventar evidencia, no PII"], "det")
    c.caja(1210, 704, 450, 160, "App E1 — AUDITA-PIMS",
           ["asistente.py (RAG + citas)", "llm_local.py (cliente Ollama)",
            "revisiones (pertinencia propuesta / decidida)", "norma.py · extraer_norma.py", "evidencia_api.py"], "det")

    # ---- Capa 4
    c.marco(20, 912, 1660, 130, "4. IA local (Ollama, sin servicios externos)")
    c.caja(50, 946, 380, 80, "LLM qwen2.5:3b", ["clasificación, pertinencia, hallazgos,", "respuestas del asistente"], "ia")
    c.caja(460, 946, 380, 80, "Embeddings nomic-embed-text", ["vectoriza norma, conocimiento", "y evidencias"], "ia")
    c.caja(870, 946, 380, 80, "Índices FAISS", ["indice_conocimiento (común)", "indice_evidencias (por proyecto)"], "ia")
    c.caja(1280, 946, 380, 80, "Texto ISO/IEC 27701:2025", ["OCR con página (ISOS/texto)", "criterio de auditoría citado"], "ia")

    # ---- Capa 5
    c.marco(20, 1074, 1660, 230, "5. Persistencia")
    c.caja(50, 1108, 820, 182, "PostgreSQL 16 (Docker) — base pims_auditoria · BD/schema.sql · almacen_pg.py",
           ["Catálogo: expedientes · requisitos · requisito_expediente · requisitos_brecha · gestitel_codigos",
            "Expediente: proyectos · soa_evaluaciones · evidencias · evidencia_requisito ·",
            "cadena_custodia · revisiones_pertinencia",
            "Auditoría (modelo GESTITEL): auditorias · checklist_items · hallazgos ·",
            "hallazgo_evidencia · acciones · v_auditoria_avance · v_export_auditorias_gestitel",
            "Trazabilidad: decisiones_humanas · eventos_agentes · bitacora_mcp ·",
            "ejecuciones · ejecucion_instantaneas · checkpoints* (PostgresSaver)",
            "Triggers de solo inserción en custodia y bitácoras"], "datos", 12, "cilindro")
    c.caja(900, 1108, 220, 80, "pgAdmin 4 :5050", ["consulta visual de la BD"], "datos")
    c.caja(900, 1210, 220, 80, "GESTITEL", ["unsa.27k.pe · import Excel", "(exportar_gestitel.py)"], "actor")
    c.caja(1150, 1108, 510, 182, "Disco — Entregable-2/datos",
           ["documentos_unsa/ (PDF públicos reales + fuentes.json)",
            "proyectos/unsa/expediente/archivos/ (EV-XXXX)",
            "bandeja_entrada/ → procesados/ · rechazados/",
            "salidas/ informes .md · incidentes · Excel GESTITEL",
            "índices FAISS",
            "PIMS_BACKEND=archivos: JSON/JSONL + SqliteSaver"], "datos")

    # ---- Flechas entre capas
    c.flecha([(180, 188), (180, 270)], "usa")
    c.flecha([(480, 188), (480, 212), (300, 212), (300, 270)], "aprueba", pos=(390, 212))
    c.flecha([(965, 188), (965, 226), (465, 226), (465, 492)], "MCP (stdio / HTTP)", pos=(700, 226))
    # agentes 1-8 y agente 6 -> bus de eventos por el pasillo entre orquestador y registro
    c.flecha([(1280, 188), (1280, 220), (1350, 220)], punta=False)
    c.flecha([(1540, 188), (1540, 220), (1350, 220), (1350, 446), (1130, 446), (1130, 492)],
             "evidencia.nueva · incidente.detectado", pos=(1250, 446))
    c.flecha([(450, 340), (480, 340)])
    c.flecha([(730, 340), (760, 340)])
    c.flecha([(1320, 340), (1380, 340)])
    c.flecha([(1000, 410), (1000, 492)], "publica / consume", pos=(1000, 470), doble=True)
    c.flecha([(1600, 492), (1600, 436), (1290, 436), (1290, 410)], "dispara grafos", pos=(1500, 436))
    c.flecha([(310, 622), (310, 704)], "tools → herramientas")
    c.flecha([(800, 410), (800, 432), (585, 432), (585, 704)], "nodos → herramientas", pos=(585, 660))
    c.flecha([(690, 784), (720, 784)])
    c.flecha([(1180, 784), (1210, 784)])
    c.flecha([(1430, 864), (1430, 896), (240, 896), (240, 946)], "IA local", pos=(830, 896))
    c.flecha([(650, 896), (650, 946)])
    c.flecha([(1060, 896), (1060, 946)])
    c.flecha([(1470, 896), (1470, 946)])
    c.flecha([(50, 850), (34, 850), (34, 1200), (50, 1200)], "lee / escribe", pos=(60, 1060))
    c.flecha([(1180, 850), (1195, 850), (1195, 908), (1265, 908), (1265, 1090), (1320, 1090), (1320, 1108)],
             "archivos de evidencia", pos=(1265, 1058))
    c.flecha([(870, 1148), (900, 1148)], doble=True)
    c.flecha([(860, 1250), (900, 1250)])


    c.texto(850, 1340, "Leyenda:  azul = componente determinista · amarillo = IA local · verde = eventos / registro · "
            "morado = datos · gris = actores externos · azul oscuro = orquestador", 12, "normal", "#555")
    c.guardar("arquitectura_entregable2.svg")


# ===================================================================== FLUJO
def flujo():
    c = Lienzo(1700, 1612)
    c.texto(850, 38, "Diagrama de flujo del Agente de Evidencia y Auditoría — Entregable 2 (Grupo 6)", 24, "bold")
    c.texto(850, 64, "Disparadores → orquestador LangGraph → grafos auditoria_interna · incidente · bandeja → puertas humanas → salidas",
            14, "normal", "#555")

    # ---- Disparadores
    c.caja(40, 90, 300, 62, "Panel /agente o CLI", ["botón «Iniciar auditoría» · cli_agente.py"], "inicio", forma="pildora")
    c.caja(370, 90, 300, 62, "Evento auditoria.solicitada", ["orquestador PIMS / DPO"], "evento", forma="pildora")
    c.caja(700, 90, 300, 62, "Evento incidente.detectado", ["Agente 6 (simulador)"], "evento", forma="pildora")
    c.caja(1030, 90, 300, 62, "Archivo en bandeja_entrada", ["evidencia.nueva · vigilar() 10 s"], "evento", forma="pildora")
    c.caja(1360, 90, 300, 62, "Temporizador 24 h", ["verificar_periodica()"], "inicio", forma="pildora")

    c.caja(500, 190, 700, 64, "Orquestador LangGraph — iniciar(tipo, proyecto=\"unsa\", parámetros)",
           ["crea la ejecución AUD-…, guarda el estado tras cada paso (PostgreSQL)"], "clave")
    for x in (190, 520):
        c.flecha([(x, 152), (x, 172), (700, 172), (700, 190)])
    c.flecha([(850, 152), (850, 190)])
    c.flecha([(1180, 152), (1180, 172), (1000, 172), (1000, 190)])
    # temporizador -> verificación directa
    c.caja(1430, 190, 230, 64, "verificar_integridad", ["si hay cambios → evento", "integridad.alterada"], "alerta")
    c.flecha([(1510, 152), (1510, 190)])

    # ---- Columnas
    c.marco(20, 290, 640, 1100, "Grafo auditoria_interna (cláusula 9.2)")
    c.marco(680, 290, 470, 1100, "Grafo incidente (A.3.11 · A.3.12 · A.3.14)")
    c.marco(1170, 290, 510, 1100, "Grafo bandeja (registro automático)")
    c.flecha([(600, 254), (600, 272), (240, 272), (240, 330)], "tipo = auditoria_interna", pos=(400, 272))
    c.flecha([(850, 254), (850, 330)], "tipo = incidente", pos=(850, 285))
    c.flecha([(1100, 254), (1100, 272), (1420, 272), (1420, 330)], "tipo = bandeja", pos=(1300, 272))

    # -- auditoria_interna
    X, W = 80, 320
    cx = X + W / 2
    pasos = [
        (330, "planificar", ["estado_expediente: rol, vigencia,", "fecha de corte, nº de evidencias"], "det", "rect"),
        (430, "verificar_integridad", ["recalcula SHA-256 y cadena de custodia"], "det", "rect"),
        (520, "¿expediente íntegro?", [], "det", "rombo"),
        (630, "matriz_cobertura", ["estado por control (38 aplicables) y %"], "det", "rect"),
        (720, "evaluar_pertinencia", ["IA: cumple / parcial / no cumple", "(determinista en modo rápido)"], "ia", "rect"),
        (820, "priorizar", ["clasificación propuesta, criticidad,", "tipo de requisito → puntaje"], "det", "rect"),
        (920, "redactar_hallazgos", ["IA para los prioritarios (max 3),", "resto determinista · PRELIMINAR"], "ia", "rect"),
        (1020, "PUERTA HITL aprobacion_auditor", ["interrupt() · evento aprobacion.requerida"], "hitl", "hex"),
        (1130, "generar_informe", ["informe validado → datos/salidas/"], "det", "rect"),
        (1220, "plan_accion", ["prioridad, acción, responsable, plazo (10.2)"], "det", "rect"),
        (1310, "Fin · auditoria.completada", ["vuelca auditorias · hallazgos · acciones"], "evento", "pildora"),
    ]
    alturas = {"rect": 64, "rombo": 76, "hex": 70, "pildora": 62}
    ys = []
    for y, t, l, e, f in pasos:
        h = alturas[f]
        c.caja(X, y, W, h, t, l, e, forma=f)
        ys.append((y, h))
    for i in range(len(pasos) - 1):
        if i in (2, 7):
            continue
        y0 = ys[i][0] + ys[i][1]
        y1 = ys[i + 1][0]
        c.flecha([(cx, y0), (cx, y1)])
    # rombo
    c.flecha([(cx, 596), (cx, 630)], "sí", pos=(cx + 16, 614))
    c.caja(430, 516, 210, 84, "alerta_integridad",
           ["evento integridad.alterada", "evidencias → Comprometidas", "(la auditoría continúa)"], "alerta")
    c.flecha([(X + W, 558), (430, 558)], "no", pos=(415, 552))
    c.flecha([(535, 600), (535, 662), (X + W, 662)])
    # puerta
    c.flecha([(cx, 1090), (cx, 1130)], "aprobada", pos=(cx + 34, 1110))
    c.caja(430, 1022, 210, 66, "Fin: rechazo registrado", ["sin informe validado"], "inicio", forma="pildora")
    c.flecha([(X + W, 1055), (430, 1055)], "rech.", pos=(415, 1046), tam=10)
    c.caja(430, 1130, 210, 66, "exportar_gestitel", ["Excel con formato", "GESTITEL (opcional)"], "det")
    c.flecha([(X + W, 1252), (535, 1252), (535, 1196)], punteada=True)
    c.caja(430, 1300, 210, 74, "Auditor interno", ["aprueba / rechaza y acepta", "cada propuesta (decidir_", "pertinencia)"], "actor")
    c.flecha([(430, 1337), (415, 1337), (415, 1078), (390, 1078)], punteada=True)

    # -- incidente
    X2, W2 = 715, 300
    cx2 = X2 + W2 / 2
    pasos2 = [
        (330, "recibir_evento", ["valida incidente.detectado"], "det", "rect"),
        (430, "registrar_incidente", ["reporte como evidencia A.3.11/A.3.12", "SHA-256 + cadena de custodia"], "det", "rect"),
        (530, "verificar_integridad", ["del expediente tras el registro"], "det", "rect"),
        (630, "buscar_relacionadas", ["RAG: plan de respuesta, políticas,", "evidencias previas"], "ia", "rect"),
        (740, "PUERTA HITL aprobacion_dpo", ["interrupt() · aprobacion.requerida"], "hitl", "hex"),
        (860, "informe_incidente", ["reporte en salidas/incidentes/"], "det", "rect"),
        (960, "Evento incidente.documentado", ["al Agente 6"], "evento", "pildora"),
        (1060, "Agente 6 notifica", ["a la autoridad y a los titulares", "(fuera del Agente 4, D.S. 016-2024-JUS)"], "actor", "rect"),
    ]
    ys2 = []
    for y, t, l, e, f in pasos2:
        h = alturas[f]
        c.caja(X2, y, W2, h, t, l, e, forma=f)
        ys2.append((y, h))
    for i in range(len(pasos2) - 1):
        y0 = ys2[i][0] + ys2[i][1]
        y1 = ys2[i + 1][0]
        et = "aprobada" if i == 4 else None
        c.flecha([(cx2, y0), (cx2, y1)], et, pos=(cx2 + 34, (y0 + y1) / 2) if et else None)
    c.caja(1030, 742, 105, 66, "Fin", ["rechazo", "registrado"], "inicio", forma="pildora")
    c.flecha([(X2 + W2, 775), (1030, 775)])
    c.texto(1022, 766, "rech.", 11, "normal", "#333", "end", italica=True)
    c.caja(715, 1170, 300, 66, "DPO / Oficial de Datos Personales", ["valida el expediente del incidente"], "actor")
    c.flecha([(1015, 1203), (1080, 1203), (1080, 830), (980, 830), (980, 810)], punteada=True)

    # -- bandeja
    X3, W3 = 1210, 300
    cx3 = X3 + W3 / 2
    c.caja(X3, 330, W3, 64, "tomar_archivos", ["lee datos/bandeja_entrada"], "det")
    c.caja(X3, 430, W3, 76, "¿hay archivos?", [], "det", forma="rombo")
    c.caja(1540, 436, 120, 62, "Fin", ["bandeja vacía"], "inicio", forma="pildora")
    c.caja(X3, 550, W3, 64, "clasificar", ["IA: controles, tipo, título, fecha", "(no registra)"], "ia")
    c.caja(X3, 650, W3, 70, "PUERTA HITL aprobacion_bandeja", ["ligera · omitible con auto_registrar"], "hitl", forma="hex")
    c.caja(X3, 770, W3, 64, "registrar", ["SHA-256 + cadena de custodia", "+ índice FAISS (RAG)"], "det")
    c.caja(X3, 880, W3, 64, "mover", ["procesados/ o rechazados/"], "det")
    c.caja(X3, 980, W3, 62, "Evento evidencia.registrada", ["al resto de agentes"], "evento", forma="pildora")
    c.flecha([(cx3, 394), (cx3, 430)])
    c.flecha([(X3 + W3, 468), (1540, 468)], "no", pos=(1525, 460))
    c.flecha([(cx3, 506), (cx3, 550)], "sí", pos=(cx3 + 14, 530))
    c.flecha([(cx3, 614), (cx3, 650)])
    c.flecha([(cx3, 720), (cx3, 770)], "aceptados", pos=(cx3 + 38, 745))
    c.flecha([(X3 + W3, 685), (1590, 685), (1590, 912), (X3 + W3, 912)], "rechazados", pos=(1590, 800))
    c.flecha([(cx3, 834), (cx3, 880)])
    c.flecha([(cx3, 944), (cx3, 980)])
    c.caja(X3, 1090, W3, 110, "Nota", ["registrar ≠ control cumplido:", "solo prueba existencia, fecha",
                                        "e integridad. La pertinencia la", "decide el auditor en la auditoría."], "actor")

    # ---- Persistencia común
    c.marco(20, 1410, 1660, 150, "Persistencia y trazabilidad comunes (PostgreSQL pims_auditoria · PIMS_BACKEND=archivos como respaldo)")
    items = [
        ("ejecuciones + instantáneas", ["estado tras cada nodo", "(línea de tiempo del panel)"]),
        ("checkpoints* (PostgresSaver)", ["reanuda tras interrupt()", "aunque el proceso reinicie"]),
        ("decisiones_humanas", ["auditor / DPO, decisión,", "comentario, actor"]),
        ("eventos_agentes · bitacora_mcp", ["eventos del bus y llamadas", "MCP encadenadas (SHA-256)"]),
        ("evidencias · cadena_custodia", ["registro, verificación y", "revisión de pertinencia"]),
    ]
    for i, (t, l) in enumerate(items):
        c.caja(45 + i * 328, 1446, 305, 96, t, l, "datos")

    c.texto(850, 1594, "Leyenda:  azul = paso determinista · amarillo = IA local (qwen2.5:3b / FAISS) · rojo = puerta humana (HITL) · "
            "naranja = alerta · verde = evento del bus · morado = datos · línea punteada = decisión humana", 12, "normal", "#555")
    c.guardar("flujo_entregable2.svg")


if __name__ == "__main__":
    arquitectura()
    flujo()
