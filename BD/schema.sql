-- =============================================================================
-- Base de datos del Agente de Evidencia y Auditoria (Grupo 6) - PIMS ISO/IEC 27701:2025
--
-- Modelo alineado con GESTITEL (https://unsa.27k.pe), la plataforma del profesor:
--   * catalogo de controles = los 142 de su "Analisis de brecha . SOA"
--     (93 de ISO/IEC 27001:2022 + 49 de las tablas A.1-A.2 de ISO/IEC 27701:2025);
--     los 29 controles A.3 se guardan con su equivalencia 27001 ("Cubre A.3.x").
--   * auditorias / checklist / hallazgos / acciones = su modulo "Auditorias"
--     (mismos campos que su "Exportar Excel"; estados con sus codigos de una letra).
--   * requisitos_brecha = los 69 requisitos de clausulas 4-10 de su analisis de brecha.
--   * expedientes D01-D37 = "Guia de documentos ISO 27701:2025" (Yauli, rev. 2).
-- Lo que agrega el agente sobre GESTITEL: evidencias reales con hash SHA-256,
-- cadena de custodia encadenada, revisiones de pertinencia y bitacoras.
-- =============================================================================

SET client_encoding = 'UTF8';
SET timezone = 'America/Lima';

-- -----------------------------------------------------------------------------
-- 1. CATALOGO (comun a todos los proyectos; lo llena cargar_catalogo.py)
-- -----------------------------------------------------------------------------

-- Expedientes D01-D37 de la guia del delegado.
CREATE TABLE expedientes (
    codigo                 VARCHAR(3) PRIMARY KEY CHECK (codigo ~ '^D[0-9]{2}$'),
    nombre                 TEXT NOT NULL,
    marca                  VARCHAR(5) NOT NULL,      -- E, C, S, X o combinaciones (E/C, S/C...)
    referencias            TEXT NOT NULL,            -- clausulas / controles de la norma
    fase                   TEXT NOT NULL,            -- fase del diagrama de implementacion
    accion                 TEXT,
    responsable_propuesto  TEXT,
    contenido              TEXT,
    se_revisa_cuando       TEXT
);

-- Requisitos auditables: clausulas 4-10 y controles (27001 Anexo A + 27701 A.1/A.2/A.3).
CREATE TABLE requisitos (
    codigo                 VARCHAR(12) PRIMARY KEY,  -- '9.2', 'A.5.33', 'A.1.2.2', 'A.3.14'
    tipo                   VARCHAR(10) NOT NULL CHECK (tipo IN ('clausula', 'control')),
    norma                  TEXT NOT NULL,            -- 'ISO/IEC 27001:2022' | 'ISO/IEC 27701:2025'
    nombre                 TEXT NOT NULL,
    grupo                  VARCHAR(10),              -- 'A.5', 'A.1.2', 'clausula', 'A.3'
    nombre_grupo           TEXT,
    rol_aplicable          TEXT,                     -- 'Todos' | 'Responsable del tratamiento' | 'Encargado del tratamiento'
    descripcion            TEXT,
    -- Equivalencia: un control A.3 (27701) apunta al control 27001 que lo cubre en GESTITEL.
    cubierto_por           VARCHAR(12) REFERENCES requisitos(codigo),
    en_gestitel            BOOLEAN NOT NULL DEFAULT FALSE,
    gestitel_id            INTEGER,                  -- columna "Id" del Excel de la SOA
    ley29733_aplica        BOOLEAN,
    ley29733_articulos     TEXT,
    ley29733_explicacion   TEXT,
    -- Criterio de evidencia de la skill evidencia-auditoria-pims (Entregable 1)
    evidencia_esperada     TEXT,
    evidencia_minima       SMALLINT,
    -- Tema del programa de seguridad (ISO/IEC 27701:2025, 6.1.3 c) para los controles 27001
    tema_programa          TEXT
);
CREATE INDEX ix_requisitos_cubierto_por ON requisitos (cubierto_por);

-- fuente: guia = tabla de la guia del delegado; equivalencia = heredado del control A.3
-- que cubre; norma = verificado contra el texto de ISO/IEC 27701:2025 (6.1.3 c).
CREATE TABLE requisito_expediente (
    requisito   VARCHAR(12) REFERENCES requisitos(codigo) ON DELETE CASCADE,
    expediente  VARCHAR(3)  REFERENCES expedientes(codigo) ON DELETE CASCADE,
    fuente      VARCHAR(12) NOT NULL DEFAULT 'guia'
                CHECK (fuente IN ('guia', 'equivalencia', 'norma')),
    fundamento  TEXT,
    PRIMARY KEY (requisito, expediente)
);

-- Requisitos de las clausulas 4-10 tal como los desglosa GESTITEL en su analisis de
-- brecha (core_gaprequirement: 69 filas, '4.2.a', '6.1.3.c', '9.2.1'...). Su checklist de
-- auditoria apunta a estos codigos ("Requisito de origen"). 'requisito' es la clausula de
-- nuestro catalogo que lo contiene ('4.2.a' -> '4.2', '9.3.2.a' -> '9.3').
CREATE TABLE requisitos_brecha (
    codigo        VARCHAR(10) PRIMARY KEY,           -- source_requirement_code en GESTITEL
    gestitel_id   INTEGER UNIQUE,
    clausula_soa  VARCHAR(5) NOT NULL,               -- '4' ... '10'
    titulo        TEXT NOT NULL,
    descripcion   TEXT NOT NULL,
    requisito     VARCHAR(12) NOT NULL REFERENCES requisitos(codigo)
);
CREATE INDEX ix_requisitos_brecha_requisito ON requisitos_brecha (requisito);

-- Codigos de una letra con que GESTITEL guarda los estados (varchar(1) en su BD) y que su
-- "Exportar Excel" escribe tal cual. codigo NULL = aun no confirmado con el ingeniero:
-- la exportacion deja el texto y avisa.
CREATE TABLE gestitel_codigos (
    dominio  VARCHAR(20) NOT NULL,                   -- tipo_auditoria, estado_auditoria, clasificacion, estado_accion
    valor    TEXT NOT NULL,                          -- el texto que usamos en nuestras tablas
    codigo   CHAR(1),
    fuente   TEXT,
    PRIMARY KEY (dominio, valor)
);
INSERT INTO gestitel_codigos VALUES
    ('tipo_auditoria',   'Interna',               'I', 'Export real de GESTITEL (formato_auditorias_gestitel.xlsx)'),
    ('tipo_auditoria',   'Externa',               NULL, NULL),
    ('estado_auditoria', 'Planificada',           NULL, NULL),
    ('estado_auditoria', 'En curso',              NULL, NULL),
    ('estado_auditoria', 'Cerrada',               'C', 'Export real de GESTITEL (auditoria "CLOSED" con estado C)'),
    ('clasificacion',    'No conformidad',        'N', 'Export real de GESTITEL (formato_auditorias_gestitel.xlsx)'),
    ('clasificacion',    'Observación',           NULL, NULL),
    ('clasificacion',    'Oportunidad de mejora', NULL, NULL),
    ('estado_accion',    'Abierta',               'O', 'Export real de GESTITEL (formato_auditorias_gestitel.xlsx)'),
    ('estado_accion',    'En progreso',           NULL, NULL),
    ('estado_accion',    'Cerrada',               NULL, NULL);

-- -----------------------------------------------------------------------------
-- 2. PROYECTO Y SOA
-- -----------------------------------------------------------------------------

CREATE TABLE proyectos (
    id           VARCHAR(60) PRIMARY KEY,           -- 'unsa'
    nombre       TEXT NOT NULL,
    rol          VARCHAR(12) NOT NULL CHECK (rol IN ('responsable', 'encargado', 'ambos')),
    descripcion  TEXT,
    creado       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Una fila por control y proyecto = pestana "Anexo A" de GESTITEL.
CREATE TABLE soa_evaluaciones (
    proyecto          VARCHAR(60) REFERENCES proyectos(id) ON DELETE CASCADE,
    requisito         VARCHAR(12) REFERENCES requisitos(codigo),
    aplicable         BOOLEAN NOT NULL DEFAULT TRUE,
    justificacion     TEXT,
    nivel_actual      SMALLINT CHECK (nivel_actual BETWEEN 0 AND 5),
    nivel_objetivo    SMALLINT CHECK (nivel_objetivo BETWEEN 0 AND 5),
    brecha            SMALLINT GENERATED ALWAYS AS (nivel_objetivo - nivel_actual) STORED,
    cumplimiento_pct  NUMERIC(5,2),
    evidencia_texto   TEXT,                          -- campo "Evidencia existente" de GESTITEL
    accion_mejora     TEXT,
    responsable       TEXT,
    prioridad         VARCHAR(5) CHECK (prioridad IN ('Alta', 'Media', 'Baja')),
    fecha_limite      DATE,
    estado            VARCHAR(12) NOT NULL DEFAULT 'Pendiente'
                      CHECK (estado IN ('Pendiente', 'En progreso', 'Cumplido', 'No aplica')),
    actualizado       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (proyecto, requisito)
);

-- -----------------------------------------------------------------------------
-- 3. EXPEDIENTE DE EVIDENCIAS (lo propio del Agente 4; control A.3.14 / D11)
-- -----------------------------------------------------------------------------

CREATE TABLE evidencias (
    id               BIGSERIAL PRIMARY KEY,
    proyecto         VARCHAR(60) NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
    codigo           VARCHAR(20) NOT NULL,           -- 'EV-0001'
    tipo             VARCHAR(30) NOT NULL,           -- politica, procedimiento, acta, registro...
    titulo           TEXT NOT NULL,
    ruta_archivo     TEXT NOT NULL,                  -- el binario queda en disco; aqui metadatos
    sha256           CHAR(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    tamano_bytes     BIGINT CHECK (tamano_bytes >= 0),
    fecha_documento  DATE,
    fecha_registro   TIMESTAMPTZ NOT NULL DEFAULT now(),
    responsable      TEXT NOT NULL,
    fuente           TEXT,                           -- URL oficial u origen
    version          INTEGER NOT NULL DEFAULT 1,
    estado           VARCHAR(10) NOT NULL DEFAULT 'vigente'
                     CHECK (estado IN ('vigente', 'obsoleta', 'retirada')),
    UNIQUE (proyecto, codigo)
);

CREATE TABLE evidencia_requisito (
    evidencia_id  BIGINT REFERENCES evidencias(id) ON DELETE CASCADE,
    requisito     VARCHAR(12) REFERENCES requisitos(codigo),
    orden         SMALLINT NOT NULL DEFAULT 0,
    PRIMARY KEY (evidencia_id, requisito)
);

-- Cadena de custodia encadenada por hash (solo insercion).
-- 'contenido' guarda la linea exacta que se hasheo, para poder recalcular el hash.
CREATE TABLE cadena_custodia (
    id             BIGSERIAL PRIMARY KEY,
    proyecto       VARCHAR(60) NOT NULL REFERENCES proyectos(id),
    n              INTEGER NOT NULL,
    fecha          TIMESTAMPTZ NOT NULL,
    accion         TEXT NOT NULL,             -- REGISTRO, VERIFICACION, REVISION_PERTINENCIA
    responsable    TEXT NOT NULL,
    evidencia_id   BIGINT REFERENCES evidencias(id),
    contenido      JSONB NOT NULL,
    hash_anterior  CHAR(64) NOT NULL,
    hash_linea     CHAR(64) NOT NULL,
    UNIQUE (proyecto, n)
);

-- Juicio de pertinencia vigente por requisito (IA local + decision del auditor).
-- El historial de decisiones queda en cadena_custodia (accion REVISION_PERTINENCIA).
CREATE TABLE revisiones_pertinencia (
    proyecto        VARCHAR(60) NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
    requisito       VARCHAR(12) NOT NULL REFERENCES requisitos(codigo),
    veredicto       TEXT NOT NULL,            -- cumple, cumple_parcialmente, no_cumple
    justificacion   TEXT,
    falta           TEXT,
    huellas         JSONB NOT NULL DEFAULT '{}'::jsonb, -- {codigo_evidencia: sha256} revisadas
    modelo          TEXT,
    decision        TEXT,                     -- NULL (pendiente), aceptada, rechazada
    auditor         TEXT,
    fecha_ia        TIMESTAMPTZ,
    fecha_decision  TIMESTAMPTZ,
    datos           JSONB NOT NULL,                  -- registro completo (citas, comentario...)
    PRIMARY KEY (proyecto, requisito)
);

-- -----------------------------------------------------------------------------
-- 4. AUDITORIAS (espejo del modulo "Auditorias" de GESTITEL; D33 / D34)
-- -----------------------------------------------------------------------------

CREATE TABLE auditorias (
    id                BIGSERIAL PRIMARY KEY,
    proyecto          VARCHAR(60) NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
    codigo            VARCHAR(20) NOT NULL UNIQUE,   -- 'AUD-2026-001' (audit_code de GESTITEL: max. 20)
    tipo              VARCHAR(8) NOT NULL DEFAULT 'Interna' CHECK (tipo IN ('Interna', 'Externa')),
    nombre            TEXT NOT NULL,
    alcance           TEXT,
    objetivo          TEXT,
    fecha_inicio      DATE,
    fecha_fin         DATE,
    lider             TEXT,
    equipo_auditor    TEXT[] NOT NULL DEFAULT '{}',
    areas             TEXT[] NOT NULL DEFAULT '{}',
    estado            VARCHAR(12) NOT NULL DEFAULT 'Planificada'
                      CHECK (estado IN ('Planificada', 'En curso', 'Cerrada')),
    ejecucion_agente  VARCHAR(80) UNIQUE,            -- id de la ejecucion LangGraph (AUD-2026...-xxxx)
    informe_ruta      TEXT,
    creado            TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE TABLE checklist_items (
    id                 BIGSERIAL PRIMARY KEY,
    auditoria_id       BIGINT NOT NULL REFERENCES auditorias(id) ON DELETE CASCADE,
    requisito          VARCHAR(12) REFERENCES requisitos(codigo),
    requisito_origen   VARCHAR(10) REFERENCES requisitos_brecha(codigo), -- source_requirement_code ('4.2.a')
    proceso            TEXT,
    norma              TEXT,
    evidencia_textual  TEXT,
    resultado          TEXT                    -- conforme, no_conforme, sin_evidencia...
);

CREATE TABLE hallazgos (
    id                     BIGSERIAL PRIMARY KEY,
    auditoria_id           BIGINT NOT NULL REFERENCES auditorias(id) ON DELETE CASCADE,
    checklist_item_id      BIGINT REFERENCES checklist_items(id) ON DELETE SET NULL,
    requisito              VARCHAR(12) REFERENCES requisitos(codigo),
    clasificacion          VARCHAR(25) NOT NULL
                           CHECK (clasificacion IN ('No conformidad', 'Observación', 'Oportunidad de mejora')),
    descripcion            TEXT NOT NULL,
    evidencia_texto        TEXT,
    origen                 VARCHAR(10) NOT NULL DEFAULT 'agente' CHECK (origen IN ('agente', 'humano')),
    -- Tratamiento de la no conformidad (10.2 / D34)
    correccion             TEXT,
    analisis_causa         TEXT,
    verificacion_eficacia  TEXT,
    fecha_cierre           DATE,
    creado                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Hallazgo -> evidencias concretas del expediente (lo que GESTITEL guarda solo como texto).
CREATE TABLE hallazgo_evidencia (
    hallazgo_id   BIGINT REFERENCES hallazgos(id) ON DELETE CASCADE,
    evidencia_id  BIGINT REFERENCES evidencias(id) ON DELETE CASCADE,
    PRIMARY KEY (hallazgo_id, evidencia_id)
);

CREATE TABLE acciones (
    id                BIGSERIAL PRIMARY KEY,
    hallazgo_id       BIGINT NOT NULL REFERENCES hallazgos(id) ON DELETE CASCADE,
    descripcion       TEXT NOT NULL,
    responsable       TEXT,
    fecha_compromiso  DATE,
    estado            VARCHAR(12) NOT NULL DEFAULT 'Abierta'
                      CHECK (estado IN ('Abierta', 'En progreso', 'Cerrada')),
    avance            SMALLINT NOT NULL DEFAULT 0 CHECK (avance BETWEEN 0 AND 100)
);

-- -----------------------------------------------------------------------------
-- 5. BITACORAS Y COORDINACION ENTRE AGENTES
-- -----------------------------------------------------------------------------

CREATE TABLE decisiones_humanas (
    id         BIGSERIAL PRIMARY KEY,
    fecha      TIMESTAMPTZ NOT NULL,
    ejecucion  VARCHAR(80),
    flujo      TEXT,
    proyecto   VARCHAR(60) REFERENCES proyectos(id),
    nodo       TEXT,
    actor      TEXT NOT NULL,
    origen     TEXT,                           -- humano | agente
    decision   TEXT NOT NULL,
    detalle    JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE eventos_agentes (
    id         VARCHAR(80) PRIMARY KEY,               -- 'EVT-20261027-161722-htt0'
    fecha      TIMESTAMPTZ NOT NULL,
    tipo       TEXT NOT NULL,                  -- aprobacion.requerida, auditoria.completada...
    origen     TEXT NOT NULL,
    proyecto   VARCHAR(60),
    ejecucion  VARCHAR(80),
    payload    JSONB NOT NULL DEFAULT '{}'::jsonb,
    entregas   JSONB NOT NULL DEFAULT '[]'::jsonb
);
CREATE INDEX ix_eventos_tipo_fecha ON eventos_agentes (tipo, fecha);

CREATE TABLE bitacora_mcp (
    n              INTEGER PRIMARY KEY,
    fecha          TIMESTAMPTZ NOT NULL,
    tool           TEXT NOT NULL,
    argumentos     JSONB NOT NULL DEFAULT '{}'::jsonb,
    transporte     VARCHAR(10),
    pid            INTEGER,
    resultado      TEXT,
    duracion_ms    NUMERIC(12,2),
    contenido      JSONB NOT NULL,                   -- entrada exacta que se hasheo
    hash_anterior  CHAR(64) NOT NULL,
    hash           CHAR(64) NOT NULL
);

-- Ejecuciones del orquestador LangGraph (antes datos/ejecuciones/*.json).
-- El estado interno del grafo lo guarda PostgresSaver en sus propias tablas (checkpoints...).
CREATE TABLE ejecuciones (
    id           VARCHAR(80) PRIMARY KEY,           -- AUD-20261027-161721-i9jw
    tipo         TEXT NOT NULL,              -- auditoria_interna | incidente | bandeja
    proyecto     VARCHAR(60) REFERENCES proyectos(id) ON DELETE CASCADE,
    estado       TEXT NOT NULL,
    creado       TIMESTAMPTZ NOT NULL,
    actualizado  TIMESTAMPTZ NOT NULL,
    datos        JSONB NOT NULL                     -- pasos, aprobacion, resultado...
);
CREATE INDEX ix_ejecuciones_proyecto ON ejecuciones (proyecto, creado DESC);

-- Ultimo estado del grafo de cada ejecucion (antes datos/ejecuciones/_estado/*.json).
CREATE TABLE ejecucion_instantaneas (
    ejecucion  VARCHAR(80) PRIMARY KEY,
    estado     JSONB NOT NULL,
    guardado   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Registros de solo insercion: protegen la trazabilidad (A.3.14).
CREATE FUNCTION fn_solo_insercion() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'La tabla % es de solo insercion (cadena de custodia / bitacora)', TG_TABLE_NAME;
END $$;

CREATE TRIGGER tg_custodia_inmutable BEFORE UPDATE OR DELETE ON cadena_custodia
    FOR EACH ROW EXECUTE FUNCTION fn_solo_insercion();
CREATE TRIGGER tg_mcp_inmutable BEFORE UPDATE OR DELETE ON bitacora_mcp
    FOR EACH ROW EXECUTE FUNCTION fn_solo_insercion();

-- -----------------------------------------------------------------------------
-- 6. VISTAS
-- -----------------------------------------------------------------------------

-- Cobertura de evidencias por requisito y proyecto (incluye la equivalencia A.3 <-> 27001).
CREATE VIEW v_cobertura AS
SELECT p.id AS proyecto, r.codigo AS requisito, r.nombre, r.tipo, r.evidencia_minima,
       COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'vigente') AS evidencias_vigentes,
       CASE
         WHEN COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'vigente') = 0 THEN 'Sin evidencia'
         WHEN COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'vigente') < COALESCE(r.evidencia_minima, 1) THEN 'Parcial'
         ELSE 'Con evidencia'
       END AS estado_cobertura,
       string_agg(DISTINCT re.expediente, ', ') AS expedientes
FROM proyectos p
CROSS JOIN requisitos r
LEFT JOIN evidencia_requisito er
       ON er.requisito = r.codigo OR er.requisito = r.cubierto_por
       OR er.requisito IN (SELECT codigo FROM requisitos x WHERE x.cubierto_por = r.codigo)
LEFT JOIN evidencias e ON e.id = er.evidencia_id AND e.proyecto = p.id
LEFT JOIN requisito_expediente re ON re.requisito = r.codigo
GROUP BY p.id, r.codigo, r.nombre, r.tipo, r.evidencia_minima;

-- Avance de cada auditoria (promedio de sus acciones, como en "Seguimiento" de GESTITEL).
CREATE VIEW v_auditoria_avance AS
SELECT a.id, a.codigo, a.estado,
       COUNT(DISTINCT h.id) AS hallazgos,
       COUNT(DISTINCT h.id) FILTER (WHERE h.clasificacion = 'No conformidad') AS no_conformidades,
       COALESCE(ROUND(AVG(ac.avance)), 0) AS avance_pct,
       COUNT(ac.id) FILTER (WHERE ac.estado <> 'Cerrada' AND ac.fecha_compromiso < CURRENT_DATE) AS acciones_vencidas,
       COUNT(ac.id) FILTER (WHERE ac.estado = 'Cerrada') AS acciones_cerradas
FROM auditorias a
LEFT JOIN hallazgos h ON h.auditoria_id = a.id
LEFT JOIN acciones ac ON ac.hallazgo_id = h.id
GROUP BY a.id, a.codigo, a.estado;

-- Filas con las mismas columnas que "Exportar Excel" del modulo Auditorias de GESTITEL.
CREATE VIEW v_export_auditorias_gestitel AS
-- Los estados salen con el codigo de una letra de GESTITEL (tabla gestitel_codigos).
SELECT a.codigo                       AS "Código de auditoría",
       COALESCE(gt.codigo, a.tipo)    AS "Tipo",
       a.nombre                       AS "Nombre",
       a.alcance                      AS "Alcance",
       a.objetivo                     AS "Objetivo",
       a.fecha_inicio                 AS "Fecha de inicio",
       a.fecha_fin                    AS "Fecha de fin",
       a.lider                        AS "Líder de auditoría",
       array_to_string(a.equipo_auditor, ', ') AS "Equipo auditor",
       array_to_string(a.areas, ', ')          AS "Áreas involucradas",
       COALESCE(ge.codigo, a.estado)  AS "Estado",
       v.avance_pct                   AS "Avance (%)",
       c.requisito_origen             AS "Requisito de origen (checklist)",
       c.proceso                      AS "Proceso (checklist)",
       c.norma                        AS "Norma (checklist)",
       c.requisito                    AS "Requisito (checklist)",
       c.evidencia_textual            AS "Evidencia textual (checklist)",
       COALESCE(gc.codigo, h.clasificacion) AS "Clasificación (hallazgo)",
       h.descripcion                  AS "Descripción (hallazgo)",
       h.evidencia_texto              AS "Evidencia (hallazgo)",
       ac.descripcion                 AS "Plan de acción",
       ac.responsable                 AS "Responsable (acción)",
       ac.fecha_compromiso            AS "Fecha compromiso (acción)",
       COALESCE(ga.codigo, ac.estado) AS "Estado (acción)",
       ac.avance                      AS "Avance (acción)"
FROM auditorias a
JOIN v_auditoria_avance v ON v.id = a.id
LEFT JOIN hallazgos h ON h.auditoria_id = a.id
LEFT JOIN checklist_items c ON c.id = h.checklist_item_id
LEFT JOIN acciones ac ON ac.hallazgo_id = h.id
LEFT JOIN gestitel_codigos gt ON gt.dominio = 'tipo_auditoria'   AND gt.valor = a.tipo
LEFT JOIN gestitel_codigos ge ON ge.dominio = 'estado_auditoria' AND ge.valor = a.estado
LEFT JOIN gestitel_codigos gc ON gc.dominio = 'clasificacion'    AND gc.valor = h.clasificacion
LEFT JOIN gestitel_codigos ga ON ga.dominio = 'estado_accion'    AND ga.valor = ac.estado;
