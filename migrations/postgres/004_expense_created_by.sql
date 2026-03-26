DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'despesas' AND column_name = 'criado_por_id'
  ) THEN
    ALTER TABLE despesas ADD COLUMN criado_por_id integer NULL;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_despesas_criado_por'
  ) THEN
    ALTER TABLE despesas
      ADD CONSTRAINT fk_despesas_criado_por
      FOREIGN KEY (criado_por_id) REFERENCES usuarios(id);
  END IF;
END $$;

UPDATE despesas d
SET criado_por_id = COALESCE(d.criado_por_id, d.pago_por_id, d.registrado_para_id, v.responsavel_id)
FROM viagens v
WHERE d.viagem_id = v.id
  AND d.criado_por_id IS NULL;

