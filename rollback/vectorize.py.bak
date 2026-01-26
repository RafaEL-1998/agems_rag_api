import math
from pyodide.ffi import to_js
from js import Object

def sanitize_embedding(embedding):
    """
    Garante que o embedding seja uma lista de floats válidos.
    Remove NaNs e Infinitos.
    """
    try:
        clean = []
        for x in embedding:
            xf = float(x)
            if math.isnan(xf) or math.isinf(xf):
                return None
            clean.append(xf)
        return clean
    except:
        return None

async def process_and_vectorize_chunks(env, document_id, doc_metadata, chunks):
    """
    Recebe chunks com embeddings JÁ GERADOS e insere no Vectorize.
    Aplica sanitização rigorosa para evitar erros de formato.
    """
    vectors = []

    for chunk in chunks:
        # 1. Sanitização do Embedding
        emb = sanitize_embedding(chunk["embedding"])
        if emb is None:
            print(f"WARN: Chunk {chunk.get('id')} descartado por embedding inválido/NaN")
            continue

        # 2. Construção do Objeto Vetor
        vector_obj = {
            "id": f"{document_id}-{chunk['id']}",
            "values": emb,
            "metadata": {
                "document_id": str(document_id),
                "title": str(doc_metadata.get("title", "Unknown")),
                "type": str(doc_metadata.get("type", "Document")),
                "sector": str(doc_metadata.get("sector", "General")),
                "text": str(chunk.get("text", "")),
                "chunk_index": chunk.get("chunk_index", 0),
                # Incorporar metadados extras removendo Nones
                **{k: v for k, v in chunk.get("metadata", {}).items() if v is not None}
            }
        }
        vectors.append(vector_obj)

    if not vectors:
        print("WARN: Nenhum vetor válido para inserir neste lote.")
        return 0

    # 3. DEBUG CRÍTICO (Amostragem)
    # print(f"DEBUG VECTOR SAMPLE: ID={vectors[0]['id']} DIMS={len(vectors[0]['values'])}")

    # 4. Inserção no Vectorize
    # Usamos dict_converter=Object.fromEntries para garantir que dicts Python virem Objetos JS (e não Maps)
    # O método é .insert() (que atua como upsert no Cloudflare Vectorize)
    await env.VECTORIZE.insert(to_js(vectors, dict_converter=Object.fromEntries))
    
    print(f"DEBUG: {len(vectors)} vetores inseridos com sucesso!")
    return len(vectors)
