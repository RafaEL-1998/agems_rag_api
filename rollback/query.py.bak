from js import Response, Object, Array
from pyodide.ffi import to_js
import json

async def handle_query(request, env):
    try:
        body_proxy = await request.json()
        body = body_proxy.to_py()
        user_query = str(body.get("query", ""))
        session_id = body.get("session_id")
        
        if not user_query:
            return Response.new(json.dumps({"error": "Query is required"}), to_js({"status": 400}))

        # 0. Recuperar Histórico do D1 (se houver session_id)
        history = []
        if session_id:
            # Buscar as últimas 10 mensagens para manter contexto curto e eficiente
            history_proxy = await env.agems_rag_db.prepare(
                "SELECT message_type, content FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10"
            ).bind(session_id).all()
            
            history_data = history_proxy.to_py().get("results", [])
            # Inverter para ordem cronológica (D1 retornou as mais novas primeiro)
            for msg in reversed(history_data):
                role = "assistant" if msg["message_type"] == "ai" else "user"
                history.append({"role": role, "content": msg["content"]})


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
            "Sua resposta deve ser estritamente baseada no CONTEXTO REUPERADO fornecido. "
            "Se o CONTEXTO não contiver a resposta, informe o usuário. "
            "Considere o histórico da conversa se for relevante para a pergunta atual."
            "Responda sempre em Português do Brasil."
        )
        
        # Montar lista de mensagens final
        messages = [{"role": "system", "content": system_prompt}]
        
        # Adicionar histórico (sem o prompt de contexto para não poluir o histórico antigo)
        messages.extend(history)
        
        # Adicionar a pergunta atual com o contexto RAG novo
        current_augmented_msg = f"CONTEXTO REUPERADO:\n{context_text}\n\nPERGUNTA ATUAL: {user_query}"
        messages.append({"role": "user", "content": current_augmented_msg})
        
        llm_input = to_js({
            "messages": messages
        }, dict_converter=Object.fromEntries)

        llm_res_proxy = await env.AI.run('@cf/meta/llama-3.1-8b-instruct-fast', llm_input)
        llm_res = llm_res_proxy.to_py()
        
        answer = llm_res.get("response") or llm_res.get("result", {}).get("response") or "Não foi possível gerar uma resposta."

        # 5. Persistir no D1 (se houver session_id)
        if session_id:
            try:
                # Salvar mensagem do usuário (salvamos a original, sem o contexto injetado)
                await env.agems_rag_db.prepare(
                    "INSERT INTO conversations (session_id, message_type, content) VALUES (?, 'user', ?)"
                ).bind(session_id, user_query).run()
                
                # Salvar resposta da IA
                await env.agems_rag_db.prepare(
                    "INSERT INTO conversations (session_id, message_type, content, context_chunks, model_used) VALUES (?, 'ai', ?, ?, ?)"
                ).bind(session_id, answer, json.dumps(sources), "llama-3.1-8b").run()
                
                # Atualizar ou Criar sessão
                await env.agems_rag_db.prepare(
                    "INSERT INTO sessions (id, last_activity, message_count) VALUES (?, CURRENT_TIMESTAMP, 1) "
                    "ON CONFLICT(id) DO UPDATE SET last_activity = CURRENT_TIMESTAMP, message_count = message_count + 1"
                ).bind(session_id).run()
            except Exception as d1_err:
                print(f"ERRO AO SALVAR NO D1: {str(d1_err)}")


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
