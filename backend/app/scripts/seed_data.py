import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.models.catalog import ItemCatalogo
from app.models.quotes import Usuario, Cliente, ConfiguracionEmpresa, Cotizacion, CotizacionItem
from app.modules.catalog.services import embedder
from datetime import datetime, timedelta

def seed():
    print("Iniciando sembrado de datos de prueba para CotizaAI...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Configuración de la Empresa
        if not db.query(ConfiguracionEmpresa).first():
            config = ConfiguracionEmpresa(
                nombre_empresa="ClimaCaribe Soluciones S.A.S.",
                nit="901.458.789-2",
                margen_minimo_pct=25.0,
                iva_default_pct=19.0,
                moneda="COP",
                pie_pagina_pdf="Cotización válida por 15 días calendario. Precios sujetos a verificación de sitio."
            )
            db.add(config)
            print("Configuración de empresa creada.")

        # 2. Usuarios
        if not db.query(Usuario).first():
            admin = Usuario(
                nombre="Kathy Otero",
                email="admin@climacaribe.com",
                password_hash="$2b$12$e8Y6J9H9h3mG4P8F2J7a3.vV5m8f1O4v0n9b8v7c6x5z4y3x2w1",
                rol="administrador"
            )
            vendedor = Usuario(
                nombre="Juan Diego Serpa",
                email="vendedor@climacaribe.com",
                password_hash="$2b$12$e8Y6J9H9h3mG4P8F2J7a3.vV5m8f1O4v0n9b8v7c6x5z4y3x2w1",
                rol="vendedor"
            )
            db.add_all([admin, vendedor])
            print("Usuarios de prueba creados.")

        # 3. Clientes (MiPymes de Cartagena y Costa Caribe)
        if not db.query(Cliente).first():
            clientes = [
                Cliente(nombre="Hotel Caribe Plaza", documento="800.123.456-1", email="mantenimiento@hotelcaribe.com", telefono="3001234567", direccion="Bocagrande Cra 2 # 5-40, Cartagena"),
                Cliente(nombre="Restaurante La Cevichera", documento="900.234.567-2", email="gerencia@lacevichera.com", telefono="3109876543", direccion="Centro Histórico Calle de las Damas, Cartagena"),
                Cliente(nombre="Clínica del Prado Cartagena", documento="890.345.678-3", email="compras@clinicadelprado.com", telefono="3154567890", direccion="Manga Callejón Baloco, Cartagena"),
                Cliente(nombre="Edificio Puerta del Mar PH", documento="901.567.890-4", email="admin@puertadelmar.com", telefono="3017890123", direccion="Crespo Av Santander, Cartagena"),
                Cliente(nombre="Distribuidora Mamonal SAS", documento="806.789.012-5", email="logistica@distrimamonal.com", telefono="3206543210", direccion="Zona Industrial Mamonal Km 7, Cartagena")
            ]
            db.add_all(clientes)
            print("Clientes de prueba creados.")

        # 4. Catálogo de Productos y Servicios con Embeddings
        if not db.query(ItemCatalogo).first():
            items = [
                {"nombre": "Mantenimiento Preventivo Aire Acondicionado Split", "desc": "Limpieza profunda de serpentines, turbina, filtros, revisión de presiones y chequeo eléctrico", "unidad": "Servicio", "cat": "Climatización", "costo": 45000.0, "precio": 90000.0},
                {"nombre": "Mantenimiento Preventivo Aire Central / Fan Coil", "desc": "Mantenimiento de unidades centrales, lavado a presión de condensadoras y desinfección", "unidad": "Servicio", "cat": "Climatización", "costo": 95000.0, "precio": 180000.0},
                {"nombre": "Recarga de Gas Refrigerante R410A", "desc": "Suministro y carga de refrigerante ecológico R410A por libra con prueba de hermeticidad", "unidad": "Libra", "cat": "Repuestos", "costo": 30000.0, "precio": 65000.0},
                {"nombre": "Cambio de Capacitor de Arranque 45uF", "desc": "Suministro e instalación de capacitor de marcha para compresor de aire acondicionado", "unidad": "Unidad", "cat": "Repuestos", "costo": 25000.0, "precio": 60000.0},
                {"nombre": "Instalación de Aire Acondicionado 12000 BTU Inverter", "desc": "Instalación básica que incluye kit de tubería de cobre hasta 3 metros, ménsulas y vacío con bomba", "unidad": "Instalación", "cat": "Instalaciones", "costo": 120000.0, "precio": 250000.0},
                {"nombre": "Limpieza y Desinfección de Ductos de Aire", "desc": "Aplicación de bactericida grado hospitalario y cepillado mecánico de ductería interna", "unidad": "Metro lineal", "cat": "Climatización", "costo": 15000.0, "precio": 35000.0},
                {"nombre": "Reemplazo de Motor Ventilador Condensador", "desc": "Suministro y calibración de motor soplador para unidad exterior", "unidad": "Unidad", "cat": "Repuestos", "costo": 110000.0, "precio": 220000.0},
                {"nombre": "Revisión y Diagnóstico Técnico en Sitio", "desc": "Visita técnica especializada de levantamiento de falla y medición eléctrica", "unidad": "Visita", "cat": "Servicios", "costo": 20000.0, "precio": 50000.0}
            ]

            for it in items:
                # Generar embedding del nombre + descripción
                texto = f"{it['nombre']}: {it['desc']}"
                vec = embedder.encode(texto).tolist()
                nuevo_item = ItemCatalogo(
                    nombre=it["nombre"],
                    descripcion=it["desc"],
                    unidad=it["unidad"],
                    categoria=it["cat"],
                    costo=it["costo"],
                    precio_venta=it["precio"],
                    embedding=vec,
                    indexado=True
                )
                db.add(nuevo_item)
            print("Catálogo con embeddings indexados creado.")

        db.commit()
        print("¡Sembrado completado exitosamente!")
    except Exception as e:
        db.rollback()
        print(f"Error al sembrar datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
