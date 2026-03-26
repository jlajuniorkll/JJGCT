# Refatoração incremental: responsável, despesas (individual/compartilhada) e rateio

## 1) Modelo atual (hoje)

**Tabelas principais**
- `viagens`
  - Não possui `responsavel_id`
  - Possui `meio_transporte`, `status`, datas previstas e reais
- `viagem_usuarios` (N:N)
  - Relaciona participantes da viagem (`viagem_id`, `usuario_id`)
  - Já evita duplicidade por PK composta (`viagem_id`, `usuario_id`)
- `transporte_viagem`
  - 1:1 com `viagens` (via `viagem_id`)
  - `motorista_id`, `veiculo_id`, `km_saida`, `km_chegada`
- `despesas`
  - Só tem `viagem_id`, `valor`, `forma_pagamento`, `descricao`, `comprovante_url`
  - Não tem “pago_por”, nem “para quem”, nem rateio

**Limitações**
- Não há um “dono/gestor” da viagem para controle de permissões (iniciar/editar).
- Em despesas, não existe rastreio de:
  - quem pagou
  - para quem a despesa foi registrada
  - despesas compartilhadas e rateio
- Integridade motorista/participantes é mantida só por regra de aplicação (não por constraint).

## 2) Proposta de refatoração incremental (sem recriar do zero)

### 2.1 Viagens

**Adicionar `responsavel_id` em `viagens`**
- Objetivo: definir “quem pode iniciar e editar a viagem”.
- Regra funcional:
  - Se existir motorista, por padrão `responsavel_id = motorista_id` (pode ser alterado depois).
  - Se não existir motorista (carona/terceiros), `responsavel_id` deve existir (padrão: primeiro participante ou usuário logado).

**Integridade**
- Garantir via FK composta que `responsavel_id` pertence aos participantes:
  - `FOREIGN KEY (viagens.id, viagens.responsavel_id) -> viagem_usuarios(viagem_id, usuario_id)`
- Garantir via FK composta que `motorista_id` (quando existir) pertence aos participantes:
  - `FOREIGN KEY (transporte_viagem.viagem_id, transporte_viagem.motorista_id) -> viagem_usuarios(viagem_id, usuario_id)`

### 2.2 Participantes

**Manter `viagem_usuarios`**
- Mantém baixo impacto e preserva dados existentes.
- Evolução futura (opcional) para escalabilidade:
  - Transformar `viagem_usuarios` em uma tabela “entidade” com colunas adicionais (ex.: `papel`, `adicionado_por`, `data_criacao`).
  - Isso pode ser feito em uma segunda fase, mantendo compatibilidade.

### 2.3 Despesas (individual/compartilhada)

**Evoluir `despesas`**
- Adicionar colunas:
  - `pago_por_id` (FK `usuarios.id`)
  - `registrado_para_id` (FK `usuarios.id`) — permite registrar “em nome de outro usuário”
  - `tipo_pagamento` (`INDIVIDUAL` ou `COMPARTILHADO`)

**Nova tabela de rateio**
- `despesa_rateio`
  - `despesa_id` (FK `despesas.id`)
  - `usuario_id` (FK `usuarios.id`)
  - `valor` (parte do valor total da despesa)
  - `UNIQUE (despesa_id, usuario_id)` para evitar duplicidade

**Regra de integridade para compartilhadas**
- Se `tipo_pagamento = COMPARTILHADO`, então:
  - `SUM(despesa_rateio.valor) = despesas.valor`
  - rateio com pelo menos 2 participantes
- Em Postgres, isso exige trigger/constraint trigger (não dá para fazer com `CHECK` simples).

## 3) Plano de migração de dados (sem perda)

### Fase A — migrations “aditivas” (seguras)
1. Aplicar `001_schema_additions.sql`:
   - adiciona colunas novas e tabela `despesa_rateio`
   - adiciona FKs e checks básicos

### Fase B — backfill de dados antigos
2. Aplicar `003_backfill.sql`:
   - `viagens.responsavel_id`:
     - usa `motorista_id` se existir, senão o menor `usuario_id` em `viagem_usuarios`
   - `despesas.tipo_pagamento` = `INDIVIDUAL` quando vazio/nulo
   - `despesas.pago_por_id` e `despesas.registrado_para_id`:
     - usa `viagens.responsavel_id` quando não houver informação histórica
   - cria `despesa_rateio` 100% para o `registrado_para_id` em despesas individuais

### Fase C — constraints fortes (opcional em deploy gradual)
3. Aplicar `002_integrity_constraints.sql`:
   - FKs compostas para garantir responsável/motorista ∈ participantes
   - constraint trigger para garantir somatório do rateio em despesas compartilhadas

## 4) Ajustes mínimos na API (compatibilidade)

**Manter endpoints existentes (v1)**
- Os endpoints atuais continuam funcionando.
- Novos campos em `despesas` são opcionais no v1.

**Novos endpoints (incrementais)**
- `GET /api/despesas/{id}/rateio`
- `PUT /api/despesas/{id}/rateio`

Se, no futuro, for necessário “payload único” (despesa + rateio + anexo) de forma mais elegante, recomenda-se:
- criar `v2` (ex.: `/api/v2/despesas`) com contrato JSON + upload, mantendo `v1` intacto.

## 5) Estratégia de deploy sem downtime

1. Subir migrations (Fase A) primeiro:
   - não quebra o backend antigo (só adiciona estrutura)
2. Subir novo backend:
   - já pode escrever/ler colunas novas
3. Rodar backfill (Fase B)
4. Ativar constraints fortes (Fase C)

## 6) Scripts entregues

- [001_schema_additions.sql](file:///c:/DevPrograms/src/jjg_viagem/migrations/postgres/001_schema_additions.sql)
- [002_integrity_constraints.sql](file:///c:/DevPrograms/src/jjg_viagem/migrations/postgres/002_integrity_constraints.sql)
- [003_backfill.sql](file:///c:/DevPrograms/src/jjg_viagem/migrations/postgres/003_backfill.sql)

