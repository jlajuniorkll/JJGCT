from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Schemas para Usuário
class UsuarioBase(BaseModel):
    nome: str
    email: str
    tipousuario: str
    tem_cnh: bool = False

class UsuarioCreate(UsuarioBase):
    senha: str


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    senha: Optional[str] = None
    tipousuario: Optional[str] = None
    tem_cnh: Optional[bool] = None


class Usuario(UsuarioBase):
    id: int
    data_criacao: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: str
    senha: str


# Schemas para Veículo
class VeiculoBase(BaseModel):
    placa: str
    modelo: str
    marca: str
    ano: int

class VeiculoCreate(VeiculoBase):
    pass


class VeiculoUpdate(BaseModel):
    placa: Optional[str] = None
    modelo: Optional[str] = None
    marca: Optional[str] = None
    ano: Optional[int] = None


class Veiculo(VeiculoBase):
    id: int

    class Config:
        from_attributes = True

# Schemas para TransporteViagem
class TransporteViagemBase(BaseModel):
    veiculo_id: Optional[int] = None
    motorista_id: Optional[int] = None
    km_saida: Optional[float] = None
    km_chegada: Optional[float] = None

class TransporteViagemCreate(TransporteViagemBase):
    pass

class TransporteViagem(TransporteViagemBase):
    id: int
    viagem_id: int
    veiculo: Optional[Veiculo] = None
    motorista: Optional[Usuario] = None

    class Config:
        from_attributes = True


# Schemas para Despesa
class DespesaBase(BaseModel):
    valor: float
    forma_pagamento: str
    descricao: str
    criado_por_id: Optional[int] = None
    pago_por_id: Optional[int] = None
    tipo_pagamento: Optional[str] = "INDIVIDUAL"
    registrado_para_id: Optional[int] = None

class DespesaCreate(DespesaBase):
    pass


class DespesaUpdate(BaseModel):
    valor: Optional[float] = None
    forma_pagamento: Optional[str] = None
    descricao: Optional[str] = None
    criado_por_id: Optional[int] = None
    pago_por_id: Optional[int] = None
    tipo_pagamento: Optional[str] = None
    registrado_para_id: Optional[int] = None
    comprovante_url: Optional[str] = None


class DespesaRateioBase(BaseModel):
    usuario_id: int
    valor: float


class DespesaRateio(DespesaRateioBase):
    id: int
    despesa_id: int
    data_criacao: datetime

    class Config:
        from_attributes = True


class Despesa(DespesaBase):
    id: int
    viagem_id: int
    comprovante_url: Optional[str] = None
    data_registro: datetime
    rateios: List[DespesaRateio] = []
    criado_por: Optional[Usuario] = None

    class Config:
        from_attributes = True

# Schemas para Pausa
class PausaBase(BaseModel):
    motivo: str

class PausaCreate(PausaBase):
    inicio: Optional[datetime] = None

class Pausa(PausaBase):
    id: int
    atividade_id: int
    inicio: datetime
    fim: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schemas para Atividade
class AtividadeBase(BaseModel):
    descricao: str

class AtividadeCreate(AtividadeBase):
    usuario_id: int

class AtividadeUpdate(BaseModel):
    descricao: Optional[str] = None

class Atividade(AtividadeBase):
    id: int
    viagem_id: int
    usuario_id: int
    ordem: Optional[int] = None
    inicio: Optional[datetime] = None
    fim: Optional[datetime] = None
    status: str
    pausas: List[Pausa] = []

    class Config:
        from_attributes = True


class AtividadeReorder(BaseModel):
    atividade_ids: List[int]

# Schemas para Viagem
class ViagemBase(BaseModel):
    motivo: str
    clientes: List[str]
    data_hora_prevista_saida: datetime
    data_hora_prevista_retorno: datetime
    meio_transporte: str
    obs_interna: Optional[str] = None
    obs_geral: Optional[str] = None
    responsavel_id: Optional[int] = None

class ViagemCreate(ViagemBase):
    participantes_ids: List[int]
    transporte: Optional[TransporteViagemCreate] = None


class ViagemUpdate(BaseModel):
    motivo: Optional[str] = None
    clientes: Optional[List[str]] = None
    data_hora_prevista_saida: Optional[datetime] = None
    data_hora_prevista_retorno: Optional[datetime] = None
    meio_transporte: Optional[str] = None
    obs_interna: Optional[str] = None
    obs_geral: Optional[str] = None
    responsavel_id: Optional[int] = None
    participantes_ids: Optional[List[int]] = None
    transporte: Optional[TransporteViagemCreate] = None


class Viagem(ViagemBase):
    id: int
    status: str
    data_criacao: datetime
    data_hora_real_saida: Optional[datetime] = None
    data_hora_real_chegada: Optional[datetime] = None
    participantes: List[Usuario] = []
    transporte: Optional[TransporteViagem] = None
    despesas: List[Despesa] = []
    atividades: List[Atividade] = []

    class Config:
        from_attributes = True


class RelatorioViagem(BaseModel):
    viagem: Viagem
    distancia_percorrida_km: float
    total_horas_trabalhadas: str
    total_despesas: float


class AppConfig(BaseModel):
    expense_photo_required: bool
    expense_description_options: List[str]
    activity_edit_delete_allowed_statuses: List[str]
    trip_edit_blocked_statuses: List[str]
    trip_activity_expense_allowed_statuses: List[str]
    trips_show_all_admin: bool
    trips_show_all_colaborador: bool


class AppConfigUpdate(BaseModel):
    expense_photo_required: Optional[bool] = None
    expense_description_options: Optional[List[str]] = None
    activity_edit_delete_allowed_statuses: Optional[List[str]] = None
    trip_edit_blocked_statuses: Optional[List[str]] = None
    trip_activity_expense_allowed_statuses: Optional[List[str]] = None
    trips_show_all_admin: Optional[bool] = None
    trips_show_all_colaborador: Optional[bool] = None
