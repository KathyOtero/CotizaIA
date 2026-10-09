-- Inicialización de base de datos PostgreSQL con extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificación de instalación
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
