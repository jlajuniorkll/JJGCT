TOOLS_ESCRITA = [
    {
        "name": "criar_despesa",
        "description": "Cria uma PROPOSTA de criação de despesa (não executa). Use quando o usuário pedir para registrar uma despesa e você tiver todos os campos obrigatórios.",
        "input_schema": {
            "type": "object",
            "properties": {
                "viagem_id": {"type": "integer", "description": "ID da viagem."},
                "valor": {"type": "number", "description": "Valor da despesa (ex: 50.0)."},
                "descricao": {"type": "string", "description": "Categoria/descrição (ex: Almoço)."},
                "forma_pagamento": {"type": "string", "description": "Forma de pagamento (ex: PIX, DINHEIRO, CARTAO_CREDITO, CARTAO_DEBITO)."},
                "tipo_pagamento": {"type": "string", "description": "Tipo: INDIVIDUAL ou COMPARTILHADO (opcional)."},
                "registrado_para_id": {"type": "integer", "description": "ID do usuário para quem a despesa foi registrada (opcional)."},
                "comprovante_url": {"type": "string", "description": "URL/caminho do comprovante já salvo (opcional)."},
            },
            "required": ["viagem_id", "valor", "descricao", "forma_pagamento"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "criar_atividade",
        "description": "Cria uma PROPOSTA de criação de atividade (não executa). Use quando o usuário pedir para registrar uma atividade e você tiver todos os campos obrigatórios.",
        "input_schema": {
            "type": "object",
            "properties": {
                "viagem_id": {"type": "integer", "description": "ID da viagem."},
                "descricao": {"type": "string", "description": "Descrição da atividade."},
                "ordem": {"type": "integer", "minimum": 1, "description": "Posição (1..N) na lista de atividades (opcional)."},
                "usuario_id": {"type": "integer", "description": "ID do usuário dono da atividade (opcional)."},
            },
            "required": ["viagem_id", "descricao"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "iniciar_atividade",
        "description": "Cria uma PROPOSTA para iniciar (dar start) em uma atividade da viagem (não executa). Use quando o usuário pedir para iniciar uma atividade específica.",
        "input_schema": {
            "type": "object",
            "properties": {
                "viagem_id": {"type": "integer", "description": "ID da viagem."},
                "atividade_id": {"type": "integer", "description": "ID da atividade a iniciar."},
            },
            "required": ["viagem_id", "atividade_id"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "pausar_atividade",
        "description": "Cria uma PROPOSTA para pausar uma atividade (não executa). Use quando o usuário pedir para pausar uma atividade e informar o motivo da pausa.",
        "input_schema": {
            "type": "object",
            "properties": {
                "viagem_id": {"type": "integer", "description": "ID da viagem."},
                "atividade_id": {"type": "integer", "description": "ID da atividade a pausar."},
                "motivo": {"type": "string", "description": "Motivo da pausa (obrigatório)."},
            },
            "required": ["viagem_id", "atividade_id", "motivo"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "finalizar_pausa",
        "description": "Cria uma PROPOSTA para finalizar a pausa (retomar) e voltar a atividade para ativa (não executa). Use quando o usuário pedir para retomar após uma pausa específica.",
        "input_schema": {
            "type": "object",
            "properties": {
                "viagem_id": {"type": "integer", "description": "ID da viagem."},
                "pausa_id": {"type": "integer", "description": "ID da pausa a finalizar."},
            },
            "required": ["viagem_id", "pausa_id"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "finalizar_viagem",
        "description": "Cria uma PROPOSTA para finalizar a viagem (registrar chegada) (não executa). Use quando o usuário pedir para finalizar/encerrar a viagem. A execução real só ocorre com confirmação no frontend.",
        "input_schema": {
            "type": "object",
            "properties": {
                "viagem_id": {"type": "integer", "description": "ID da viagem."},
                "km_chegada": {"type": "number", "description": "KM de chegada (obrigatório para carro empresa ou carro próprio)."},
                "data_hora_real_chegada": {"type": "string", "description": "Data/hora da chegada real em ISO 8601 (opcional; depende da configuração)."},
            },
            "required": ["viagem_id"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
]
