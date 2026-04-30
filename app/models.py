from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Table, func, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from .database import Base

viagem_usuarios = Table('viagem_usuarios', Base.metadata,
    Column('viagem_id', Integer, ForeignKey('viagens.id'), primary_key=True),
    Column('usuario_id', Integer, ForeignKey('usuarios.id'), primary_key=True)
)

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    senha = Column(String)
    tipousuario = Column(String)
    tem_cnh = Column(Boolean, default=False)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    viagens = relationship("Viagem", secondary=viagem_usuarios, back_populates="participantes")

class Veiculo(Base):
    __tablename__ = "veiculos"
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, unique=True, index=True)
    modelo = Column(String)
    marca = Column(String)
    ano = Column(Integer)

class Viagem(Base):
    __tablename__ = "viagens"
    id = Column(Integer, primary_key=True, index=True)
    responsavel_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    motivo = Column(String)
    data_hora_prevista_saida = Column(DateTime)
    data_hora_prevista_retorno = Column("data_hora_prevista_chegada", DateTime)
    data_hora_real_saida = Column(DateTime, nullable=True)
    data_hora_real_chegada = Column(DateTime, nullable=True)
    meio_transporte = Column(String)
    status = Column(String, default="planejada")
    obs_interna = Column(String, nullable=True)
    obs_geral = Column(String, nullable=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    participantes = relationship("Usuario", secondary=viagem_usuarios, back_populates="viagens")
    responsavel = relationship("Usuario", foreign_keys=[responsavel_id])
    transporte = relationship("TransporteViagem", back_populates="viagem", uselist=False)
    despesas = relationship("Despesa", back_populates="viagem")
    atividades = relationship("Atividade", back_populates="viagem", order_by="Atividade.ordem, Atividade.id")
    clientes_itens = relationship(
        "ViagemCliente",
        back_populates="viagem",
        cascade="all, delete-orphan",
        order_by="ViagemCliente.id",
    )

    @property
    def clientes(self):
        return [c.nome for c in (self.clientes_itens or [])]


class ViagemCliente(Base):
    __tablename__ = "viagem_clientes"
    id = Column(Integer, primary_key=True, index=True)
    viagem_id = Column(Integer, ForeignKey("viagens.id", ondelete="CASCADE"))
    nome = Column(String)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())

    viagem = relationship("Viagem", back_populates="clientes_itens")

class TransporteViagem(Base):
    __tablename__ = "transporte_viagem"
    id = Column(Integer, primary_key=True, index=True)
    viagem_id = Column(Integer, ForeignKey("viagens.id"))
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=True)
    motorista_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    km_saida = Column(Float, nullable=True)
    km_chegada = Column(Float, nullable=True)
    viagem = relationship("Viagem", back_populates="transporte")
    veiculo = relationship("Veiculo")
    motorista = relationship("Usuario")

class Despesa(Base):
    __tablename__ = "despesas"
    id = Column(Integer, primary_key=True, index=True)
    viagem_id = Column(Integer, ForeignKey("viagens.id"))
    valor = Column(Float)
    forma_pagamento = Column(String)
    descricao = Column(String)
    criado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    pago_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tipo_pagamento = Column(String, default="INDIVIDUAL")
    registrado_para_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    comprovante_url = Column(String, nullable=True)
    data_registro = Column(DateTime(timezone=True), server_default=func.now())
    viagem = relationship("Viagem", back_populates="despesas")
    criado_por = relationship("Usuario", foreign_keys=[criado_por_id])
    pago_por = relationship("Usuario", foreign_keys=[pago_por_id])
    registrado_para = relationship("Usuario", foreign_keys=[registrado_para_id])
    rateios = relationship("DespesaRateio", back_populates="despesa")


class DespesaRateio(Base):
    __tablename__ = "despesa_rateio"
    id = Column(Integer, primary_key=True, index=True)
    despesa_id = Column(Integer, ForeignKey("despesas.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    valor = Column(Float)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    despesa = relationship("Despesa", back_populates="rateios")
    usuario = relationship("Usuario")

class Atividade(Base):
    __tablename__ = "atividades"
    id = Column(Integer, primary_key=True, index=True)
    viagem_id = Column(Integer, ForeignKey("viagens.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    ordem = Column(Integer, nullable=False)
    inicio = Column(DateTime, nullable=True)
    fim = Column(DateTime, nullable=True)
    descricao = Column(String)
    status = Column(String, default="pendente") # pendente, ativa, pausada, finalizada
    viagem = relationship("Viagem", back_populates="atividades")
    usuario = relationship("Usuario")
    pausas = relationship("Pausa", back_populates="atividade")

class Pausa(Base):
    __tablename__ = "pausas"
    id = Column(Integer, primary_key=True, index=True)
    atividade_id = Column(Integer, ForeignKey("atividades.id"))
    inicio = Column(DateTime)
    fim = Column(DateTime, nullable=True)
    motivo = Column(String)
    atividade = relationship("Atividade", back_populates="pausas")


class AppConfig(Base):
    __tablename__ = "app_config"
    id = Column(Integer, primary_key=True, index=True)
    expense_photo_required = Column(Boolean, default=False)
    report_include_receipts = Column(Boolean, default=True)
    trip_allow_manual_arrival_datetime = Column(Boolean, default=False)
    expense_description_options = Column(String, default='["Almoço","Janta","Lanche","Hospedagem","Taxi/Uber","Estacionamento","Pedágio","Combustível","Locação"]')
    activity_edit_delete_allowed_statuses = Column(String, default='["pendente"]')
    ia_provider = Column(String, default="anthropic")
    ia_model_anthropic = Column(String, default="claude-sonnet-4-6")
    ia_model_gemini = Column(String, default="gemini-2.5-flash")
    anthropic_api_key_enc = Column(String, nullable=True)
    anthropic_api_key_last4 = Column(String, nullable=True)
    gemini_api_key_enc = Column(String, nullable=True)
    gemini_api_key_last4 = Column(String, nullable=True)
    trip_edit_blocked_statuses = Column(String, default='["em_andamento","finalizada","cancelada"]')
    trip_activity_expense_allowed_statuses = Column(String, default='["em_andamento"]')
    trips_show_all_admin = Column(Boolean, default=True)
    trips_show_all_colaborador = Column(Boolean, default=True)


class IALog(Base):
    __tablename__ = "ia_log"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    tipo = Column(String, nullable=False, index=True)

    mensagem_usuario = Column(Text, nullable=True)
    ferramentas_chamadas = Column(JSON, nullable=True)

    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    tokens_cache_read = Column(Integer, nullable=True)
    custo_estimado_usd = Column(Float, nullable=True)
    latencia_ms = Column(Integer, nullable=True)

    sucesso = Column(Boolean, nullable=False, default=False, index=True)
    erro = Column(String, nullable=True)

    usuario = relationship("Usuario")
