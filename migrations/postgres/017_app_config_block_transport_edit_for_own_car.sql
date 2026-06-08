DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'app_config'
      AND column_name = 'block_transport_edit_for_own_car'
  ) THEN
    ALTER TABLE public.app_config
      ADD COLUMN block_transport_edit_for_own_car boolean NOT NULL DEFAULT false;
  END IF;
END $$;
