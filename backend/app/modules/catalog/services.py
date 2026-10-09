from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from app.models.catalog import ItemCatalogo

# Modelo liviano ejecutado en CPU local (RNF06)
embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def buscar_items_semanticos(db: Session, query: str, limit: int = 5):
    # 1. Genera el vector localmente
    query_vector = embedder.encode(query).tolist()
    
    # 2. Búsqueda semántica usando pgvector (distancia coseno)
    resultados = db.query(ItemCatalogo).filter(
        ItemCatalogo.activo == True
    ).order_by(
        ItemCatalogo.embedding.cosine_distance(query_vector)
    ).limit(limit).all()
    
    return resultados