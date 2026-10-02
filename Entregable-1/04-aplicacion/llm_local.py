# -*- coding: utf-8 -*-
"""
Cliente minimo de Ollama (servidor local en http://localhost:11434).

Dos modelos, ambos ejecutados en la maquina del auditor:
  - EMBEDDINGS (nomic-embed-text): convierte texto en vectores para el RAG.
  - CHAT (qwen2.5:7b): redacta respuestas y hallazgos a partir del contexto.

Solo usa la biblioteca estandar (urllib), sin dependencias.
"""

import json
import os
import urllib.error
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODELO_CHAT = os.environ.get("AUDITA_MODELO_CHAT", "qwen2.5:7b")
MODELO_EMBEDDINGS = os.environ.get("AUDITA_MODELO_EMBEDDINGS", "nomic-embed-text")


class ErrorModelo(RuntimeError):
    """Ollama no responde o el modelo no esta descargado."""


def _post(ruta, cuerpo, timeout=600):
    datos = json.dumps(cuerpo).encode("utf-8")
    peticion = urllib.request.Request(OLLAMA_URL + ruta, data=datos,
                                      headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ErrorModelo("Ollama devolvio %s: %s" % (e.code, e.read().decode("utf-8", "replace")))
    except urllib.error.URLError as e:
        raise ErrorModelo("No se pudo conectar con Ollama en %s (%s). "
                          "Inicia Ollama y vuelve a intentarlo." % (OLLAMA_URL, e.reason))


def embeber(textos):
    """Devuelve una lista de vectores, uno por texto."""
    if not textos:
        return []
    r = _post("/api/embed", {"model": MODELO_EMBEDDINGS, "input": textos})
    return r["embeddings"]


def conversar(mensajes, temperatura=0.2, formato_json=False):
    """mensajes: lista de {"role": "system"|"user"|"assistant", "content": str}."""
    cuerpo = {"model": MODELO_CHAT, "messages": mensajes, "stream": False,
              "options": {"temperature": temperatura, "num_ctx": 8192}}
    if formato_json:
        cuerpo["format"] = "json"
    r = _post("/api/chat", cuerpo)
    return r["message"]["content"]


def estado():
    """Informa si Ollama esta activo y que modelos tiene descargados."""
    try:
        with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=5) as r:
            modelos = [m["name"] for m in json.loads(r.read().decode("utf-8"))["models"]]
    except Exception:
        return {"activo": False, "modelos": [], "chat": MODELO_CHAT,
                "embeddings": MODELO_EMBEDDINGS, "listo": False}

    def presente(nombre):
        return any(m == nombre or m.split(":")[0] == nombre or m == nombre + ":latest"
                   for m in modelos)
    return {"activo": True, "modelos": modelos, "chat": MODELO_CHAT,
            "embeddings": MODELO_EMBEDDINGS,
            "listo": presente(MODELO_CHAT) and presente(MODELO_EMBEDDINGS)}
