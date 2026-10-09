# CotizaAI — Asistente de Cotizaciones con IA para PYMES

> Plataforma web de gestión de clientes, catálogo y cotizaciones comerciales asistida por IA generativa con supervisión humana estricta (*Human-in-the-Loop*), costo de infraestructura de **$0** y búsqueda semántica local.

**Universidad Tecnológica de Bolívar (UTB) — Proyecto de Ingeniería I**  
**Docente:** Prof. Aisner Marrugo  
**Equipo:** Juan Diego Serpa Medina, Kathy Luz Otero Pérez, Jesús David Julio Hawasly  

---

## 🌟 Características Principales

* **Asistente en Lenguaje Natural (Human-in-the-Loop):** Transforma requerimientos comerciales informales en borradores de cotización con precios reales de catálogo. La IA **solo sugiere**; nunca fija precios ni aprueba descuentos de forma autónoma (RF22, RF23).
* **Búsqueda Semántica Local:** Búsqueda por significado en el catálogo propio usando `sentence-transformers` (384 dimensiones) y la extensión `pgvector` en PostgreSQL 16.
* **Control y Alertas de Margen:** Motor de cálculo en tiempo real que protege la rentabilidad de la empresa alertando si una cotización cae por debajo del margen mínimo configurable (ej. 25%).
* **Máquina de Estados & Trazabilidad:** Ciclo de vida comercial (`borrador` &rarr; `enviada` &rarr; `aceptada` / `rechazada` / `vencida`) con auditoría completa de cambios.
* **Generación de PDF Oficial:** Emisión de cotizaciones formales con membrete y términos comerciales.
* **Costo de Operación $0:** Componentes de código abierto, embeddings en CPU local y LLMs externos en capa gratuita con política de degradación elegante (*fallback*).

---

## 🚀 Prototipo Navegable (Entrega Avance 3)

Puedes explorar y probar la experiencia de usuario interactiva del producto de dos formas:

### Opción A: Abrir directamente en el navegador (Sin dependencias)
Abre el archivo [`frontend/index.html`](frontend/index.html) con doble clic en Google Chrome o Microsoft Edge.

### Opción B: Ejecutar con servidor local
```bash
# Con Python
cd frontend
python -m http.server 3000
# Abrir http://localhost:3000 en tu navegador
```

---

## 🏗️ Arquitectura y Tecnologías

```
[ Frontend: React / HTML / Tailwind ]
                   │
                   ▼ (HTTP / REST)
[ Backend: FastAPI (Python 3.12) - Monolito Modular ]
   ├── Módulos: Auth, Clientes, Catálogo, Cotizaciones, Asistente IA, Auditoría
   ├── Embeddings: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2 en CPU)
   └── LLM desacoplado: Interfaz abstracta LLMProvider (Groq / Gemini Free Tier)
                   │
                   ▼ (SQLAlchemy + pgvector)
[ Base de Datos: PostgreSQL 16 + Extensión Vector ]
   ├── items_catalogo (embedding vector(384))
   └── borradores_ia & sugerencias_ia (Aislamiento de Guardrails)
```

---

## 📦 Ejecución con Docker Compose

```bash
# 1. Clonar el repositorio
git clone https://github.com/KathyOtero/CotizaIA.git
cd CotizaIA

# 2. Levantar servicios (PostgreSQL + pgvector, Backend, Frontend)
docker compose -f infrastructure/docker-compose.yml up -d

# 3. Sembrar datos de prueba iniciales
docker compose -f infrastructure/docker-compose.yml exec backend python app/scripts/seed_data.py
```

* **Frontend:** `http://localhost:3000`
* **API Backend & Documentación Swagger:** `http://localhost:8000/docs`

---

## 📄 Documentación Entregable

* [Documento Completo de Avance 3](docs/Avance3_CotizaAI.md): Flujos de usuario, diagramas de arquitectura, modelo de datos y justificación de alcance.
