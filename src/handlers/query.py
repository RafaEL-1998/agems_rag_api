from js import Response, Object, Array
from pyodide.ffi import to_js
import json

async def handle_query(request, env):
    try:
        body_proxy = await request.json()
        body = body_proxy.to_py()
        user_query = str(body.get("query", ""))
        
        if not user_query:
            return Response.new(json.dumps({"error": "Query is required"}), to_js({"status": 400}))

        # 1. Gerar embedding
        # bge-m3 espera {"text": ["..."]}
        ai_input = to_js({"text": [user_query]}, dict_converter=Object.fromEntries)
        ai_res_proxy = await env.AI.run('@cf/baai/bge-m3', ai_input)
        ai_res = ai_res_proxy.to_py()
        
        # Se o Workers AI retornar um erro formatado como sucesso
        if "error" in ai_res:
             return Response.new(
                json.dumps({"error": "Erro na API de AI", "details": ai_res["error"]}), 
                to_js({"status": 500, "headers": {"Content-Type": "application/json"}})
            )
        
        # O formato pode variar entre {"result": {"data": [...]}} e {"data": [...] }
        if "result" in ai_res:
            query_vector = ai_res["result"].get("data", [[]])[0]
        else:
            query_vector = ai_res.get("data", [[]])[0]
        
        if not query_vector:
            return Response.new(
                json.dumps({"error": "Vetor de embedding vazio", "raw": ai_res}), 
                to_js({"status": 500, "headers": {"Content-Type": "application/json"}})
            )

        # 2. Busca no Vectorize
        options = to_js({
            "topK": 5,
            "returnMetadata": True
        }, dict_converter=Object.fromEntries)
        
        vector_search_proxy = await env.VECTORIZE.query(to_js(query_vector), options)
        vector_search = vector_search_proxy.to_py()
        print(f"DEBUG VECTOR SEARCH: {len(vector_search.get('matches', []))} matches")

        # 3. Processar Contexto
        matches = vector_search.get('matches', [])
        context_text = ""
        sources = []
        
        for m in matches:
            meta = m.get('metadata', {})
            txt = meta.get('text') or meta.get('content') or ""
            src = meta.get('title') or "Documento"
            if txt:
                context_text += f"\n\nFONTE: {src}\n{txt}"
                if src not in sources: sources.append(src)

        if not context_text:
            context_text = "Nenhum contexto relevante encontrado nos documentos oficiais."

        # 4. Resposta com Llama 3.1
        system_prompt = (
            "Você é um assistente técnico especializado da AGEMS. "
            "Sua resposta deve ser estritamente baseada no CONTEXTO fornecido. "
            "Se o CONTEXTO disser que não encontrou informação, diga isso ao usuário. "
            "Responda sempre em Português do Brasil."
        )
        user_msg = f"CONTEXTO REUPERADO:\n{context_text}\n\nPERGUNTA DO USUÁRIO: {user_query}"
        
        llm_input = to_js({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        }, dict_converter=Object.fromEntries)

        llm_res_proxy = await env.AI.run('@cf/meta/llama-3.1-8b-instruct-fast', llm_input)
        llm_res = llm_res_proxy.to_py()
        
        # O Llama no Workers AI retorna {"response": "..."} ou {"result": {"response": "..."}}
        answer = llm_res.get("response") or llm_res.get("result", {}).get("response") or "Não foi possível gerar uma resposta."

        return Response.new(
            json.dumps({
                "answer": answer,
                "sources": sources,
                "debug_context_len": len(context_text),
                "match_count": len(matches)
            }),
            to_js({"headers": {"Content-Type": "application/json"}})
        )

    except Exception as e:
        import traceback
        error_stack = traceback.format_exc()
        print(f"ERRO CRITICO: {error_stack}")
        return Response.new(
            json.dumps({"error": str(e), "stack": error_stack}), 
            to_js({"status": 500, "headers": {"Content-Type": "application/json"}})
        )
