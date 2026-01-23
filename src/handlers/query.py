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
        # Usamos Object.fromEntries para garantir que o input seja um Objeto JS puro
        ai_input = to_js({"text": [user_query]}, dict_converter=Object.fromEntries)
        ai_res_proxy = await env.AI.run('@cf/baai/bge-m3', ai_input)
        
        # 2. Busca no Vectorize
        # Importante: Tentamos acessar a data[0] diretamente do proxy JS para evitar conversão falha
        try:
            # Pegamos o vetor do proxy e garantimos que o Vectorize o veja como um Array JS
            query_vector_js = ai_res_proxy.data[0]
            
            # Chamada da query passando o vetor JS diretamente
            vector_search_proxy = await env.VECTORIZE.query(query_vector_js, top_k=5, return_metadata=True)
            vector_search = vector_search_proxy.to_py()
        except Exception as vec_err:
            # Fallback caso o acesso direto ao proxy falhe em algum edge case
            res_py = ai_res_proxy.to_py()
            vec_py = res_py['data'][0]
            vector_search_proxy = await env.VECTORIZE.query(to_js(vec_py), top_k=5, return_metadata=True)
            vector_search = vector_search_proxy.to_py()

        # 3. Processar Contexto
        matches = vector_search.get('matches', [])
        context_text = ""
        sources = []
        
        for m in matches:
            meta = m.get('metadata', {})
            txt = meta.get('text', '')
            src = meta.get('title', 'Documento')
            if txt:
                context_text += f"\n\nFONTE: {src}\n{txt}"
                if src not in sources: sources.append(src)

        if not context_text:
            context_text = "Nenhum contexto relevante encontrado."

        # 4. Resposta com Llama 3.1
        # Usando a estrutura de messages sugerida
        system_prompt = "Você é o assistente técnico da AGEMS. Responda em português baseado no contexto."
        user_msg = f"CONTEXTO:\n{context_text}\n\nPERGUNTA: {user_query}"
        
        llm_input = to_js({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        }, dict_converter=Object.fromEntries)

        llm_res_proxy = await env.AI.run('@cf/meta/llama-3.1-8b-instruct-fast', llm_input)
        answer = llm_res_proxy.to_py().get("response", "Erro na resposta")

        return Response.new(
            json.dumps({
                "answer": answer,
                "sources": sources,
                "debug_context_len": len(context_text)
            }),
            to_js({"headers": {"Content-Type": "application/json"}})
        )

    except Exception as e:
        return Response.new(json.dumps({"error": f"Erro Final: {str(e)}"}), to_js({"status": 500}))
