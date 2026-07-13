-- Índices em colunas de FK usadas em filtros/joins frequentes (viagens, despesas, atividades, pausas, rateio).
-- Puramente aditivo: não altera dados nem resultados de query, só acelera leituras.
-- IMPORTANTE: CREATE INDEX CONCURRENTLY não pode rodar dentro de uma transação explícita.
-- Execute este arquivo fora de um BEGIN/COMMIT (ex: `psql -f 018_add_fk_indexes.sql`, uma instrução por vez / autocommit).
-- Sem "IF NOT EXISTS": este banco está em PostgreSQL 9.3, que não suporta essa cláusula em CREATE INDEX
-- (só chegou no Postgres 9.5). Se rodar de novo, remova manualmente as linhas dos índices já criados.

CREATE INDEX CONCURRENTLY ix_viagem_usuarios_usuario_id ON viagem_usuarios (usuario_id);

CREATE INDEX CONCURRENTLY ix_viagens_responsavel_id ON viagens (responsavel_id);

CREATE INDEX CONCURRENTLY ix_viagem_clientes_viagem_id ON viagem_clientes (viagem_id);

CREATE INDEX CONCURRENTLY ix_transporte_viagem_viagem_id ON transporte_viagem (viagem_id);
CREATE INDEX CONCURRENTLY ix_transporte_viagem_veiculo_id ON transporte_viagem (veiculo_id);
CREATE INDEX CONCURRENTLY ix_transporte_viagem_motorista_id ON transporte_viagem (motorista_id);

CREATE INDEX CONCURRENTLY ix_despesas_viagem_id ON despesas (viagem_id);
CREATE INDEX CONCURRENTLY ix_despesas_pago_por_id ON despesas (pago_por_id);
CREATE INDEX CONCURRENTLY ix_despesas_registrado_para_id ON despesas (registrado_para_id);

CREATE INDEX CONCURRENTLY ix_despesa_rateio_despesa_id ON despesa_rateio (despesa_id);
CREATE INDEX CONCURRENTLY ix_despesa_rateio_usuario_id ON despesa_rateio (usuario_id);

CREATE INDEX CONCURRENTLY ix_atividades_viagem_id ON atividades (viagem_id);
CREATE INDEX CONCURRENTLY ix_atividades_usuario_id ON atividades (usuario_id);

CREATE INDEX CONCURRENTLY ix_pausas_atividade_id ON pausas (atividade_id);
