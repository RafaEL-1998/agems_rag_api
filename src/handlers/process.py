from js import Response, Uint8Array, JSON
from pyodide.ffi import to_js
import json
from utils.pdf_extractor import extract_text_from_pdf
from utils.chunking import chunk_text
from utils.vectorize import process_and_vectorize_chunks

async def handle_process(request, env):
    """ Processa um documento em etapas para evitar limites de CPU do Cloudflare """

    # Extrai document_id da URL e parâmetros de range se houver
    url_obj = request.url
    document_id = url_obj.split("/documents/")[1].split("/process")[0]
    
    from urllib.parse import urlparse, parse_qs
    parsed_url = urlparse(url_obj)
    query_params = parse_qs(parsed_url.query)
    
    step = query_params.get("step", ["all"])[0] # extract, vectorize
    
    # Parâmetros de Extração
    start_page = int(query_params.get("start_page", [0])[0])
    limit_pages = int(query_params.get("limit_pages", [50])[0])
    
    # Parâmetros de Vetorização
    start_chunk = int(query_params.get("start_chunk", [0])[0])
    limit_chunks = int(query_params.get("limit_chunks", [10])[0])

    # Buscar documento no D1
    doc_result_proxy = await env.agems_rag_db.prepare("SELECT * FROM documents WHERE id = ?").bind(document_id).first()
    if not doc_result_proxy:
        return Response.new(
            json.dumps({"error": "Document not found"}), 
            JSON.parse(json.dumps({"status": 404, "headers": {"Content-Type": "application/json"}}))
        )
    
    doc_result = doc_result_proxy.to_py()
    txt_dir = f"documents/{document_id}/pages"

    try:
        if step == "extract":
            print(f"DEBUG: Passo EXTRACT - Paginas {start_page} a {start_page + limit_pages}")
            text_batch, total_pages = await extract_text_from_pdf(env, doc_result["r2_key"], start_page, limit_pages)
            
            # Salvar este lote separadamente para evitar o gargalo de append
            batch_key = f"{txt_dir}/{start_page}.txt"
            await env.agems_docs.put(batch_key, Uint8Array.new(text_batch.encode("utf-8")))
            
            current_page = start_page + limit_pages
            is_finished = current_page >= total_pages
            
            return Response.new(
                json.dumps({
                    "success": True,
                    "step": "extract",
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "is_finished": is_finished
                }),
                JSON.parse(json.dumps({"status": 200, "headers": {"Content-Type": "application/json"}}))
            )

        elif step == "vectorize":
            print(f"DEBUG: Passo VECTORIZE - Chunks {start_chunk} a {start_chunk + limit_chunks}")
            
            # Se for o primeiro chunk, precisamos reconstruir o texto completo
            # Poderíamos cachear o texto completo no R2 em um arquivo único após o extract terminar
            full_txt_key = f"documents/{document_id}/full.txt"
            
            if start_chunk == 0:
                print("DEBUG: Reconstruindo texto completo a partir dos fragmentos...")
                # Listar todos os fragmentos
                listed = await env.agems_docs.list(to_js({"prefix": txt_dir}))
                # Ordenar por nome (que é o start_page)
                keys = sorted([o.key for o in listed.objects], key=lambda x: int(x.split("/")[-1].replace(".txt", "")))
                
                parts = []
                for k in keys:
                    obj = await env.agems_docs.get(k)
                    parts.append(bytes(Uint8Array.new(await obj.arrayBuffer())).decode("utf-8"))
                
                full_text = "\n\n".join(parts)
                # Cachear o texto completo para as próximas chamadas de chunk
                await env.agems_docs.put(full_txt_key, Uint8Array.new(full_text.encode("utf-8")))
            else:
                # Ler o texto completo já cacheado
                obj = await env.agems_docs.get(full_txt_key)
                full_text = bytes(Uint8Array.new(await obj.arrayBuffer())).decode("utf-8")
            
            chunks = chunk_text(full_text)
            chunks_processed = await process_and_vectorize_chunks(env, document_id, doc_result, chunks, start_chunk, limit_chunks)
            
            total_chunks = len(chunks)
            current_processed = start_chunk + chunks_processed
            is_finished = current_processed >= total_chunks
            
            # Atualizar D1
            new_status = 'processed' if is_finished else 'processing'
            await env.agems_rag_db.prepare("UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?").bind(new_status, current_processed, document_id).run()

            return Response.new(
                json.dumps({
                    "success": True,
                    "step": "vectorize",
                    "total_processed": current_processed,
                    "total_chunks": total_chunks,
                    "is_finished": is_finished
                }),
                JSON.parse(json.dumps({"status": 200, "headers": {"Content-Type": "application/json"}}))
            )


        else:
            return Response.new(
                json.dumps({"error": "Passo inválido. Use 'extract' ou 'vectorize'."}), 
                JSON.parse(json.dumps({"status": 400, "headers": {"Content-Type": "application/json"}}))
            )

    except Exception as e:
        print(f"ERRO NO PROCESSAMENTO ({step}): {str(e)}")
        import traceback
        print(traceback.format_exc())
        await env.agems_rag_db.prepare("UPDATE documents SET status = 'error' WHERE id = ?").bind(document_id).run()
        return Response.new(
            json.dumps({"error": str(e)}), 
            JSON.parse(json.dumps({"status": 500, "headers": {"Content-Type": "application/json"}}))
        )


