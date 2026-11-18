-- Entregable 3: documentos del PIMS (lista maestra PIMS-RG-01 de PIMS-PR-01).
-- Cada documento PIMS (procedimiento, politica, formulario, registro...) que suben los grupos
-- vive en `documentos` (archivo, SHA-256 y texto por pagina/seccion) y aqui sus metadatos de
-- control (ISO/IEC 27701:2025, 7.5.2 y 7.5.3), tal como los lee el agente de la portada.
-- Idempotente: se puede volver a aplicar.
ALTER TABLE documentos DROP CONSTRAINT IF EXISTS documentos_tipo_documento_check;

CREATE TABLE IF NOT EXISTS documentos_pims (
    id                BIGSERIAL PRIMARY KEY,
    proyecto          VARCHAR(60) NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
    documento_id      BIGINT NOT NULL UNIQUE REFERENCES documentos(id) ON DELETE CASCADE,
    evidencia_id      BIGINT REFERENCES evidencias(id) ON DELETE SET NULL,
    codigo            VARCHAR(20) NOT NULL,              -- PIMS-PR-01 (formato PIMS-TT-NN)
    titulo            TEXT NOT NULL,
    tipo              VARCHAR(20) NOT NULL,              -- politica, procedimiento, formulario...
    version           VARCHAR(20),
    fecha_version     DATE,
    creado_por        TEXT,
    aprobado_por      TEXT,
    confidencialidad  TEXT,
    propietario       TEXT,
    valido_hasta      DATE,
    historial         JSONB NOT NULL DEFAULT '[]'::jsonb, -- [{fecha, version, autor, descripcion}]
    requisitos        TEXT[] NOT NULL DEFAULT '{}',      -- clausulas / controles que respalda
    expedientes       TEXT[] NOT NULL DEFAULT '{}',      -- D11, D34... (guia del delegado)
    agente_autor      TEXT,                              -- equipo del PIMS que lo elaboro
    estado            VARCHAR(12) NOT NULL DEFAULT 'borrador'
                      CHECK (estado IN ('borrador', 'aprobado', 'obsoleto')),
    control           JSONB NOT NULL DEFAULT '{}'::jsonb, -- resultado de la verificacion PR-01
    registrado_por    TEXT NOT NULL,
    registrado        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_documentos_pims_codigo ON documentos_pims (proyecto, codigo);

-- Version vigente de cada codigo = la ultima aprobada no obsoleta.
CREATE OR REPLACE VIEW v_documentos_pims AS
SELECT d.*, doc.archivo, doc.sha256, doc.paginas, doc.caracteres,
       (d.estado = 'aprobado' AND (d.valido_hasta IS NULL OR d.valido_hasta >= CURRENT_DATE)) AS vigente
FROM documentos_pims d
JOIN documentos doc ON doc.id = d.documento_id;

-- Lista maestra de informacion documentada (PIMS-RG-01): que documentos debe tener el PIMS,
-- con las clausulas y controles que los exigen y el equipo que los elabora (Mensaje 3).
-- Fuente: Entregable-3/agente/lista_maestra_pims.py (la sincroniza cargar_documentos_pims.py).
CREATE TABLE IF NOT EXISTS lista_maestra_pims (
    proyecto          VARCHAR(60) NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
    codigo            VARCHAR(20) NOT NULL,              -- PIMS-TT-NN
    orden             INTEGER NOT NULL DEFAULT 0,
    titulo            TEXT NOT NULL,
    tipo              VARCHAR(20) NOT NULL,
    requisitos        TEXT[] NOT NULL DEFAULT '{}',      -- clausulas y controles ISO/IEC 27701:2025
    expedientes       TEXT[] NOT NULL DEFAULT '{}',      -- D01-D37 de la guia del docente
    marca             VARCHAR(4),                        -- E exigido, C control, S apoyo
    equipo            TEXT NOT NULL,                     -- equipo (agente) del PIMS que lo elabora
    propietario       TEXT,
    confidencialidad  TEXT,
    actualizado       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (proyecto, codigo)
);
