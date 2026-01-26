import requests
import json

WORKER_BASE_URL = "https://agems-rag-api.dgeagems.workers.dev"

def test_chat_query(query_text):
    print(f"\n--- Testando Query: {query_text} ---")
    url = f"{WORKER_BASE_URL}/chat/query"
    payload = {"query": query_text}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"RAW RESP: {response.text}")
            result = response.json()
            print(f"Status: SUCESSO")
            print(f"Contexto Recuperado (caracteres): {result.get('debug_context_len')}")
            print(f"Fontes: {', '.join(result.get('sources', []))}")
            print("\nResposta da IA:")
            print("-" * 30)
            print(result.get("answer"))
            print("-" * 30)
        else:
            print(f"Erro {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Falha na requisição: {str(e)}")

if __name__ == "__main__":
    # Teste 1: Pergunta sobre o documento que realmente existe (REN 1000)
    test_chat_query("O que a Resolução 1000 da ANEEL estabelece?")
    
    # Teste 2: Outra pergunta específica da REN 1000
    test_chat_query("Quais os direitos do consumidor de energia elétrica?")
    
    # Teste 3: Pergunta fora do contexto (deve dizer que não encontrou agora)
    test_chat_query("Quais são as regras para regulação de gás?")
