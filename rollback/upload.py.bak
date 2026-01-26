from js import Response, FormData, Uint8Array, JSON
from pyodide.ffi import to_js
import json
import uuid

async def handle_upload(request, env):
    """
    Handler de Upload - Versao ultra-estavel com JSON.parse para options.
    """
    try:
        print(f"DEBUG: Recebendo request de upload")
        form_data = await request.formData()
        
        file = form_data.get("file")
        title = form_data.get("title") or "Sem Titulo"
        doc_type = form_data.get("type") or "Documento"
        sector = form_data.get("sector") or "Geral"

        if not file:
            return Response.new(
                json.dumps({"error": "No file uploaded"}),
                JSON.parse(json.dumps({"status": 400, "headers": {"Content-Type": "application/json"}}))
            )

        doc_id = str(uuid.uuid4())
        r2_key = f"documents/{doc_id}.pdf"

        # 1. R2 - Upload
        print(f"DEBUG: Salvando no R2")
        array_buffer = await file.arrayBuffer()
        await env.agems_docs.put(r2_key, Uint8Array.new(array_buffer))

        # 2. D1
        print(f"DEBUG: Registrando no D1 via .run()")
        
        try:
            def sql_quote(v):
                return f"'{str(v).replace("'", "''")}'"

            sql = f"""
                INSERT INTO documents (id, title, type, sector, r2_key, status)
                VALUES (
                    {sql_quote(doc_id)}, 
                    {sql_quote(title)}, 
                    {sql_quote(doc_type)}, 
                    {sql_quote(sector)}, 
                    {sql_quote(r2_key)}, 
                    'pending'
                )
            """
            await env.agems_rag_db.prepare(sql).run()
            
            print("Sucesso absoluto no D1 via .run()!")
            
            return Response.new(
                json.dumps({
                    "success": True, 
                    "message": "Upload e registro concluídos",
                    "document_id": str(doc_id)
                }),
                JSON.parse(json.dumps({"status": 201, "headers": {"Content-Type": "application/json"}}))
            )

        except Exception as d1_err:
            print(f"Erro no D1: {str(d1_err)}")
            return Response.new(
                json.dumps({"error": str(d1_err)}),
                JSON.parse(json.dumps({"status": 500, "headers": {"Content-Type": "application/json"}}))
            )

    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        print(f"FALHA NO UPLOAD: {err_trace}")
        return Response.new(
            json.dumps({"error": str(e), "trace": err_trace}),
            JSON.parse(json.dumps({"status": 500, "headers": {"Content-Type": "application/json"}}))
        )
