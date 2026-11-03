
-- Documentos fuente descargados de sitios oficiales (docs-unsa/) y su texto, pagina por pagina.
-- El agente lee el contenido desde aqui (OCR ya hecho) y no desde el PDF; el archivo sigue en disco
-- solo como respaldo y para comprobar su SHA-256.
CREATE TABLE documentos (
    id               BIGSERIAL PRIMARY KEY,
    proyecto         VARCHAR(60) NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
    handle           INTEGER,                         -- identificador en transparencia.unsa.edu.pe
    archivo          TEXT NOT NULL,
    titulo           TEXT NOT NULL,
    tipo_documento   VARCHAR(30) NOT NULL,            -- resolucion_rcu | resolucion_rr | informe | directiva | otro
    url_origen       TEXT,
    fecha_documento  DATE,
    fecha_descarga   DATE,
    sha256           CHAR(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    tamano_bytes     BIGINT,
    paginas          INTEGER NOT NULL DEFAULT 0,
    metodo_texto     VARCHAR(12) NOT NULL DEFAULT 'sin_texto'
                     CHECK (metodo_texto IN ('texto', 'ocr', 'mixto', 'sin_texto')),
    caracteres       INTEGER NOT NULL DEFAULT 0,
    cargado          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (proyecto, sha256)
);
CREATE INDEX ix_documentos_proyecto ON documentos (proyecto, fecha_documento DESC);

CREATE TABLE documento_paginas (
    documento_id  BIGINT NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    pagina        INTEGER NOT NULL CHECK (pagina >= 1),
    texto         TEXT NOT NULL,
    metodo        VARCHAR(6) NOT NULL CHECK (metodo IN ('texto', 'ocr')),
    PRIMARY KEY (documento_id, pagina)
);
CREATE INDEX ix_documento_paginas_texto ON documento_paginas
    USING GIN (to_tsvector('spanish', texto));
