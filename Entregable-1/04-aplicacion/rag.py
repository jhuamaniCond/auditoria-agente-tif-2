# -*- coding: utf-8 -*-
"""
RAG local de AUDITA-PIMS: embeddings con nomic-embed-text (Ollama) e indice
vectorial FAISS en memoria y en disco.

Fuentes que se indexan:
  conocimiento  catalogo de controles (un fragmento por control), criterios de
                evidencia, plantilla de hallazgo, reglas de la skill y glosario.
  norma         texto de ISO/IEC 27701:2025 (ISOS/texto, ver extraer_norma.py):
                una o varias piezas por clausula, control del Anexo A y guia
                del Anexo B, con la referencia y la pagina del PDF.
  evidencia     texto de cada evidencia archivada en el expediente, con su ID.

El indice se reconstruye solo cuando cambia alguna fuente (se compara una
huella SHA-256 de todo lo indexado).
"""

import hashlib
import json
import os
import re
import threading

import faiss
import numpy as np

import llm_local
import norma

# FAISS usa OpenMP; combinado con los hilos de Flask en Windows puede bloquearse.
# El indice es pequeno: un hilo basta y el acceso se serializa con un candado.
faiss.omp_set_num_threads(1)
_CANDADO = threading.RLock()

# nomic-embed-text distingue documentos y consultas con un prefijo.
PREFIJO_DOC = "search_document: "
PREFIJO_CONSULTA = "search_query: "
EXTENSIONES_TEXTO = (".md", ".txt", ".csv", ".json", ".log")
TAM_FRAGMENTO = 1200


def _normalizar(matriz):
    matriz = np.asarray(matriz, dtype="float32")
    faiss.normalize_L2(matriz)
    return matriz


def _trocear(texto, tam=TAM_FRAGMENTO):
    """Divide por parrafos sin pasar de `tam` caracteres por fragmento."""
    partes, actual = [], ""
    for parrafo in re.split(r"\n\s*\n", texto):
        if len(actual) + len(parrafo) > tam and actual:
            partes.append(actual.strip())
            actual = ""
        actual += parrafo + "\n\n"
    if actual.strip():
        partes.append(actual.strip())
    return partes


def _secciones_markdown(texto):
    """Fragmentos por encabezado ## para conservar el contexto de cada seccion."""
    bloques = re.split(r"\n(?=#{1,3} )", texto)
    salida = []
    for b in bloques:
        salida.extend(_trocear(b))
    return [s for s in salida if len(s) > 40]


def leer_texto(ruta, limite=20000):
    """Texto plano de una evidencia, o cadena vacia si no es un formato de texto."""
    if not ruta.lower().endswith(EXTENSIONES_TEXTO):
        return ""
    with open(ruta, encoding="utf-8", errors="replace") as f:
        return f.read(limite)


class IndiceRAG(object):
    def __init__(self, rutas_conocimiento, catalogo, expediente, carpeta_datos):
        self.rutas_conocimiento = rutas_conocimiento
        self.catalogo = catalogo
        self.expediente = expediente
        self.ruta_indice = os.path.join(carpeta_datos, "indice.faiss")
        self.ruta_meta = os.path.join(carpeta_datos, "indice_meta.json")
        self.fragmentos = []          # [{"texto", "fuente", "tipo", "ref"}]
        self.indice = None

    # ------------------------------------------------------------ fragmentos
    def _fragmentos_conocimiento(self):
        frags = []
        for c in self.catalogo:
            texto = ("Control %s (%s): %s. Evidencia esperada: %s. Minimo de evidencias: %d."
                     % (c["ref"], "clausula" if c["grupo"] == "clausula" else "Anexo " + c["grupo"],
                        c["titulo"], c["evidencia_esperada"], c["minimo"]))
            frags.append({"texto": texto, "fuente": "controles_27701.json",
                          "tipo": "control", "ref": c["ref"]})
        for ruta in self.rutas_conocimiento:
            with open(ruta, encoding="utf-8") as f:
                contenido = f.read()
            for s in _secciones_markdown(contenido):
                frags.append({"texto": s, "fuente": os.path.basename(ruta),
                              "tipo": "conocimiento", "ref": ""})
        return frags + self._fragmentos_norma()

    def _titulo_es(self, ref):
        """Titulo en espanol del catalogo para una seccion de la norma (B.x -> A.x,
        9.2.1 -> 9.2): la norma esta en ingles y las preguntas llegan en espanol."""
        titulos = {c["ref"]: c["titulo"] for c in self.catalogo}
        if ref.startswith("B."):
            ref = "A." + ref[2:]
        while ref:
            if ref in titulos:
                return titulos[ref]
            ref = ref.rpartition(".")[0] if not ref.startswith("A.") else ""
        return ""

    def _fragmentos_norma(self):
        frags = []
        for s in norma.secciones():
            if len(s["texto"]) < 40:
                continue
            es = self._titulo_es(s["ref"])
            cabecera = "%s - %s %s%s" % (norma.cita(s), s["ref"], s["titulo"],
                                         " (%s)" % es if es else "")
            for t in _trocear(s["texto"]):
                frags.append({"texto": cabecera + "\n" + t, "fuente": norma.cita(s),
                              "tipo": "norma", "ref": s["ref"]})
        return frags

    def _fragmentos_evidencia(self):
        from evidencia_api import leer_indice
        frags = []
        for ev in leer_indice(self.expediente)["evidencias"]:
            frags.extend(self.fragmentos_de_evidencia(ev))
        return frags

    def fragmentos_de_evidencia(self, ev):
        texto = leer_texto(os.path.join(self.expediente, ev["archivo"]))
        cabecera = "%s - %s (tipo %s, fecha %s, controles %s)" % (
            ev["id"], ev["titulo"], ev["tipo"], ev["fecha_documento"], ", ".join(ev["controles"]))
        if not texto:
            return [{"texto": cabecera + ". Archivo no textual.", "fuente": ev["id"],
                     "tipo": "evidencia", "ref": ev["id"]}]
        return [{"texto": cabecera + "\n" + t, "fuente": ev["id"], "tipo": "evidencia",
                 "ref": ev["id"]} for t in _trocear(texto)]

    # --------------------------------------------------------------- indice
    def _huella(self, frags):
        h = hashlib.sha256(llm_local.MODELO_EMBEDDINGS.encode("utf-8"))
        for f in frags:
            h.update(f["texto"].encode("utf-8"))
        return h.hexdigest()

    def construir(self, forzar=False):
        """Carga el indice de disco si sigue vigente; si no, lo reconstruye."""
        frags = self._fragmentos_conocimiento() + self._fragmentos_evidencia()
        huella = self._huella(frags)
        if not forzar and os.path.exists(self.ruta_indice) and os.path.exists(self.ruta_meta):
            with open(self.ruta_meta, encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("huella") == huella:
                self.indice = faiss.read_index(self.ruta_indice)
                self.fragmentos = meta["fragmentos"]
                return "cargado"
        vectores = []
        for i in range(0, len(frags), 32):
            lote = frags[i:i + 32]
            vectores.extend(llm_local.embeber([PREFIJO_DOC + f["texto"] for f in lote]))
        matriz = _normalizar(vectores)
        self.indice = faiss.IndexFlatIP(matriz.shape[1])
        self.indice.add(matriz)
        self.fragmentos = frags
        faiss.write_index(self.indice, self.ruta_indice)
        with open(self.ruta_meta, "w", encoding="utf-8") as f:
            json.dump({"huella": huella, "fragmentos": frags}, f, ensure_ascii=False)
        return "reconstruido"

    def agregar_evidencia(self, ev):
        """Indexa una evidencia recien registrada sin reconstruir todo."""
        frags = self.fragmentos_de_evidencia(ev)
        vectores = llm_local.embeber([PREFIJO_DOC + f["texto"] for f in frags])
        with _CANDADO:
            self._agregar(frags, vectores)

    def _agregar(self, frags, vectores):
        matriz = _normalizar(vectores)
        self.indice.add(matriz)
        self.fragmentos.extend(frags)
        faiss.write_index(self.indice, self.ruta_indice)
        with open(self.ruta_meta, "w", encoding="utf-8") as f:
            json.dump({"huella": self._huella(self.fragmentos), "fragmentos": self.fragmentos},
                      f, ensure_ascii=False)

    def buscar(self, consulta, k=6, tipos=None):
        """Devuelve los k fragmentos mas parecidos, con su similitud coseno."""
        if self.indice is None or self.indice.ntotal == 0:
            return []
        vector = llm_local.embeber([PREFIJO_CONSULTA + consulta])
        with _CANDADO:
            q = _normalizar(vector)
            # Con filtro de tipo se recorre todo el indice (es pequeno): una pregunta
            # en espanol tiene cerca muchos textos en espanol antes que la norma.
            n = self.indice.ntotal if tipos else min(self.indice.ntotal, k)
            puntajes, posiciones = self.indice.search(q, n)
        salida = []
        for p, i in zip(puntajes[0], posiciones[0]):
            if i < 0:
                continue
            frag = dict(self.fragmentos[i])
            if tipos and frag["tipo"] not in tipos:
                continue
            frag["similitud"] = round(float(p), 3)
            salida.append(frag)
            if len(salida) == k:
                break
        return salida
