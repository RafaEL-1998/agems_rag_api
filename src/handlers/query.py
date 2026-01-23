from js import Response
from pyodide.ffi import to_js
import json
from js import Object

async def handle_query(request, env):
    try:
        body_proxy = await request.json()
        body = body_proxy.to_py()
        user_query = str(body.get("query", "Olá"))
        
        # Teste direto com Llama para validar Bindings
        try:
            test_llm = await env.AI.run('@cf/meta/llama-3.1-8b-instruct-fast', to_js({
                "prompt": "Responda apenas 'OK'",
                "max_tokens": 5
            }))
            print("DEBUG: Llama Test OK")
        except Exception as e:
            return Response.new(json.dumps({"error": f"Erro Binding AI: {str(e)}"}), to_js({"status": 500}))

        # Tentativa 1: BGE-M3 com string direta
        # Tentativa 2: BGE-M3 com dict e Object.fromEntries
        try:
            print(f"DEBUG: Tentando BGE-M3 com string direta")
            res_proxy = await env.AI.run('@cf/baai/bge-m3', user_query)
            res = res_proxy.to_py()
            query_vector = res['data'][0]
        except Exception as e1:
            print(f"DEBUG: Falha string direta: {str(e1)}")
            try:
                print(f"DEBUG: Tentando BGE-M3 com dict e Object.fromEntries")
                # Forçando a conversão para Object JS puro
                res_proxy = await env.AI.run('@cf/baai/bge-m3', to_js({"text": user_query}, dict_converter=Object.fromEntries))
                res = res_proxy.to_py()
                query_vector = res['data'][0]
            except Exception as e2:
                return Response.new(json.dumps({
                    "error": "Falha total no embedding",
                    "e1_string": str(e1),
                    "e2_dict": str(e2)
                }), to_js({"status": 500}))

        # Se chegou aqui, temos o vetor. Vamos buscar no Vectorize.
        try:
            vector_search_proxy = await env.VECTORIZE.query(vector=query_vector, top_k=3, return_metadata=True)
            vector_search = vector_search_proxy.to_py()
            matches = vector_search.get('matches', [])
            context = "\n".join([m.get('metadata', {}).get('text', '') for m in matches])
        except Exception as e:
            return Response.new(json.dumps({"error": f"Erro Vectorize: {str(e)}"}), to_js({"status": 500}))

        # Resposta Final
        prompt = f"Contexto: {context}\n\nPergunta: {user_query}\n\nResposta:"
        llm_res = await env.AI.run('@cf/meta/llama-3.1-8b-instruct-fast', to_js({"prompt": prompt}))
        answer = llm_res.to_py().get("response", "...")

        return Response.new(
            json.dumps({"answer": answer, "debug_vector_len": len(query_vector)}),
            to_js({"headers": {"Content-Type": "application/json"}})
        )

    except Exception as e:
        return Response.new(json.dumps({"error": str(e)}), to_js({"status": 500}))
