import json
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.catalog import ItemCatalogo
from app.models.quotes import BorradorIA, SugerenciaIA
from app.modules.catalog.services import buscar_items_semanticos
from app.modules.quotes.services import calcular_totales_cotizacion

class LLMProvider:
    """Interfaz desacoplada para proveedores de LLM (Groq, Gemini, Local)"""
    def interpretar_requerimiento(self, prompt: str, catalogo_recuperado: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raise NotImplementedError

class MockLocalLLMProvider(LLMProvider):
    """
    Proveedor de fallback y demo local:
    Analiza la descripción del usuario en lenguaje natural extrayendo números de cantidades
    y mapeándolos contra los ítems recuperados semánticamente por pgvector.
    No requiere API key externa y garantiza $0 de costo.
    """
    def interpretar_requerimiento(self, prompt: str, catalogo_recuperado: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Intentar extraer números del prompt para asignar cantidades inteligentes
        numeros = [float(n) for n in re.findall(r'\b\d+\b', prompt)]
        cantidad_default = numeros[0] if numeros else 1.0

        sugerencias = []
        for i, item in enumerate(catalogo_recuperado):
            cant = numeros[i] if i < len(numeros) else cantidad_default
            sugerencias.append({
                "item_id": item["id"],
                "nombre": item["nombre"],
                "cantidad": cant,
                "precio_unitario": item["precio_venta"],
                "costo_unitario": item["costo"],
                "descuento_pct": 0.0,
                "justificacion": f"Coincidencia semántica con requerimiento: '{item['nombre']}'"
            })
        return sugerencias

def generar_borrador_asistido(
    db: Session,
    prompt: str,
    cliente_id: int,
    usuario_id: int,
    llm: Optional[LLMProvider] = None
) -> Dict[str, Any]:
    """
    Flujo Asistido con IA (Human-in-the-Loop):
    1. Búsqueda semántica en catálogo (embeddings locales en CPU).
    2. Redacción/extracción estructurada (LLM desacoplado).
    3. Almacenamiento exclusivo en tablas temporales: borradores_ia y sugerencias_ia.
    4. Cálculo de totales y margen en tiempo real.
    5. Retorna borrador claramente identificado como 'Sugerido por IA'.
    """
    if llm is None:
        llm = MockLocalLLMProvider()

    # 1. Recuperación semántica
    items_bd = buscar_items_semanticos(db, query=prompt, limit=4)
    catalogo_items = [
        {
            "id": it.id,
            "nombre": it.nombre,
            "descripcion": it.descripcion,
            "unidad": it.unidad,
            "costo": it.costo,
            "precio_venta": it.precio_venta
        }
        for it in items_bd
    ]

    # 2. Interpretación de la solicitud
    sugerencias = llm.interpretar_requerimiento(prompt, catalogo_items)

    # 3. Guardar en tablas separadas de guardrails (NO escribe en cotizaciones oficiales)
    borrador = BorradorIA(
        usuario_id=usuario_id,
        cliente_id=cliente_id,
        prompt_usuario=prompt,
        estado="pendiente"
    )
    db.add(borrador)
    db.flush()

    for sug in sugerencias:
        sug_db = SugerenciaIA(
            borrador_id=borrador.id,
            item_id=sug["item_id"],
            cantidad_sugerida=sug["cantidad"],
            descuento_sugerido=sug.get("descuento_pct", 0.0),
            justificacion_ia=sug.get("justificacion", "Sugerencia automática de IA")
        )
        db.add(sug_db)
    
    db.commit()
    db.refresh(borrador)

    # 4. Calcular totales provisionales
    totales = calcular_totales_cotizacion(sugerencias, descuento_global_pct=0.0, iva_pct=19.0)

    return {
        "borrador_id": borrador.id,
        "prompt": prompt,
        "items_sugeridos": sugerencias,
        "calculo_provisional": totales,
        "distintivo_ia": True,
        "advertencia": "Borrador preliminar generado con IA. Requiere confirmación humana antes de ser emitido."
    }
