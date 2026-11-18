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
        self.texto(x + 14, y + 26, titulo, 19, "bold", "#444", "start", destino=self.capas)

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
        paso = round(tam * 1.3)
        alto_bloque = (tam + 3) + n * paso
        cy = y + h / 2 - alto_bloque / 2 + tam + 1
        self.texto(x + w / 2, cy, titulo, tam + 3, "bold", color_t)
        for i, l in enumerate(lineas):
            self.texto(x + w / 2, cy + 4 + (i + 1) * paso, l, tam, "normal",
                       "#e8eef5" if estilo == "clave" else "#444")

    def flecha(self, puntos, etiqueta=None, pos=None, punteada=False, color="#444", doble=False, tam=16, punta=True):
        d = "M" + " L".join(f"{px},{py}" for px, py in puntos)
        guion = ' stroke-dasharray="6 4"' if punteada else ""
        ini = ' marker-start="url(#pi)"' if doble else ""
        self.flechas.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.2"{guion}{ini}'
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
    c = Lienzo(1200, 1010)
    c.texto(600, 42, "Arquitectura del Agente de Evidencia y Auditoría", 30, "bold")
    T = 18  # subtítulo (el título usa T + 3)

    c.marco(20, 64, 1160, 112, "Actores")
    c.caja(60, 100, 280, 60, "Auditor / DPO", [], "actor", T)
    c.caja(460, 100, 280, 60, "Hosts MCP", [], "actor", T)
    c.caja(860, 100, 280, 60, "Otros agentes PIMS", [], "actor", T)

    c.marco(20, 200, 740, 124, "1. Interfaces")
    c.caja(60, 236, 280, 72, "Panel web + CLI", ["aprobación humana"], "det", T)
    c.caja(460, 236, 280, 72, "Servidor MCP", ["11 herramientas"], "det", T)

    c.marco(20, 350, 1160, 142, "2. Coordinación")
    c.caja(60, 388, 480, 88, "Orquestador LangGraph", ["3 grafos + puertas humanas (HITL)"], "clave", T)
    c.caja(580, 388, 260, 88, "Bus de eventos", ["entre agentes"], "evento", T)
    c.caja(880, 388, 260, 88, "Bandeja", ["vigila archivos nuevos"], "det", T)

    c.marco(20, 518, 1160, 124, "3. Herramientas")
    c.caja(60, 554, 580, 72, "herramientas.py", ["registrar · verificar · cobertura · informe"], "det", T)
    c.caja(680, 554, 220, 72, "Skill E1", ["SHA-256, custodia"], "det", T)
    c.caja(920, 554, 220, 72, "App E1", ["RAG + citas"], "det", T)

    c.marco(20, 668, 1160, 124, "4. IA local (Ollama)")
    c.caja(60, 704, 460, 72, "LLM qwen2.5:3b", ["clasifica, evalúa, redacta"], "ia", T)
    c.caja(720, 704, 420, 72, "Embeddings + FAISS", ["búsqueda en norma y evidencias"], "ia", T)

    c.marco(20, 818, 1160, 142, "5. Datos")
    c.caja(60, 852, 440, 94, "PostgreSQL", ["expediente, auditorías, bitácoras"], "datos", T, "cilindro")
    c.caja(560, 858, 260, 82, "Disco", ["archivos de evidencia"], "datos", T)
    c.caja(880, 858, 260, 82, "GESTITEL", ["import Excel"], "actor", T)

    c.flecha([(200, 160), (200, 236)])
    c.flecha([(600, 160), (600, 236)])
    c.flecha([(1000, 160), (1000, 336), (710, 336), (710, 388)], "eventos", pos=(1000, 270))
    c.flecha([(200, 308), (200, 388)])
    c.flecha([(560, 308), (560, 554)], "MCP", pos=(560, 506))
    c.flecha([(540, 432), (580, 432)], doble=True)
    c.flecha([(880, 432), (840, 432)])
    c.flecha([(300, 476), (300, 554)])
    c.flecha([(640, 590), (680, 590)])
    c.flecha([(900, 590), (920, 590)])
    c.flecha([(290, 626), (290, 704)])
    c.flecha([(1030, 626), (1030, 704)])
    c.flecha([(60, 600), (27, 600), (27, 900), (60, 900)])
    c.flecha([(620, 626), (620, 858)], "evidencias", pos=(620, 742))
    c.flecha([(820, 899), (880, 899)])

    c.texto(600, 992, "azul = determinista · amarillo = IA local · verde = eventos · morado = datos · gris = externo",
            16, "normal", "#555")
    c.guardar("arquitectura_entregable2.svg")


# ===================================================================== FLUJO
def flujo():
    c = Lienzo(1200, 1100)
    c.texto(600, 42, "Flujo del Agente de Evidencia y Auditoría", 30, "bold")
    T = 19
    centros = (200, 600, 1000)

    disparadores = [("Panel / CLI", "inicio"), ("Incidente (Agente 6)", "evento"), ("Archivo nuevo", "evento")]
    for cx, (t, e) in zip(centros, disparadores):
        c.caja(cx - 150, 72, 300, 56, t, [], e, T, "pildora")
        c.flecha([(cx, 128), (cx, 166)])
    c.caja(60, 166, 1080, 60, "Orquestador LangGraph", [], "clave", T)

    columnas = [
        ("Auditoría interna (9.2)", [
            ("Planificar", "det", "rect"),
            ("Verificar integridad", "det", "rect"),
            ("Matriz de cobertura", "det", "rect"),
            ("Evaluar pertinencia", "ia", "rect"),
            ("Redactar hallazgos", "ia", "rect"),
            ("Aprueba el auditor", "hitl", "hex"),
            ("Informe + plan de acción", "det", "rect"),
            ("Auditoría completada", "evento", "pildora"),
        ]),
        ("Incidente (A.3.14)", [
            ("Recibir evento", "det", "rect"),
            ("Registrar incidente", "det", "rect"),
            ("Verificar integridad", "det", "rect"),
            ("Buscar relacionadas", "ia", "rect"),
            ("Aprueba el DPO", "hitl", "hex"),
            ("Informe de incidente", "det", "rect"),
            ("Aviso al Agente 6", "evento", "pildora"),
        ]),
        ("Bandeja", [
            ("Tomar archivos", "det", "rect"),
            ("Clasificar", "ia", "rect"),
            ("Aprobación", "hitl", "hex"),
            ("Registrar evidencia", "det", "rect"),
            ("Mover archivo", "det", "rect"),
            ("Evidencia registrada", "evento", "pildora"),
        ]),
    ]
    Y0, PASO, H, W = 320, 92, 56, 300
    for cx, (titulo, pasos) in zip(centros, columnas):
        c.marco(cx - 180, 262, 360, 790, titulo)
        c.flecha([(cx, 226), (cx, 262)])
        for i, (t, e, f) in enumerate(pasos):
            y = Y0 + i * PASO
            c.caja(cx - W / 2, y, W, H, t, [], e, T, f)
            if i:
                et = "aprobado" if pasos[i - 1][1] == "hitl" else None
                c.flecha([(cx, y - PASO + H), (cx, y)], et,
                         pos=(cx + 60, y - (PASO - H) / 2 + 5) if et else None)

    c.texto(600, 1082, "azul = determinista · amarillo = IA local · rojo = decisión humana · verde = evento",
            16, "normal", "#555")
    c.guardar("flujo_entregable2.svg")


if __name__ == "__main__":
    arquitectura()
    flujo()


