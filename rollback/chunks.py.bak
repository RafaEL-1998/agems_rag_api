from js import Response, JSON
from pyodide.ffi import to_js
import json
from utils.vectorize import process_and_vectorize_chunks

async def handle_add_chunks(request, env):
    """
    Recebe chunks de texto prontos, gera embeddings e salva no Vectorize.
    """
    try:
        url_obj = request.url
        document_id = url_obj.split("/documents/")[1].split("/chunks")[0]
        
        body_proxy = await request.json()
        body = body_proxy.to_py()
        
        chunks = body.get("chunks", [])
        doc_metadata = body.get("metadata", {})

        if not chunks:
            return Response.new(
                json.dumps({"error": "No chunks provided"}), 
                JSON.parse(json.dumps({"status": 400, "headers": {"Content-Type": "application/json"}}))
            )

        print(f"DEBUG: Processando {len(chunks)} chunks para o doc {document_id}")
        
        # O process_and_vectorize_chunks já foi atualizado para lidar com listas
        processed = await process_and_vectorize_chunks(env, document_id, doc_metadata, chunks)

        # Atualizar contagem no D1
        await env.agems_rag_db.prepare("""
            UPDATE documents 
            SET chunk_count = chunk_count + ?, status = 'processed' 
            WHERE id = ?
        """).bind(processed, document_id).run()

        return Response.new(
            json.dumps({"success": True, "processed_this_batch": processed}),
            JSON.parse(json.dumps({"status": 200, "headers": {"Content-Type": "application/json"}}))
        )
    except Exception as e:
        print(f"ERRO NO ADD_CHUNKS: {str(e)}")
        return Response.new(
            json.dumps({"error": str(e)}), 
            JSON.parse(json.dumps({"status": 500, "headers": {"Content-Type": "application/json"}}))
        )
