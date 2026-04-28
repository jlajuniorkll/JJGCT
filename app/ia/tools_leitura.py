TOOLS_LEITURA = [
    {
        "name": "listar_usuarios",
        "description": "Lista usuários (somente leitura). Use para buscar pessoas por nome/email e obter seus IDs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Filtro por nome ou email (parcial)."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Máximo de itens a retornar."},
            },
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "listar_veiculos",
        "description": "Lista veículos (somente leitura). Use para buscar por placa/modelo/marca e obter IDs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Filtro por placa/modelo/marca (parcial)."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Máximo de itens a retornar."},
            },
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "listar_viagens",
        "description": "Lista viagens (somente leitura) com filtros. Respeita permissões do usuário autenticado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Status da viagem (ex: planejada, em_andamento, finalizada, cancelada)."},
                "periodo_inicio": {"type": "string", "description": "Data/hora inicial em ISO 8601."},
                "periodo_fim": {"type": "string", "description": "Data/hora final em ISO 8601."},
                "responsavel_id": {"type": "integer", "description": "Filtra pelo ID do responsável."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Máximo de itens a retornar."},
            },
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "obter_viagem_detalhes",
        "description": "Obtém os detalhes completos de uma viagem (somente leitura), incluindo motivo, clientes, participantes, transporte, despesas e atividades. Respeita permissões do usuário autenticado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "viagem_id": {"type": "integer", "description": "ID da viagem."},
                "incluir_despesas": {"type": "boolean", "description": "Se deve incluir despesas.", "default": True},
                "incluir_atividades": {"type": "boolean", "description": "Se deve incluir atividades e pausas.", "default": True},
            },
            "required": ["viagem_id"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "listar_despesas",
        "description": "Lista despesas (somente leitura) com filtros. Ideal quando você já sabe a viagem_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "viagem_id": {"type": "integer", "description": "ID da viagem (obrigatório para listar despesas)."},
                "categoria": {"type": "string", "description": "Categoria/descrição exata (ex: Combustível)."},
                "periodo_inicio": {"type": "string", "description": "Data/hora inicial em ISO 8601."},
                "periodo_fim": {"type": "string", "description": "Data/hora final em ISO 8601."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "description": "Máximo de itens a retornar."},
            },
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "buscar_atividades",
        "description": "Busca atividades por título/descrição (somente leitura). Use quando o usuário citar o nome da atividade mas não souber o ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texto para buscar na descrição da atividade (parcial)."},
                "viagem_id": {"type": "integer", "description": "ID da viagem para limitar a busca (recomendado)."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Máximo de itens a retornar."},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "buscar_categorias_despesa",
        "description": "Retorna as categorias de despesa permitidas configuradas no sistema (AppConfig).",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "consultar_metrica",
        "description": "Consulta métricas agregadas (somente leitura).",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": ["total_despesas_viagem", "ranking_categorias", "custo_por_km", "horas_atividade_usuario"],
                    "description": "Tipo da métrica.",
                },
                "filtros": {"type": "object", "description": "Filtros em formato de objeto (ex: {\"viagem_id\": 123})."},
            },
            "required": ["tipo", "filtros"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
    {
        "name": "gerar_relatorio",
        "description": "Gera relatórios analíticos estruturados (somente leitura), com sugestão de gráfico e totais. Respeita permissões do usuário autenticado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": [
                        "despesas_por_viagem",
                        "despesas_por_categoria",
                        "despesas_por_usuario",
                        "custo_por_km",
                        "horas_atividade_por_usuario",
                        "viagens_por_status",
                    ],
                    "description": "Tipo do relatório.",
                },
                "periodo_inicio": {"type": "string", "description": "Data/hora inicial em ISO 8601 (opcional)."},
                "periodo_fim": {"type": "string", "description": "Data/hora final em ISO 8601 (opcional)."},
                "viagem_id": {"type": "integer", "description": "Filtra por uma viagem específica (opcional)."},
                "usuario_id": {"type": "integer", "description": "Filtra por um usuário específico (opcional; depende do tipo)."},
                "agrupar_por": {"type": "string", "description": "Opção de agrupamento (opcional; depende do tipo)."},
            },
            "required": ["tipo"],
            "additionalProperties": False,
        },
        "cache_control": {"type": "ephemeral"},
    },
]
