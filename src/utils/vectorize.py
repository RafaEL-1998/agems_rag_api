from pyodide.ffi import to_js

async def process_and_vectorize_chunks(env, document_id, doc_metadata, chunks):
    """
    Recebe chunks com embeddings JÁ GERADOS e apenas insere no Vectorize.
    
    Args:
        env: Cloudflare Worker environment
        document_id: ID do documento
        doc_metadata: Metadados do documento (title, type, sector)
        chunks: Lista de dicts com estrutura:
            {
                "id": "chunk-0",
                "embedding": [0.1, 0.2, ...],  # Vetor de 768 dims
                "text": "conteúdo do chunk",
                "metadata": {...}  # Opcional
            }
    
    Returns:
        Número de chunks processados
    """
    vectors = []

    for chunk in chunks:
        vector_obj = {
            "id": f"{document_id}-{chunk['id']}",
            "values": chunk["embedding"],  # JÁ VEM PRONTO DO CLIENTE
            "metadata": {
                "document_id": document_id,
                "title": doc_metadata.get("title", "Unknown"),
                "type": doc_metadata.get("type", "Document"),
                "sector": doc_metadata.get("sector", "General"),
                "text": chunk.get("text", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                **chunk.get("metadata", {})  # Metadados adicionais opcionais
            }
        }
        vectors.append(vector_obj)

    # Inserir todos os vetores de uma vez (mais eficiente)
    if vectors:
        print(f"DEBUG: Inserindo {len(vectors)} vetores no Vectorize...")
        await env.VECTORIZE.insert(to_js(vectors))
        print(f"DEBUG: {len(vectors)} vetores inseridos com sucesso!")

    return len(vectors)
