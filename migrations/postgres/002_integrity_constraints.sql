DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_viagens_responsavel_participante'
  ) THEN
    ALTER TABLE viagens
      ADD CONSTRAINT fk_viagens_responsavel_participante
      FOREIGN KEY (id, responsavel_id)
      REFERENCES viagem_usuarios(viagem_id, usuario_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_transporte_motorista_participante'
  ) THEN
    ALTER TABLE transporte_viagem
      ADD CONSTRAINT fk_transporte_motorista_participante
      FOREIGN KEY (viagem_id, motorista_id)
      REFERENCES viagem_usuarios(viagem_id, usuario_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

CREATE OR REPLACE FUNCTION despesa_rateio_check_sum() RETURNS trigger AS $$
DECLARE
  total double precision;
  valor_total double precision;
  tipo varchar(20);
BEGIN
  SELECT d.valor, d.tipo_pagamento INTO valor_total, tipo
  FROM despesas d
  WHERE d.id = COALESCE(NEW.despesa_id, OLD.despesa_id);

  IF tipo IS NULL THEN
    RETURN NULL;
  END IF;

  IF tipo <> 'COMPARTILHADO' THEN
    RETURN NULL;
  END IF;

  SELECT COALESCE(SUM(r.valor), 0) INTO total
  FROM despesa_rateio r
  WHERE r.despesa_id = COALESCE(NEW.despesa_id, OLD.despesa_id);

  IF ABS(total - valor_total) > 0.01 THEN
    RAISE EXCEPTION 'Somatório do rateio (%) deve ser igual ao valor total (%)', total, valor_total;
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_despesa_rateio_check_sum'
  ) THEN
    CREATE CONSTRAINT TRIGGER trg_despesa_rateio_check_sum
      AFTER INSERT OR UPDATE OR DELETE ON despesa_rateio
      DEFERRABLE INITIALLY DEFERRED
      FOR EACH ROW
      EXECUTE PROCEDURE despesa_rateio_check_sum();
  END IF;
END $$;
