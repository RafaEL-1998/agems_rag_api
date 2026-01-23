from js import Response
from pyodide.ffi import to_js
import json

async def handle_query(request, env):
    """
    Handler de Query RAG: 
    1. Gera embedding da pergunta
    2. Busca chunks relevantes no Vectorize
    3. Gera resposta contextualizada usando Llama 3.1
    """
    
    try:
        body = await request.json()
        user_query = body.get("query")
        
        if not user_query:
            return Response.new(
                json.dumps({"error": "Query is required"}),
                to_js({
                    "headers": {"Content-Type": "application/json"},
                    "status": 400
                })
            )

        # 1. Gerar embedding da pergunta do usuário
        embedding_response_proxy = await env.AI.run(
            '@cf/qwen/qwen3-embedding-0.6b',
            {"text": user_query}
        )
        embedding_response = embedding_response_proxy.to_py()
        query_vector = embedding_response['data'][0]

        # 2. Buscar os Top 5 chunks mais relevantes no Vectorize
        vector_search = await env.VECTORIZE.query(
            vector=query_vector,
            top_k=5,
            return_metadata=True
        )

        # 3. Extrair e formatar o contexto dos metadados
        context_chunks = []
        sources = []
        
        for match in vector_search.matches:
            metadata = match.metadata.to_py()
            text_content = metadata.get("text", "")
            doc_title = metadata.get("title", "Documento desconhecido")
            context_chunks.append(f"--- DOCUMENTO: {doc_title} ---\n{text_content}")

            
            if doc_title not in sources:
                sources.append(doc_title)

        context_text = "\n\n".join(context_chunks)

        # 4. Construir o Prompt para o Llama 3.1
        system_prompt = """Você é a IA Regulatória da AGEMS (Agência de Regulação de Serviços Públicos de Mato Grosso do Sul).
Sua missão é responder perguntas baseando-se EXCLUSIVAMENTE nos documentos fornecidos como contexto.
Se a informação não estiver no contexto, diga honestamente que não possui essa informação específica nos documentos regulatórios atuais.
Mantenha um tom profissional, técnico e prestativo."""

        full_prompt = f"""CONTEXTO REGULATÓRIO:
{context_text}

PERGUNTA DO USUÁRIO:
{user_query}

RESPOSTA:"""

        # 5. Gerar a resposta final
        llm_response = await env.AI.run(
            '@cf/meta/llama-3.1-8b-instruct-fast',
            {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ]
            }
        )

        return Response.new(
            json.dumps({
                "answer": llm_response.get("response", "Erro ao gerar resposta"),
                "sources": sources,
                "context_used": len(context_chunks)
            }),
            to_js({"headers": {"Content-Type": "application/json"}})
        )

    except Exception as e:
        return Response.new(
            json.dumps({"error": f"Query failed: {str(e)}"}),
            to_js({
                "headers": {"Content-Type": "application/json"},
                "status": 500
            })
        )
