# -*- coding: utf-8 -*-
"""
Proyectos de auditoria: una organizacion auditada = un proyecto = una carpeta.

    datos/proyectos/<id>/
        proyecto.json            nombre, rol en el tratamiento, descripcion
        expediente/              evidencias, cadena de custodia, SoA, revisiones IA
        indice_evidencias.*      indice FAISS solo con las evidencias de este proyecto

Nada se comparte entre proyectos salvo la base de conocimiento (norma, catalogo,
criterios), que es la misma para todos. Asi la cobertura, las revisiones y el
chat de una organizacion nunca ven documentos de otra.
"""

import csv
import datetime as dt
import json
import os
import re
import threading
import unicodedata

from rag import IndiceRAG

ROLES = ("responsable", "encargado", "ambos")


class ErrorProyecto(ValueError):
    pass


class Proyecto(object):
    def __init__(self, carpeta, datos, conocimiento):
        self.carpeta = carpeta
        self.id = datos["id"]
        self.nombre = datos["nombre"]
        self.rol = datos.get("rol", "responsable")
        self.descripcion = datos.get("descripcion", "")
        self.creado = datos.get("creado", "")
        self.expediente = os.path.join(carpeta, "expediente")
        self.rag = IndiceRAG(conocimiento, self.expediente, carpeta)
        self.bloqueo = threading.Lock()      # el expediente se escribe de uno en uno
        self._rag_listo = False

    def preparar_rag(self):
        """Carga o construye el indice de evidencias la primera vez que se usa."""
        if not self._rag_listo:
            with self.bloqueo:
                if not self._rag_listo:
                    self.rag.construir()
                    self._rag_listo = True
        return self.rag

    def publico(self):
        from evidencia_api import leer_indice
        return {"id": self.id, "nombre": self.nombre, "rol": self.rol,
                "descripcion": self.descripcion, "creado": self.creado,
                "evidencias": len(leer_indice(self.expediente)["evidencias"])}


class Proyectos(object):
    def __init__(self, carpeta_datos, conocimiento):
        self.carpeta = os.path.join(carpeta_datos, "proyectos")
        self.conocimiento = conocimiento
        self._cache = {}
        self._candado = threading.Lock()
        os.makedirs(self.carpeta, exist_ok=True)

    @staticmethod
    def _almacen():
        """AlmacenPG si el Agente del Entregable 2 lo activo; None = archivos."""
        import evidencia_api  # noqa: F401  (pone scripts/ de la skill en sys.path)
        import evidencia
        return evidencia.ALMACEN

    def _leer(self, id_):
        almacen = self._almacen()
        if almacen is not None:
            return almacen.leer_proyecto(id_)
        ruta = os.path.join(self.carpeta, id_, "proyecto.json")
        if not os.path.isfile(ruta):
            return None
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)

    def listar(self):
        almacen = self._almacen()
        if almacen is not None:
            ids = almacen.listar_proyectos()
        else:
            ids = sorted(d for d in os.listdir(self.carpeta) if self._leer(d))
        return [self.obtener(i) for i in ids]

    def obtener(self, id_):
        """Proyecto por id, o None. El id solo admite [a-z0-9-] (nunca rutas)."""
        if not id_ or not re.fullmatch(r"[a-z0-9-]{1,60}", id_):
            return None
        with self._candado:
            return self._obtener_sin_candado(id_)

    def _obtener_sin_candado(self, id_):
        if id_ not in self._cache:
            datos = self._leer(id_)
            if not datos:
                return None
            carpeta = os.path.join(self.carpeta, id_)
            os.makedirs(os.path.join(carpeta, "expediente"), exist_ok=True)
            self._cache[id_] = Proyecto(carpeta, datos, self.conocimiento)
        return self._cache[id_]

    def crear(self, nombre, rol="responsable", descripcion="", excluidos=(), id_=None):
        """excluidos: [{"ref", "justificacion"}] -> soa.csv (controles que no aplican).
        id_: identificador fijo (si no, se deriva del nombre)."""
        nombre = (nombre or "").strip()
        if not nombre:
            raise ErrorProyecto("Escribe el nombre de la organizacion")
        if rol not in ROLES:
            raise ErrorProyecto("Rol no valido: %s" % rol)
        if id_ is not None and not re.fullmatch(r"[a-z0-9-]{1,60}", id_):
            raise ErrorProyecto("Identificador no valido: %s" % id_)
        for e in excluidos:
            if not (e.get("justificacion") or "").strip():
                raise ErrorProyecto("Justifica por que %s no aplica" % e.get("ref"))
        almacen = self._almacen()
        with self._candado:
            base = id_ or _slug(nombre) or "proyecto"
            id_, n = base, 2
            def ocupado(i):
                if almacen is not None:     # con BD manda la tabla proyectos
                    return almacen.leer_proyecto(i) is not None
                return os.path.exists(os.path.join(self.carpeta, i))
            while ocupado(id_):
                id_, n = "%s-%d" % (base, n), n + 1
            carpeta = os.path.join(self.carpeta, id_)
            # La carpeta guarda siempre los archivos de evidencia y el indice FAISS
            os.makedirs(os.path.join(carpeta, "expediente"), exist_ok=almacen is not None)
            datos = {"id": id_, "nombre": nombre, "rol": rol,
                     "descripcion": (descripcion or "").strip(),
                     "creado": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
            if almacen is not None:
                almacen.crear_proyecto(datos, excluidos)
                return self._obtener_sin_candado(id_)
            with open(os.path.join(carpeta, "proyecto.json"), "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            if excluidos:
                with open(os.path.join(carpeta, "expediente", "soa.csv"), "w",
                          encoding="utf-8", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["control_ref", "aplicable", "justificacion"])
                    for e in excluidos:
                        w.writerow([e["ref"], "no", e["justificacion"].strip()])
        return self.obtener(id_)


def _slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:40].strip("-")
