DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'atividades'
      AND column_name = 'ordem'
  ) THEN
    ALTER TABLE atividades ADD COLUMN ordem INTEGER;
  END IF;
END $$;

WITH ranked AS (
  SELECT
    id,
    ROW_NUMBER() OVER (PARTITION BY viagem_id ORDER BY id) AS rn
  FROM atividades
)
UPDATE atividades a
SET ordem = r.rn
FROM ranked r
WHERE a.id = r.id
  AND a.ordem IS NULL;

ALTER TABLE atividades
ALTER COLUMN ordem SET NOT NULL;
