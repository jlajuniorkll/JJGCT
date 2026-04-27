DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'app_config' AND column_name = 'expense_description_options'
  ) THEN
    ALTER TABLE app_config
    ADD COLUMN expense_description_options text NOT NULL DEFAULT '["Almoço","Janta","Lanche","Hospedagem","Taxi/Uber","Estacionamento","Pedágio","Combustível","Locação"]';
  END IF;
END $$;

UPDATE app_config
SET expense_description_options = COALESCE(expense_description_options, '["Almoço","Janta","Lanche","Hospedagem","Taxi/Uber","Estacionamento","Pedágio","Combustível","Locação"]')
WHERE id = 1;
