# -*- coding: utf-8 -*-
"""
Dibuja las figuras 1 (arquitectura) y 2 (flujo de la skill) del informe con
matplotlib, en blanco, negro y grises, sin sombras. Salida en esta carpeta:
arquitectura.png y flujo_skill.png.

    pip install matplotlib
    python informe/figuras/dibujar_figuras.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
plt.rcParams["font.family"] = "DejaVu Sans"
GRIS = "#6b6b6b"
GRIS_CLARO = "#ececec"


def caja(ax, x, y, w, h, texto, grueso=False, fondo="white", tam=9, negrita=False):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fondo,
                           edgecolor="black" if grueso else GRIS,
                           linewidth=2.4 if grueso else 0.9))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=tam,
            fontweight="bold" if negrita or grueso else "normal", wrap=True)


def flecha(ax, x1, y1, x2, y2, texto=None, color=GRIS, ancho=0.9, tam=7.5, desp=(0, 0)):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=10,
                                 color=color, linewidth=ancho))
    if texto:
        ax.text((x1 + x2) / 2 + desp[0], (y1 + y2) / 2 + desp[1], texto, fontsize=tam,
                color=color, ha="center", va="center",
                bbox=dict(facecolor="white", edgecolor="none", pad=1))


def franja(ax, y, h, titulo):
    ax.add_patch(Rectangle((0.2, y), 15.6, h, facecolor=GRIS_CLARO, edgecolor="none"))
    ax.text(0.35, y + h - 0.22, titulo, fontsize=9, fontweight="bold", va="top")


# --------------------------------------------------------------------------
def arquitectura():
    fig, ax = plt.subplots(figsize=(12, 7.2))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.6)
    ax.axis("off")

    franja(ax, 8.0, 1.45, "Capa de gobernanza")
    caja(ax, 1.0, 8.15, 4.0, 0.75, "Orquestador")
    caja(ax, 6.0, 8.15, 4.0, 0.75, "Registro de decisiones")
    caja(ax, 11.0, 8.15, 4.4, 0.75, "Panel de aprobación humana\n(DPO / auditor interno)")

    franja(ax, 7.0, 0.75, "")
    ax.text(8.0, 7.37, "Bus MCP (JSON-RPC 2.0)", ha="center", va="center", fontsize=9,
            fontweight="bold")

    franja(ax, 3.0, 3.75, "Capa de agentes especializados")
    nombres = [["Inventario\nde datos", "Evaluación\nde riesgos", "Controles\ny SoA", None],
               ["Derechos\n(DSAR)", "Incidentes\ny brechas", "Terceros\n(DPA)", "Formación\ny conciencia"]]
    w, h = 3.2, 1.0
    xs = [0.8, 4.6, 8.4, 12.2]
    ys = [5.2, 3.35]
    origenes = []
    for fila, y in zip(nombres, ys):
        for x, nombre in zip(xs, fila):
            if nombre:
                caja(ax, x, y, w, h, nombre)
                origenes.append((x + w / 2, y + h / 2))
    # El agente del Grupo 6 ocupa la esquina superior derecha
    gx, gy = xs[3], ys[0]
    caja(ax, gx, gy, w, h, "Evidencia y Auditoría\n(Grupo 6)", grueso=True)
    # Canal de evidencias entre las dos filas: cada agente baja/sube a la linea
    # y la linea entra por debajo a la caja del Grupo 6.
    y_canal = 4.78
    for (ox, oy) in origenes:
        borde = oy - h / 2 if oy > y_canal else oy + h / 2
        ax.plot([ox, ox], [borde, y_canal], color="#9a9a9a", linewidth=0.8)
    centro_x = gx + w / 2
    ax.plot([xs[0] + w / 2, centro_x], [y_canal, y_canal], color="#9a9a9a", linewidth=0.8)
    flecha(ax, centro_x, y_canal, centro_x, gy, color="black", ancho=1.2)
    ax.text(8.0, y_canal, "evidencias de los demás agentes", fontsize=8, color=GRIS,
            ha="center", va="center", bbox=dict(facecolor=GRIS_CLARO, edgecolor="none", pad=1))

    # hallazgos hacia el panel humano
    flecha(ax, gx + w / 2, gy + h, 13.2, 8.15, "hallazgos\npreliminares", color="black",
           ancho=1.4, desp=(0.95, 0))

    franja(ax, 0.2, 2.5, "Capa de herramientas y datos (el Agente de Evidencia accede "
                         "mediante evidencia.py)")
    caja(ax, 0.8, 0.5, 3.4, 1.4, "PostgreSQL\n(PII, evidence_store)", tam=8.5)
    caja(ax, 4.6, 0.5, 4.2, 1.4, "Expediente de evidencias\nregistro_evidencias.json\n"
         "cadena_custodia.log", tam=8.5)
    caja(ax, 9.2, 0.5, 3.0, 1.4, "Catálogo\ncontroles_27701.json", tam=8.5)
    caja(ax, 12.6, 0.5, 2.8, 1.4, "Modelo de\nlenguaje (LLM)", tam=8.5)

    fig.savefig(os.path.join(AQUI, "arquitectura.png"), dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


# --------------------------------------------------------------------------
def flujo_skill():
    fig, ax = plt.subplots(figsize=(9, 11.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0.9, 15.5)
    ax.axis("off")

    pasos = [
        ("1", "Entender el encargo", "rol y periodo", "Modelo", ""),
        ("2", "Clasificar y registrar", "evidencia.py registrar  ·  SHA-256", "Modelo + Script",
         "controles_27701.json"),
        ("3", "Verificar integridad", "evidencia.py verificar", "Script", ""),
        ("4", "Matriz de cobertura", "evidencia.py cobertura\n+ revisión de pertinencia",
         "Modelo + Script", "controles_27701.json\ncriterios_evidencia.md"),
        ("5", "Hallazgos preliminares", "plantilla_hallazgo.md", "Modelo",
         "criterios_evidencia.md"),
        ("6", "Entregar al auditor", "alertas, resumen, hallazgos", "Modelo", ""),
    ]
    x, w, h = 3.2, 5.0, 1.45
    paso_y = 2.05
    y0 = 13.4
    ys = []
    for i, (n, titulo, detalle, quien, lee) in enumerate(pasos):
        y = y0 - i * paso_y
        ys.append(y)
        ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor="black",
                               linewidth=1.1))
        ax.text(x + 0.25, y + h - 0.32, n, fontsize=13, fontweight="bold", va="center")
        ax.text(x + w / 2 + 0.2, y + h - 0.45, titulo, fontsize=11, fontweight="bold",
                ha="center", va="center")
        ax.text(x + w / 2 + 0.2, y + 0.45, detalle, fontsize=8.5, ha="center",
                va="center", family="DejaVu Sans Mono")
        ax.add_patch(Rectangle((0.3, y + 0.42), 2.4, 0.6, facecolor=GRIS_CLARO,
                               edgecolor="none"))
        ax.text(1.5, y + 0.72, quien, fontsize=9, ha="center", va="center")
        if lee:
            ax.text(x + w + 0.35, y + h / 2, lee, fontsize=8.5, ha="left", va="center",
                    color=GRIS, family="DejaVu Sans Mono")
            flecha(ax, x + w + 0.3, y + h / 2, x + w + 0.02, y + h / 2, color=GRIS)
        if i:
            flecha(ax, x + w / 2, ys[i - 1], x + w / 2, y + h, color="black", ancho=1.1)

    ax.text(1.5, y0 + h + 0.35, "Responsable", fontsize=9, fontweight="bold", ha="center")
    ax.text(x + w + 1.6, y0 + h + 0.35, "Archivos que lee", fontsize=9, fontweight="bold",
            ha="center")

    # El paso 1 decide por donde se entra segun el tipo de encargo
    ax.text(x + w / 2 + 0.25, ys[0] - 0.29, "entra en el paso 2, 3 o 5 según el encargo",
            fontsize=8, color=GRIS, ha="left", va="center", style="italic")

    # rombo final
    cx, cy = x + w / 2, ys[-1] - 1.15
    rombo = plt.Polygon([(cx, cy + 0.75), (cx + 2.4, cy), (cx, cy - 0.75), (cx - 2.4, cy)],
                        facecolor="white", edgecolor="black", linewidth=1.1)
    ax.add_patch(rombo)
    ax.text(cx, cy, "Validación del\nauditor humano", fontsize=9.5, ha="center",
            va="center", fontweight="bold")
    flecha(ax, cx, ys[-1], cx, cy + 0.75, color="black", ancho=1.1)

    fig.savefig(os.path.join(AQUI, "flujo_skill.png"), dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


# --------------------------------------------------------------------------
def arquitectura_app():
    fig, ax = plt.subplots(figsize=(12.5, 7))
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 9.6)
    ax.axis("off")

    # Limite de la maquina del auditor
    ax.add_patch(Rectangle((0.15, 0.15), 16.7, 9.3, facecolor="none", edgecolor="black",
                           linewidth=1.2, linestyle=(0, (5, 3))))
    ax.text(0.35, 9.15, "Máquina del auditor (127.0.0.1) — ningún dato sale a internet",
            fontsize=9.5, fontweight="bold", va="center")

    def bloque(x, y, w, h, titulo, lineas, grueso=False):
        caja(ax, x, y, w, h, "", grueso=grueso)
        ax.text(x + 0.18, y + h - 0.32, titulo, fontsize=10, fontweight="bold", va="center")
        ax.text(x + 0.18, y + h - 0.72, "\n".join(lineas), fontsize=8.3, va="top",
                family="DejaVu Sans Mono", linespacing=1.45)

    # Navegador
    bloque(0.5, 3.4, 3.4, 3.6, "Navegador", ["index.html", "estilos.css", "app.js",
                                            "(JavaScript puro)", "", "Expediente",
                                            "Cobertura", "Asistente"])
    # Flask
    bloque(5.0, 2.2, 3.9, 6.0, "Backend Flask · app.py", [
        "GET  /api/estado", "GET  /api/cobertura", "POST /api/verificar",
        "POST /api/sugerir", "POST /api/registrar", "POST /api/chat",
        "POST /api/hallazgo"], grueso=True)
    flecha(ax, 3.9, 5.4, 5.0, 5.4, "HTTP / JSON", color="black", ancho=1.2, desp=(0, 0.25))
    flecha(ax, 5.0, 4.9, 3.9, 4.9, color="black", ancho=1.2)

    # Parte determinista
    bloque(10.2, 6.6, 3.0, 1.9, "evidencia.py", ["SHA-256", "cadena de custodia",
                                                 "cobertura"])
    bloque(13.7, 6.6, 2.9, 1.9, "Expediente", ["registro_evidencias", ".json",
                                               "cadena_custodia.log"])
    ax.text(11.7, 8.75, "Skill (cálculo determinista)", fontsize=8.5, color=GRIS,
            ha="center")
    flecha(ax, 8.9, 7.5, 10.2, 7.5, color="black", ancho=1.1)
    flecha(ax, 13.2, 7.55, 13.7, 7.55, color="black", ancho=1.1)
    flecha(ax, 13.7, 7.25, 13.2, 7.25, color="black", ancho=1.1)

    # RAG
    bloque(10.2, 3.75, 3.0, 2.15, "rag.py · FAISS", ["IndexFlatIP", "similitud coseno",
                                                     "59 fragmentos"])
    bloque(13.7, 3.75, 2.9, 2.15, "Conocimiento", ["catálogo, criterios", "plantilla, SKILL",
                                                   "glosario, evidencias"])
    flecha(ax, 8.9, 4.9, 10.2, 4.9, color="black", ancho=1.1)
    flecha(ax, 13.7, 4.8, 13.2, 4.8, color="black", ancho=1.1)

    # Modelos locales
    caja(ax, 10.2, 0.6, 6.4, 2.45, "", fondo=GRIS_CLARO)
    ax.text(10.4, 2.75, "Ollama (localhost:11434)", fontsize=10, fontweight="bold",
            va="center")
    caja(ax, 10.45, 0.85, 2.75, 1.5, "qwen2.5:7b\nLLM (chat)", tam=8.5)
    caja(ax, 13.6, 0.85, 2.75, 1.5, "nomic-embed-text\nembeddings", tam=8.5)
    flecha(ax, 15.6, 2.35, 12.9, 3.75, "vectores", color="black", ancho=1.1, desp=(0.75, 0.15))
    bloque(5.0, 0.6, 3.9, 1.25, "asistente.py", ["instrucciones + CONTEXTO"])
    flecha(ax, 6.95, 2.2, 6.95, 1.85, color="black", ancho=1.1)
    flecha(ax, 8.9, 1.25, 10.45, 1.25, "prompt", color="black", ancho=1.1, desp=(0, 0.22))

    fig.savefig(os.path.join(AQUI, "arquitectura_app.png"), dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


# --------------------------------------------------------------------------
# Ajustes de la revision de pertinencia (paso 4) documentados en
# hallazgos_preliminares.md: A.1.2.6 y A.3.14 pasan de Cubierto a Parcial.
AJUSTE_REVISION = {"Cubierto": -2, "Parcial": +2}


def estados_cobertura():
    import json
    ruta = os.path.join(AQUI, "..", "..", "02-skill", "evidencia-auditoria-pims", "assets",
                        "demo", "salida", "informe_cobertura.json")
    with open(ruta, encoding="utf-8") as f:
        demo = json.load(f)
    estados = ["Cubierto", "Parcial", "Desactualizada", "Comprometida", "Sin evidencia"]
    auto = [demo["conteo_estados"][e] for e in estados]
    revisado = [a + AJUSTE_REVISION.get(e, 0) for a, e in zip(auto, estados)]
    aplicables = demo["controles_aplicables"]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    alto = 0.36
    ys = list(range(len(estados)))[::-1]
    for valores, desp, color, nombre in ((auto, alto / 2 + 0.02, "#b5b5b5", "Automático (script)"),
                                         (revisado, -alto / 2 - 0.02, "#1a1a1a",
                                          "Tras revisión manual de pertinencia")):
        barras = ax.barh([y + desp for y in ys], valores, height=alto, color=color,
                         label=nombre, edgecolor="white", linewidth=1)
        for b, v in zip(barras, valores):
            ax.text(b.get_width() + 0.25, b.get_y() + b.get_height() / 2, str(v),
                    va="center", fontsize=9, color="#1a1a1a")
    ax.set_yticks(ys)
    ax.set_yticklabels(estados, fontsize=10)
    ax.set_xlabel("Número de controles (rol responsable, %d aplicables)" % aplicables,
                  fontsize=9.5)
    ax.set_xlim(0, max(auto + revisado) + 2.5)
    ax.xaxis.grid(True, color="#e3e3e3", linewidth=0.7)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#8a8a8a")
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="upper right", frameon=False, fontsize=9.5)
    from matplotlib.ticker import MaxNLocator
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    cob_a = 100.0 * auto[0] / aplicables
    cob_r = 100.0 * revisado[0] / aplicables
    ax.set_title(("Cobertura: %.1f %% automática  →  %.1f %% validada" % (cob_a, cob_r))
                 .replace(".", ","),
                 fontsize=11, loc="left", fontweight="bold")
    fig.savefig(os.path.join(AQUI, "estados_cobertura.png"), dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    arquitectura()
    flujo_skill()
    estados_cobertura()
    arquitectura_app()
    print("Figuras escritas en %s" % AQUI)
