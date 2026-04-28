DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'ia_model_anthropic'
  ) THEN
    ALTER TABLE app_config
    ADD COLUMN ia_model_anthropic text NOT NULL DEFAULT 'claude-sonnet-4-6';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'ia_model_gemini'
  ) THEN
    ALTER TABLE app_config
    ADD COLUMN ia_model_gemini text NOT NULL DEFAULT 'gemini-2.5-flash';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'anthropic_api_key_enc'
  ) THEN
    ALTER TABLE app_config
    ADD COLUMN anthropic_api_key_enc text;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'anthropic_api_key_last4'
  ) THEN
    ALTER TABLE app_config
    ADD COLUMN anthropic_api_key_last4 text;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'gemini_api_key_enc'
  ) THEN
    ALTER TABLE app_config
    ADD COLUMN gemini_api_key_enc text;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'gemini_api_key_last4'
  ) THEN
    ALTER TABLE app_config
    ADD COLUMN gemini_api_key_last4 text;
  END IF;
END $$;

UPDATE app_config
SET
  ia_model_anthropic = COALESCE(NULLIF(ia_model_anthropic, ''), 'claude-sonnet-4-6'),
  ia_model_gemini = COALESCE(NULLIF(ia_model_gemini, ''), 'gemini-2.5-flash')
WHERE id = 1;
