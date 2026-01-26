import requests
import json
import uuid

WORKER_BASE_URL = "https://agems-rag-api.dgeagems.workers.dev"

def test_chat_memory():
    session_id = f"test-session-{uuid.uuid4().hex[:8]}"
    print(f"--- Iniciando Sessão de Teste: {session_id} ---")
    
    queries = [
        "O que a Resolução 1000 da ANEEL estabelece sobre mo SCEE?",
        "E quais são as modalidades nelas previstas?",
        "Quem é responsável pelos custos de integração?"
    ]
    
    for i, q in enumerate(queries):
        print(f"\n[Pergunta {i+1}]: {q}")
        payload = {
            "query": q,
            "session_id": session_id
        }
        
        try:
            response = requests.post(f"{WORKER_BASE_URL}/chat/query", json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"Resposta IA: {result.get('answer')[:300]}...")
                print(f"Fontes: {', '.join(result.get('sources', []))}")
                print(f"Match Count: {result.get('match_count')}")
            else:
                print(f"Erro {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Falha: {str(e)}")

if __name__ == "__main__":
    test_chat_memory()
