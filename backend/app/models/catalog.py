from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class ItemCatalogo(Base):
    __tablename__ = "items_catalogo"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text)
    unidad = Column(String, default="Unidad")
    categoria = Column(String)
    costo = Column(Float, nullable=False)
    precio_venta = Column(Float, nullable=False)
    activo = Column(Boolean, default=True)
    # Columna vectorial para la búsqueda semántica (384 dimensiones)
    embedding = Column(Vector(384))
    indexado = Column(Boolean, default=False)