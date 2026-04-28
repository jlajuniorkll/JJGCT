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
]

