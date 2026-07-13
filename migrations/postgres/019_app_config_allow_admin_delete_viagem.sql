DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'app_config'
      AND column_name = 'allow_admin_delete_viagem'
  ) THEN
    ALTER TABLE app_config
      ADD COLUMN allow_admin_delete_viagem boolean NOT NULL DEFAULT false;
  END IF;
END $$;
