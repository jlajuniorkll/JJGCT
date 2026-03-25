from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Table, func, Boolean
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
    cliente = Column(String)
    motivo = Column(String)
    local_partida = Column(String)
    local_chegada = Column(String)
    data_hora_prevista_saida = Column(DateTime)
    data_hora_prevista_chegada = Column(DateTime)
    data_hora_real_saida = Column(DateTime, nullable=True)
    data_hora_real_chegada = Column(DateTime, nullable=True)
    meio_transporte = Column(String)
    status = Column(String, default="planejada")
    obs_interna = Column(String, nullable=True)
    obs_geral = Column(String, nullable=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    participantes = relationship("Usuario", secondary=viagem_usuarios, back_populates="viagens")
    transporte = relationship("TransporteViagem", back_populates="viagem", uselist=False)
    despesas = relationship("Despesa", back_populates="viagem")
    atividades = relationship("Atividade", back_populates="viagem")

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
    comprovante_url = Column(String, nullable=True)
    data_registro = Column(DateTime(timezone=True), server_default=func.now())
    viagem = relationship("Viagem", back_populates="despesas")

class Atividade(Base):
    __tablename__ = "atividades"
    id = Column(Integer, primary_key=True, index=True)
    viagem_id = Column(Integer, ForeignKey("viagens.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
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
    trip_edit_blocked_statuses = Column(String, default='["em_andamento","finalizada","cancelada"]')
