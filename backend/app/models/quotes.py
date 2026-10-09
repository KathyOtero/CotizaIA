from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(String, default="vendedor")  # 'administrador' o 'vendedor'
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cotizaciones = relationship("Cotizacion", back_populates="usuario")

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    documento = Column(String, unique=True, index=True, nullable=False) # NIT o Cédula
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    notas = Column(Text, nullable=True)
    consentimiento_datos = Column(Boolean, default=True) # Cumplimiento Ley 1581 Habeas Data
    created_at = Column(DateTime, default=datetime.utcnow)

    cotizaciones = relationship("Cotizacion", back_populates="cliente")

class ConfiguracionEmpresa(Base):
    __tablename__ = "configuracion_empresa"

    id = Column(Integer, primary_key=True, index=True)
    nombre_empresa = Column(String, nullable=False, default="Mi Pyme de Servicios")
    nit = Column(String, nullable=False, default="900.123.456-7")
    margen_minimo_pct = Column(Float, default=25.0) # Alerta si cae por debajo
    iva_default_pct = Column(Float, default=19.0)
    moneda = Column(String, default="COP")
    logo_url = Column(String, nullable=True)
    pie_pagina_pdf = Column(Text, default="Validez de la oferta: 15 días calendario. Forma de pago: 50% anticipo, 50% contra entrega.")

class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True) # Ej: COT-2026-001
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Máquina de estados: borrador -> enviada -> (aceptada | rechazada | vencida | cancelada)
    estado = Column(String, default="borrador", index=True)
    
    fecha_emision = Column(Date, default=datetime.utcnow().date)
    fecha_vencimiento = Column(Date, nullable=True)
    
    subtotal = Column(Float, default=0.0)
    descuento_global = Column(Float, default=0.0)
    iva = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    margen_calculado = Column(Float, default=0.0) # Margen promedio ponderado
    
    notas = Column(Text, nullable=True)
    origen_asistido_ia = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="cotizaciones")
    usuario = relationship("Usuario", back_populates="cotizaciones")
    items = relationship("CotizacionItem", back_populates="cotizacion", cascade="all, delete-orphan")

class CotizacionItem(Base):
    __tablename__ = "cotizacion_items"

    id = Column(Integer, primary_key=True, index=True)
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items_catalogo.id"), nullable=False)
    
    cantidad = Column(Float, default=1.0)
    # Precios históricos congelados al momento de cotizar (no alteran si el catálogo cambia)
    precio_unitario = Column(Float, nullable=False)
    costo_unitario = Column(Float, nullable=False)
    descuento_pct = Column(Float, default=0.0)
    total_linea = Column(Float, nullable=False)

    cotizacion = relationship("Cotizacion", back_populates="items")
    item = relationship("ItemCatalogo")

# Tablas separadas para Human-in-the-Loop (Guardrails de IA: RF22, RF23, RNF09)
class BorradorIA(Base):
    __tablename__ = "borradores_ia"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    prompt_usuario = Column(Text, nullable=False)
    estado = Column(String, default="pendiente") # 'pendiente', 'aceptado', 'descartado'
    created_at = Column(DateTime, default=datetime.utcnow)

    sugerencias = relationship("SugerenciaIA", back_populates="borrador", cascade="all, delete-orphan")

class SugerenciaIA(Base):
    __tablename__ = "sugerencias_ia"

    id = Column(Integer, primary_key=True, index=True)
    borrador_id = Column(Integer, ForeignKey("borradores_ia.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items_catalogo.id"), nullable=False)
    cantidad_sugerida = Column(Float, default=1.0)
    descuento_sugerido = Column(Float, default=0.0)
    justificacion_ia = Column(String, nullable=True)
    estado = Column(String, default="sugerida") # 'sugerida', 'aceptada', 'descartada'

    borrador = relationship("BorradorIA", back_populates="sugerencias")
    item = relationship("ItemCatalogo")

class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    entidad = Column(String, nullable=False) # 'cotizaciones', 'items_catalogo'
    entidad_id = Column(Integer, nullable=False)
    accion = Column(String, nullable=False) # 'creacion', 'cambio_estado', 'cambio_precio'
    valor_anterior = Column(Text, nullable=True)
    valor_nuevo = Column(Text, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
