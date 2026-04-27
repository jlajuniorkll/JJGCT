CREATE TABLE IF NOT EXISTS viagem_clientes (
  id SERIAL PRIMARY KEY,
  viagem_id INTEGER NOT NULL REFERENCES viagens(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO viagem_clientes (viagem_id, nome)
SELECT v.id, v.cliente
FROM viagens v
WHERE v.cliente IS NOT NULL
  AND btrim(v.cliente) <> ''
  AND NOT EXISTS (
    SELECT 1 FROM viagem_clientes vc WHERE vc.viagem_id = v.id
  );

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'viagens' AND column_name = 'local_partida'
  ) THEN
    ALTER TABLE viagens DROP COLUMN local_partida;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'viagens' AND column_name = 'local_chegada'
  ) THEN
    ALTER TABLE viagens DROP COLUMN local_chegada;
  END IF;
END $$;
