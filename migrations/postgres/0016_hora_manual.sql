DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'app_config'
      AND column_name = 'trip_allow_manual_arrival_datetime'
  ) THEN
    ALTER TABLE public.app_config
      ADD COLUMN trip_allow_manual_arrival_datetime boolean NOT NULL DEFAULT false;
  END IF;
END $$;