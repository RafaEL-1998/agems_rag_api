async def process_and_vectorize_chunks(env, document_id, doc, chunks):
    """ Gera embeddings e armazena no Vectorize """

    for i, chunk in enumerate(chunks):
        
        # Gerar embedding usando Workers AI
        embedding_response = await env.AI.run(
            '@cf/qwen/qwen3-embedding-0.6b',
            {"text": chunk}
        )
        
        # Extrair vetor embedding
        embedding = embedding_response['data'][0]

        # Preparar metadados
        vector_id = f"{document_id}-chunk-{i}"
        text_preview = chunk[:200] if len(chunk) > 200 else chunk

        # Inserir no Vectorize
        await env.VECTORIZE.insert([{
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "document_id": document_id,
                "chunk_index": i,
                "title": doc['title'],
                "type": doc['type'],
                "sector": doc['sector'],
                "text_preview": text_preview
            }
        }])

    return len(chunks)