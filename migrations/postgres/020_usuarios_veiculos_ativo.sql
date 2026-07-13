DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'usuarios'
      AND column_name = 'ativo'
  ) THEN
    ALTER TABLE usuarios
      ADD COLUMN ativo boolean NOT NULL DEFAULT true;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'veiculos'
      AND column_name = 'ativo'
  ) THEN
    ALTER TABLE veiculos
      ADD COLUMN ativo boolean NOT NULL DEFAULT true;
  END IF;
END $$;
