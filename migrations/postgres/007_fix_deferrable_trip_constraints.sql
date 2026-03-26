INSERT INTO viagem_usuarios (viagem_id, usuario_id)
SELECT v.id, v.responsavel_id
FROM viagens v
LEFT JOIN viagem_usuarios vu
  ON vu.viagem_id = v.id AND vu.usuario_id = v.responsavel_id
WHERE v.responsavel_id IS NOT NULL
  AND vu.viagem_id IS NULL;

INSERT INTO viagem_usuarios (viagem_id, usuario_id)
SELECT tv.viagem_id, tv.motorista_id
FROM transporte_viagem tv
LEFT JOIN viagem_usuarios vu
  ON vu.viagem_id = tv.viagem_id AND vu.usuario_id = tv.motorista_id
WHERE tv.motorista_id IS NOT NULL
  AND vu.viagem_id IS NULL;

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
