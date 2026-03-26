DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'trip_activity_expense_allowed_statuses'
  ) THEN
    ALTER TABLE app_config ADD COLUMN trip_activity_expense_allowed_statuses text NOT NULL DEFAULT '["em_andamento"]';
  END IF;
END $$;

UPDATE app_config
SET trip_activity_expense_allowed_statuses = COALESCE(trip_activity_expense_allowed_statuses, '["em_andamento"]')
WHERE id = 1;

