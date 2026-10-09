from sqlalchemy.orm import Session
from app.models.quotes import Cotizacion, CotizacionItem, Auditoria, ConfiguracionEmpresa
from typing import List, Dict, Any, Optional

TRANSICIONES_VALIDAS = {
    "borrador": ["enviada", "cancelada"],
    "enviada": ["aceptada", "rechazada", "vencida", "cancelada"],
    "aceptada": [],
    "rechazada": ["borrador"], # Permite reabrir/renegociar
    "vencida": ["borrador"],
    "cancelada": []
}

def calcular_totales_cotizacion(items_data: List[Dict[str, Any]], descuento_global_pct: float = 0.0, iva_pct: float = 19.0):
    """
    Motor de cálculo en tiempo real:
    Subtotal, Descuentos, IVA, Total y Margen porcentual ponderado.
    """
    subtotal = 0.0
    costo_total = 0.0

    lineas_calculadas = []
    for item in items_data:
        cant = float(item.get("cantidad", 1))
        precio_u = float(item.get("precio_unitario", 0))
        costo_u = float(item.get("costo_unitario", 0))
        desc_linea = float(item.get("descuento_pct", 0))

        subtotal_linea = cant * precio_u
        monto_desc = subtotal_linea * (desc_linea / 100.0)
        total_linea = subtotal_linea - monto_desc

        subtotal += total_linea
        costo_total += (cant * costo_u)

        lineas_calculadas.append({
            "item_id": item.get("item_id"),
            "cantidad": cant,
            "precio_unitario": precio_u,
            "costo_unitario": costo_u,
            "descuento_pct": desc_linea,
            "total_linea": total_linea
        })

    monto_descuento_global = subtotal * (descuento_global_pct / 100.0)
    base_gravable = subtotal - monto_descuento_global
    monto_iva = base_gravable * (iva_pct / 100.0)
    total_final = base_gravable + monto_iva

    # Cálculo del margen comercial: (Venta_sin_IVA - Costo) / Venta_sin_IVA * 100
    if base_gravable > 0:
        margen_pct = round(((base_gravable - costo_total) / base_gravable) * 100.0, 2)
    else:
        margen_pct = 0.0

    return {
        "subtotal": round(subtotal, 2),
        "descuento_global": round(monto_descuento_global, 2),
        "iva": round(monto_iva, 2),
        "total": round(total_final, 2),
        "costo_total": round(costo_total, 2),
        "margen_calculado": margen_pct,
        "lineas": lineas_calculadas
    }

def cambiar_estado_cotizacion(db: Session, cotizacion_id: int, nuevo_estado: str, usuario_id: int) -> Cotizacion:
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not cotizacion:
        raise ValueError("Cotización no encontrada")

    estado_actual = cotizacion.estado
    if nuevo_estado not in TRANSICIONES_VALIDAS.get(estado_actual, []):
        raise ValueError(f"Transición de estado inválida de '{estado_actual}' a '{nuevo_estado}'")

    # Registrar en auditoría
    auditoria = Auditoria(
        entidad="cotizaciones",
        entidad_id=cotizacion.id,
        accion="cambio_estado",
        valor_anterior=estado_actual,
        valor_nuevo=nuevo_estado,
        usuario_id=usuario_id
    )
    db.add(auditoria)

    cotizacion.estado = nuevo_estado
    db.commit()
    db.refresh(cotizacion)
    return cotizacion
