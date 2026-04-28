DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'app_config'
      AND column_name = 'report_include_receipts'
  ) THEN
    ALTER TABLE public.app_config
      ADD COLUMN report_include_receipts boolean NOT NULL DEFAULT true;
  END IF;
END $$;

