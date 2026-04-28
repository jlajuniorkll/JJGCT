CREATE TABLE IF NOT EXISTS ia_log (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER NULL REFERENCES usuarios(id) ON DELETE SET NULL,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  tipo VARCHAR(20) NOT NULL,
  mensagem_usuario TEXT NULL,
  ferramentas_chamadas JSONB NULL,
  tokens_input INTEGER NULL,
  tokens_output INTEGER NULL,
  tokens_cache_read INTEGER NULL,
  custo_estimado_usd DOUBLE PRECISION NULL,
  latencia_ms INTEGER NULL,
  sucesso BOOLEAN NOT NULL DEFAULT FALSE,
  erro VARCHAR(400) NULL
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'i'
      AND c.relname = 'ix_ia_log_criado_em'
      AND n.nspname = current_schema()
  ) THEN
    CREATE INDEX ix_ia_log_criado_em ON ia_log (criado_em);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'i'
      AND c.relname = 'ix_ia_log_tipo'
      AND n.nspname = current_schema()
  ) THEN
    CREATE INDEX ix_ia_log_tipo ON ia_log (tipo);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'i'
      AND c.relname = 'ix_ia_log_usuario_id'
      AND n.nspname = current_schema()
  ) THEN
    CREATE INDEX ix_ia_log_usuario_id ON ia_log (usuario_id);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'i'
      AND c.relname = 'ix_ia_log_sucesso'
      AND n.nspname = current_schema()
  ) THEN
    CREATE INDEX ix_ia_log_sucesso ON ia_log (sucesso);
  END IF;
END $$;
