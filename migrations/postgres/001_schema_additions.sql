DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'viagens' AND column_name = 'responsavel_id'
  ) THEN
    ALTER TABLE viagens ADD COLUMN responsavel_id integer NULL;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'despesas' AND column_name = 'pago_por_id'
  ) THEN
    ALTER TABLE despesas ADD COLUMN pago_por_id integer NULL;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'despesas' AND column_name = 'tipo_pagamento'
  ) THEN
    ALTER TABLE despesas ADD COLUMN tipo_pagamento varchar(20) NOT NULL DEFAULT 'INDIVIDUAL';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'despesas' AND column_name = 'registrado_para_id'
  ) THEN
    ALTER TABLE despesas ADD COLUMN registrado_para_id integer NULL;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS despesa_rateio (
  id serial PRIMARY KEY,
  despesa_id integer NOT NULL,
  usuario_id integer NOT NULL,
  valor double precision NOT NULL,
  data_criacao timestamptz NOT NULL DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_viagens_responsavel'
  ) THEN
    ALTER TABLE viagens
      ADD CONSTRAINT fk_viagens_responsavel
      FOREIGN KEY (responsavel_id) REFERENCES usuarios(id);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_despesas_pago_por'
  ) THEN
    ALTER TABLE despesas
      ADD CONSTRAINT fk_despesas_pago_por
      FOREIGN KEY (pago_por_id) REFERENCES usuarios(id);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_despesas_registrado_para'
  ) THEN
    ALTER TABLE despesas
      ADD CONSTRAINT fk_despesas_registrado_para
      FOREIGN KEY (registrado_para_id) REFERENCES usuarios(id);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_despesa_rateio_despesa'
  ) THEN
    ALTER TABLE despesa_rateio
      ADD CONSTRAINT fk_despesa_rateio_despesa
      FOREIGN KEY (despesa_id) REFERENCES despesas(id) ON DELETE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'fk_despesa_rateio_usuario'
  ) THEN
    ALTER TABLE despesa_rateio
      ADD CONSTRAINT fk_despesa_rateio_usuario
      FOREIGN KEY (usuario_id) REFERENCES usuarios(id);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'chk_despesas_tipo_pagamento'
  ) THEN
    ALTER TABLE despesas
      ADD CONSTRAINT chk_despesas_tipo_pagamento
      CHECK (tipo_pagamento IN ('INDIVIDUAL', 'COMPARTILHADO'));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'uq_despesa_rateio_despesa_usuario'
  ) THEN
    ALTER TABLE despesa_rateio
      ADD CONSTRAINT uq_despesa_rateio_despesa_usuario
      UNIQUE (despesa_id, usuario_id);
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'chk_despesa_rateio_valor'
  ) THEN
    ALTER TABLE despesa_rateio
      ADD CONSTRAINT chk_despesa_rateio_valor
      CHECK (valor >= 0);
  END IF;
END $$;

