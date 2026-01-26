import os
import requests
import json

def load_env_manual():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v.strip('"').strip("'")

load_env_manual()

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
INDEX_NAME = "agems-regulatory-docs"

def debug_query(query_text):
    print(f"\n--- Debugando Vectorize para: '{query_text}' ---")
    
    # 1. Gerar Embedding via API
    print("1. Gerando embedding...")
    ai_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/baai/bge-m3"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    ai_resp = requests.post(ai_url, headers=headers, json={"text": query_text})
    
    if ai_resp.status_code != 200:
        print(f"Erro AI: {ai_resp.text}")
        return
    
    vector = ai_resp.json()["result"]["data"][0]
    print(f"Dimensoes do vetor: {len(vector)}")

    # 2. Consultar Vectorize via API (v2)
    print("2. Consultando Vectorize...")
    vec_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/vectorize/v2/indexes/{INDEX_NAME}/query"
    
    vec_payload = {
        "vector": vector,
        "topK": 5,
        "returnMetadata": "all"
    }
    
    vec_resp = requests.post(vec_url, headers=headers, json=vec_payload)
    
    if vec_resp.status_code != 200:
        print(f"Erro Vectorize: {vec_resp.text}")
        return
    
    results = vec_resp.json().get("result", {})
    matches = results.get("matches", [])
    
    print(f"Total de matches encontrados: {len(matches)}")
    
    for i, m in enumerate(matches):
        print(f"\nMatch {i+1} (Score: {m.get('score'):.4f}):")
        meta = m.get("metadata", {})
        print(f"Doc: {meta.get('title')}")
        text_snippet = meta.get("text", "SEM TEXTO")[:200]
        print(f"Texto: {text_snippet}...")

if __name__ == "__main__":
    debug_query("O que a Resolução 1000 da ANEEL estabelece?")
    debug_query("direitos do consumidor")
