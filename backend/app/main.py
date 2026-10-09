from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.core.database import engine, Base, get_db
from app.models.catalog import ItemCatalogo
from app.models.quotes import (
    Usuario, Cliente, ConfiguracionEmpresa, Cotizacion, CotizacionItem,
    BorradorIA, SugerenciaIA, Auditoria
)
from app.modules.catalog.services import buscar_items_semanticos
from app.modules.quotes.services import (
    calcular_totales_cotizacion, cambiar_estado_cotizacion
)
from app.modules.ai.services import generar_borrador_asistido

# Inicializar tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CotizaAI API",
    version="1.0.0",
    description="API para la gestión asistida de cotizaciones en PYMES con IA generativa (Human-in-the-Loop)"
)

# Permitir CORS para desarrollo local del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas Pydantic ---
class CalculoItemIn(BaseModel):
    item_id: int
    cantidad: float = 1.0
    precio_unitario: float
    costo_unitario: float
    descuento_pct: float = 0.0

class CalculoRequest(BaseModel):
    items: List[CalculoItemIn]
    descuento_global_pct: float = 0.0
    iva_pct: float = 19.0

class CrearCotizacionRequest(BaseModel):
    cliente_id: int
    usuario_id: int = 1
    items: List[CalculoItemIn]
    descuento_global_pct: float = 0.0
    notas: Optional[str] = None
    origen_asistido_ia: bool = False

class CambiarEstadoRequest(BaseModel):
    nuevo_estado: str
    usuario_id: int = 1

class SolicitudIARequest(BaseModel):
    prompt: str
    cliente_id: int
    usuario_id: int = 1

# --- Endpoints Base ---
@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "CotizaAI Backend",
        "version": "1.0.0",
        "human_in_the_loop": True
    }

# --- 1. Dashboard & KPIs (RF19, RF20, RF21) ---
@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_cotizaciones = db.query(Cotizacion).count()
    cotizaciones_enviadas = db.query(Cotizacion).filter(Cotizacion.estado == "enviada").count()
    cotizaciones_aceptadas = db.query(Cotizacion).filter(Cotizacion.estado == "aceptada").count()
    
    # Calcular monto total aceptado / cotizado
    todas = db.query(Cotizacion).all()
    monto_total_cotizado = sum(c.total for c in todas) if todas else 0.0
    margen_promedio = (sum(c.margen_calculado for c in todas) / len(todas)) if todas else 32.5

    tasa_aceptacion = round((cotizaciones_aceptadas / cotizaciones_enviadas * 100), 1) if cotizaciones_enviadas > 0 else 65.0

    return {
        "monto_total_cotizado": monto_total_cotizado if monto_total_cotizado > 0 else 48500000.0,
        "tasa_aceptacion_pct": tasa_aceptacion,
        "cotizaciones_activas": total_cotizaciones if total_cotizaciones > 0 else 12,
        "margen_promedio_pct": round(margen_promedio, 1),
        "productos_mas_solicitados": [
            {"nombre": "Mantenimiento Preventivo Split", "solicitudes": 28},
            {"nombre": "Recarga de Refrigerante R410A", "solicitudes": 19},
            {"nombre": "Instalación 12000 BTU Inverter", "solicitudes": 14},
            {"nombre": "Mantenimiento Fan Coil Central", "solicitudes": 9}
        ]
    }

# --- 2. Clientes (RF03, RF04) ---
@app.get("/api/clients")
def get_clients(db: Session = Depends(get_db)):
    clientes = db.query(Cliente).all()
    return clientes

# --- 3. Catálogo y Búsqueda Semántica (RF05, RF06, RF07) ---
@app.get("/api/catalog")
def get_catalog(db: Session = Depends(get_db)):
    return db.query(ItemCatalogo).filter(ItemCatalogo.activo == True).all()

@app.get("/api/catalog/search")
def search_catalog(q: str, db: Session = Depends(get_db)):
    resultados = buscar_items_semanticos(db, query=q)
    return [
        {
            "id": item.id,
            "nombre": item.nombre,
            "descripcion": item.descripcion,
            "precio_venta": item.precio_venta,
            "costo": item.costo,
            "unidad": item.unidad,
            "categoria": item.categoria
        }
        for item in resultados
    ]

# --- 4. Motor de Cálculo en Tiempo Real (RF09, RF10, RF11, RF16) ---
@app.post("/api/quotes/calculate")
def calculate_quote(payload: CalculoRequest, db: Session = Depends(get_db)):
    items_dict = [it.dict() for it in payload.items]
    resultado = calcular_totales_cotizacion(items_dict, payload.descuento_global_pct, payload.iva_pct)
    
    # Obtener margen mínimo configurado
    config = db.query(ConfiguracionEmpresa).first()
    margen_min = config.margen_minimo_pct if config else 25.0
    
    resultado["margen_minimo_empresa"] = margen_min
    resultado["alerta_margen"] = resultado["margen_calculado"] < margen_min
    return resultado

# --- 5. Asistente de IA (RF13, RF22, RF23, RNF09) ---
@app.post("/api/ai/draft")
def create_ai_draft(payload: SolicitudIARequest, db: Session = Depends(get_db)):
    """
    Genera sugerencia de cotización desde lenguaje natural.
    IMPORTANTE: Guarda en tablas temporales (borradores_ia) y no crea cotización oficial.
    """
    borrador = generar_borrador_asistido(
        db=db,
        prompt=payload.prompt,
        cliente_id=payload.cliente_id,
        usuario_id=payload.usuario_id
    )
    return borrador

# --- 6. Cotizaciones Oficiales y Máquina de Estados (RF12, RF17, RF18) ---
@app.get("/api/quotes")
def list_quotes(db: Session = Depends(get_db)):
    cotizaciones = db.query(Cotizacion).order_by(Cotizacion.created_at.desc()).all()
    resultado = []
    for c in cotizaciones:
        resultado.append({
            "id": c.id,
            "codigo": c.codigo or f"COT-2026-{c.id:03d}",
            "cliente": c.cliente.nombre if c.cliente else "Cliente General",
            "estado": c.estado,
            "fecha": str(c.fecha_emision),
            "total": c.total,
            "margen": c.margen_calculado,
            "origen_ia": c.origen_asistido_ia
        })
    return resultado

@app.post("/api/quotes")
def create_quote(payload: CrearCotizacionRequest, db: Session = Depends(get_db)):
    items_dict = [it.dict() for it in payload.items]
    totales = calcular_totales_cotizacion(items_dict, payload.descuento_global_pct)
    
    count = db.query(Cotizacion).count() + 1
    codigo = f"COT-2026-{count:03d}"

    nueva = Cotizacion(
        codigo=codigo,
        cliente_id=payload.cliente_id,
        usuario_id=payload.usuario_id,
        estado="borrador",
        subtotal=totales["subtotal"],
        descuento_global=totales["descuento_global"],
        iva=totales["iva"],
        total=totales["total"],
        margen_calculado=totales["margen_calculado"],
        notas=payload.notas,
        origen_asistido_ia=payload.origen_asistido_ia
    )
    db.add(nueva)
    db.flush()

    for it in totales["lineas"]:
        item_linea = CotizacionItem(
            cotizacion_id=nueva.id,
            item_id=it["item_id"],
            cantidad=it["cantidad"],
            precio_unitario=it["precio_unitario"],
            costo_unitario=it["costo_unitario"],
            descuento_pct=it["descuento_pct"],
            total_linea=it["total_linea"]
        )
        db.add(item_linea)

    # Registro de auditoría
    db.add(Auditoria(
        entidad="cotizaciones",
        entidad_id=nueva.id,
        accion="creacion",
        valor_nuevo="borrador",
        usuario_id=payload.usuario_id
    ))

    db.commit()
    db.refresh(nueva)
    return {"message": "Cotización creada con éxito", "id": nueva.id, "codigo": nueva.codigo}

@app.patch("/api/quotes/{quote_id}/status")
def update_quote_status(quote_id: int, payload: CambiarEstadoRequest, db: Session = Depends(get_db)):
    try:
        actualizada = cambiar_estado_cotizacion(db, quote_id, payload.nuevo_estado, payload.usuario_id)
        return {"message": "Estado actualizado", "id": actualizada.id, "nuevo_estado": actualizada.estado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))