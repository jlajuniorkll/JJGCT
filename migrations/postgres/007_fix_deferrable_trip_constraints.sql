DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_viagens_responsavel_participante'
  ) THEN
    ALTER TABLE viagens DROP CONSTRAINT fk_viagens_responsavel_participante;
  END IF;
END $$;

ALTER TABLE viagens
  ADD CONSTRAINT fk_viagens_responsavel_participante
  FOREIGN KEY (id, responsavel_id)
  REFERENCES viagem_usuarios(viagem_id, usuario_id)
  DEFERRABLE INITIALLY DEFERRED;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_transporte_motorista_participante'
  ) THEN
    ALTER TABLE transporte_viagem DROP CONSTRAINT fk_transporte_motorista_participante;
  END IF;
END $$;

ALTER TABLE transporte_viagem
  ADD CONSTRAINT fk_transporte_motorista_participante
  FOREIGN KEY (viagem_id, motorista_id)
  REFERENCES viagem_usuarios(viagem_id, usuario_id)
  DEFERRABLE INITIALLY DEFERRED;

