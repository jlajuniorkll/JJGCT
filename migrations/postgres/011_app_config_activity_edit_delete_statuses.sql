DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'activity_edit_delete_allowed_statuses'
  ) THEN
    ALTER TABLE app_config
    ADD COLUMN activity_edit_delete_allowed_statuses text NOT NULL DEFAULT '["pendente"]';
  END IF;
END $$;

UPDATE app_config
SET activity_edit_delete_allowed_statuses = COALESCE(activity_edit_delete_allowed_statuses, '["pendente"]')
WHERE id = 1;
