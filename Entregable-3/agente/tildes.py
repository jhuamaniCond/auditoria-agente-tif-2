# -*- coding: utf-8 -*-
"""
Pone las tildes que faltan en los textos heredados sin acentos (catalogo de controles de la
skill del Entregable 1, textos deterministas del agente, nombres de requisitos en la BD).

Solo reemplaza palabras completas de una lista cerrada, respetando mayusculas; no toca codigos,
rutas con guion bajo ni huellas. No modifica los archivos del Entregable 1: se aplica al cargar.
"""

import re

PALABRAS = {
    # -cion / -sion
    "accion": "acción", "acciones": "acciones", "actualizacion": "actualización", "acreditacion": "acreditación",
    "anonimizacion": "anonimización", "aplicacion": "aplicación", "aprobacion": "aprobación",
    "asignacion": "asignación", "autorizacion": "autorización", "cancelacion": "cancelación",
    "capacitacion": "capacitación", "cesion": "cesión", "clasificacion": "clasificación",
    "comprension": "comprensión", "comunicacion": "comunicación", "concienciacion": "concienciación",
    "condicion": "condición", "configuracion": "configuración", "conservacion": "conservación",
    "contratacion": "contratación", "correccion": "corrección", "declaracion": "declaración",
    "descripcion": "descripción", "designacion": "designación", "deteccion": "detección",
    "determinacion": "determinación", "direccion": "dirección", "divulgacion": "divulgación",
    "documentacion": "documentación", "educacion": "educación", "ejecucion": "ejecución",
    "eliminacion": "eliminación", "especificacion": "especificación", "evaluacion": "evaluación",
    "exclusion": "exclusión", "finalizacion": "finalización", "formacion": "formación",
    "funcion": "función", "gestion": "gestión", "identificacion": "identificación",
    "implementacion": "implementación", "inclusion": "inclusión", "informacion": "información",
    "justificacion": "justificación", "limitacion": "limitación", "medicion": "medición",
    "minimizacion": "minimización", "mitigacion": "mitigación", "modificacion": "modificación",
    "notificacion": "notificación", "obligacion": "obligación", "operacion": "operación",
    "oposicion": "oposición", "organizacion": "organización", "planificacion": "planificación",
    "portabilidad": "portabilidad", "preparacion": "preparación", "prevencion": "prevención",
    "proteccion": "protección", "recepcion": "recepción", "recoleccion": "recolección",
    "recopilacion": "recopilación", "rectificacion": "rectificación", "relacion": "relación",
    "retencion": "retención", "revision": "revisión", "seleccion": "selección",
    "seudonimizacion": "seudonimización", "situacion": "situación", "supresion": "supresión",
    "transmision": "transmisión", "verificacion": "verificación", "version": "versión",
    "auditoria": "auditoría", "auditorias": "auditorías", "categoria": "categoría",
    "categorias": "categorías", "metodologia": "metodología", "politica": "política",
    "politicas": "políticas", "tecnologias": "tecnologías", "tecnologia": "tecnología",
    # otras frecuentes
    "analisis": "análisis", "area": "área", "areas": "áreas", "catalogo": "catálogo",
    "codigo": "código", "criterio": "criterio", "critico": "crítico", "criticos": "críticos",
    "dias": "días", "electronico": "electrónico", "especifico": "específico",
    "especifica": "específica", "especificos": "específicos", "fisico": "físico",
    "indice": "índice", "juridica": "jurídica", "juridico": "jurídico", "logico": "lógico",
    "minimo": "mínimo", "numero": "número", "pagina": "página", "proposito": "propósito",
    "propositos": "propósitos", "publica": "pública", "publico": "público", "segun": "según",
    "tecnica": "técnica", "tecnicas": "técnicas", "ultima": "última", "ultimo": "último",
    "unica": "única", "unico": "único", "valido": "válido", "periodica": "periódica",
    "periodicas": "periódicas", "automatica": "automática", "automatico": "automático",
    "academico": "académico", "economico": "económico", "biometricos": "biométricos",
    "despues": "después", "tambien": "también", "mas": "más", "duenio": "dueño",
    "parametros": "parámetros", "busqueda": "búsqueda", "rapido": "rápido",
    "Peru": "Perú", "Agustin": "Agustín", "clausula": "cláusula", "clausulas": "cláusulas",
    "titulo": "título", "titulos": "títulos", "integro": "íntegro",
}
_RE = re.compile(r"(?<![\w/.-])(" + "|".join(sorted(map(re.escape, PALABRAS), key=len, reverse=True))
                 + r")(?![\w/-])", re.IGNORECASE)
# "mas" sin tilde es conjuncion valida ("mas no"); solo se corrige en "Ley N.o" no aplica: se deja
# fuera de las expresiones de riesgo: se corrige solo cuando va seguido de espacio y palabra.
_EXCLUIR_SOLO = {"mas"}


def _reemplazo(m):
    original = m.group(0)
    clave = original.lower()
    if clave in _EXCLUIR_SOLO:
        return original
    nueva = PALABRAS.get(clave) or PALABRAS.get(original)
    if not nueva:
        return original
    if original.isupper() and len(original) > 1:
        return nueva.upper()
    if original[0].isupper():
        return nueva[0].upper() + nueva[1:]
    return nueva


def corregir(texto):
    if not isinstance(texto, str) or not texto:
        return texto
    t = _RE.sub(_reemplazo, texto)
    t = t.replace("cadena integra", "cadena íntegra").replace("Cadena integra", "Cadena íntegra")
    return t.replace("Ley N.o ", "Ley N.° ").replace("N.o ", "N.° ")


def corregir_catalogo(catalogo, campos=("titulo", "evidencia_esperada", "descripcion")):
    """Corrige en el sitio los textos de una lista de controles (dicts)."""
    for c in catalogo:
        for k in campos:
            if isinstance(c.get(k), str):
                c[k] = corregir(c[k])
    return catalogo
