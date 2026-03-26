UPDATE viagens v
SET responsavel_id = COALESCE(
  (SELECT tv.motorista_id FROM transporte_viagem tv WHERE tv.viagem_id = v.id AND tv.motorista_id IS NOT NULL LIMIT 1),
  (SELECT vu.usuario_id FROM viagem_usuarios vu WHERE vu.viagem_id = v.id ORDER BY vu.usuario_id ASC LIMIT 1)
)
WHERE v.responsavel_id IS NULL;

UPDATE despesas d
SET tipo_pagamento = 'INDIVIDUAL'
WHERE d.tipo_pagamento IS NULL OR d.tipo_pagamento = '';

UPDATE despesas d
SET pago_por_id = COALESCE(d.pago_por_id, v.responsavel_id),
    registrado_para_id = COALESCE(d.registrado_para_id, v.responsavel_id)
FROM viagens v
WHERE d.viagem_id = v.id
  AND (d.pago_por_id IS NULL OR d.registrado_para_id IS NULL);

INSERT INTO despesa_rateio (despesa_id, usuario_id, valor)
SELECT d.id, d.registrado_para_id, d.valor
FROM despesas d
LEFT JOIN despesa_rateio r
  ON r.despesa_id = d.id
WHERE d.tipo_pagamento = 'INDIVIDUAL'
  AND d.registrado_para_id IS NOT NULL
  AND r.id IS NULL;

