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

async def generate_embeddings_for_chunks(env, chunks):
    """
    Gera embeddings para uma lista de chunks usando Workers AI
    """
    print(f"DEBUG: Gerando embeddings para {len(chunks)} chunks...")
    
    for chunk in chunks:
        # Pega o texto enriquecido se existir, senão o texto base
        text_to_embed = chunk.get("texto") or chunk.get("text")
        
        if not text_to_embed:
            continue
            
        try:
            ai_input = to_js({"text": [text_to_embed]}, dict_converter=Object.fromEntries)
            ai_res_proxy = await env.AI.run('@cf/baai/bge-m3', ai_input)
            ai_res = ai_res_proxy.to_py()
            
            if "result" in ai_res:
                embedding = ai_res["result"].get("data", [[]])[0]
            else:
                embedding = ai_res.get("data", [[]])[0]
                
            chunk["embedding"] = embedding
        except Exception as e:
            print(f"ERRO ao gerar embedding para chunk: {str(e)}")
            chunk["embedding"] = None
            
    return chunks

async def process_and_vectorize_chunks(env, document_id, doc_metadata, chunks, start_index=0, limit=None):
    """
    Recebe chunks, seleciona um lote, garante que tenham embeddings e insere no Vectorize.
    """
    # Se limit foi passado, pega apenas a fatia solicitada
    target_chunks = chunks[start_index : start_index + limit] if limit else chunks[start_index:]
    
    # 1. Garante embeddings (se não houver, gera)
    has_missing_embeddings = any(c.get("embedding") is None for c in target_chunks)
    if has_missing_embeddings:
        target_chunks = await generate_embeddings_for_chunks(env, target_chunks)

    vectors = []
    for i, chunk in enumerate(target_chunks):
        actual_index = start_index + i
        
        # Sanitização do Embedding
        emb = sanitize_embedding(chunk.get("embedding"))
        if emb is None:
            print(f"WARN: Chunk {actual_index} descartado por embedding inválido/ausente")
            continue

        # 2. Construção do Objeto Vetor - Compatível com formato antigo e novo
        text = chunk.get("texto") or chunk.get("text", "")
        chunk_id_val = chunk.get("chunk_id") or f"chunk_{actual_index}"
        
        vector_obj = {
            "id": f"{document_id}-{chunk_id_val}",
            "values": emb,
            "metadata": {
                "document_id": str(document_id),
                "title": str(doc_metadata.get("title", "Unknown")),
                "type": str(doc_metadata.get("type", "Document")),
                "sector": str(doc_metadata.get("sector", "General")),
                "text": str(text),
                "chunk_index": actual_index,
                # Atributos do novo Chunker
                "tipo": str(chunk.get("tipo", "")),
                "numero": str(chunk.get("numero", "")),
                "nivel": str(chunk.get("nivel", "")),
                "pagina": str(chunk.get("pagina", "0")),
                "contexto": str(chunk.get("contexto_hierarquico", "")),
                # Metadados legados se existirem
                **{k: v for k, v in chunk.get("metadata", {}).items() if v is not None}
            }
        }
        vectors.append(vector_obj)

    if not vectors:
        return 0

    # 4. Inserção no Vectorize
    await env.VECTORIZE.insert(to_js(vectors, dict_converter=Object.fromEntries))
    
    print(f"DEBUG: {len(vectors)} vetores inseridos com sucesso!")
    return len(vectors)
