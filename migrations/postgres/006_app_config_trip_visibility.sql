DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'trips_show_all_admin'
  ) THEN
    ALTER TABLE app_config ADD COLUMN trips_show_all_admin boolean NOT NULL DEFAULT true;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'trips_show_all_colaborador'
  ) THEN
    ALTER TABLE app_config ADD COLUMN trips_show_all_colaborador boolean NOT NULL DEFAULT true;
  END IF;
END $$;

UPDATE app_config
SET trips_show_all_admin = COALESCE(trips_show_all_admin, true),
    trips_show_all_colaborador = COALESCE(trips_show_all_colaborador, true)
WHERE id = 1;

