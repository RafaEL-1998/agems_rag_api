from js import Response
import json
from utils.pdf_extractor import extract_text_from_pdf
from utils.chunking import chunk_text
from utils.vectorize import process_and_vectorize_chunks

async def handle_process(request, env):
    """ Processa um documento: extrai texto, divide em chunks e vetoriza """

    # Extrai document_id da URL
    url = request.url
    document_id = url.split("/documents/")[1].split("/process")[0]

    # Buscar documento no D1
    doc_result = await env.DB.prepare("""
    SELECT * FROM documents 
    WHERE id = ?
    """).bind(document_id).first()

    if not doc_result:
        return Response.json(
            {"error": "Document not found"}, 
            status=404
            )
    
    # Atualizar status para "processing"
    await env.DB.prepare("""
    UPDATE documents 
    SET status = 'processing' 
    WHERE id = ?
    """).bind(document_id).run()

    try:
        
        # Extrair texto do PDF
        text = await extract_text_from_pdf(env, doc_result["r2_key"])

        # Dividir em chunks
        chunks = chunk_text(text)

        # Gerar embeddings e salvar no Vectorize
        chunks_created = await process_and_vectorize_chunks(env, document_id, doc_result, chunks)

        # Atualizar status do documento no D1
        await env.DB.prepare("""
        UPDATE documents 
        SET status = 'processed', chunks_created = ? 
        WHERE id = ?
        """).bind(chunks_created, document_id).run()

        return Response.json({
            "success": True,
            "document_id": document_id,
            "chunks_created": chunks_created,
            "message": "Documento processado e vetorizado com sucesso"
        })
    

    # Marcar como erro
    except Exception as e:
            await env.DB.prepare("""
            UPDATE documents 
            SET status = 'error' 
            WHERE id = ?
            """).bind(document_id).run()

            return Response.json(
            {"error": f"Processing failed: {str(e)}"},
            status=500
        )
        
    
