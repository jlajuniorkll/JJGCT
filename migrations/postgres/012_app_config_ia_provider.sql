DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'ia_provider'
  ) THEN
    ALTER TABLE app_config
    ADD COLUMN ia_provider text NOT NULL DEFAULT 'anthropic';
  END IF;
END $$;

UPDATE app_config
SET ia_provider = COALESCE(NULLIF(ia_provider, ''), 'anthropic')
WHERE id = 1;
