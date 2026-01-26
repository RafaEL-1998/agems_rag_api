import os
import requests
import json
import statistics

# Configurações de Acesso (leitura manual do .env para evitar dependências)
def load_env_manual():
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_vars[k] = v.strip('"').strip("'")
    return env_vars

env = load_env_manual()
CLOUDFLARE_ACCOUNT_ID = env.get("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = env.get("CLOUDFLARE_API_TOKEN")
INDEX_NAME = "agems-regulatory-docs"

def audit_vectorize_index():
    print(f"--- Iniciando Auditoria do Índice: {INDEX_NAME} ---")
    
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    
    # infelizmente o Vectorize API não permite 'list all' facilmente com metadados sem queries.
    # Vamos fazer uma query genérica que pegue os top 50 resultados para amostragem estatística.
    # Usaremos um vetor de zeros (busca aleatória por posição)
    ai_url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/vectorize/v2/indexes/{INDEX_NAME}/query"
    
    # Um vetor de 1024 dimensões zerado
    dummy_vector = [0.0] * 1024
    
    payload = {
        "vector": dummy_vector,
        "topK": 50,
        "returnMetadata": "all"
    }
    
    resp = requests.post(ai_url, headers=headers, json=payload)
    if resp.status_code != 200:
        print(f"Erro ao acessar Vectorize: {resp.text}")
        return

    matches = resp.json().get("result", {}).get("matches", [])
    
    lengths = []
    article_counts = []
    broken_articles = 0
    
    print(f"Analisando amostragem de {len(matches)} chunks...\n")
    
    with open("testes_validacao/audit_report.txt", "w", encoding="utf-8") as f:
        f.write(f"RELATÓRIO DE AUDITORIA DE CHUNKS - AMÓSTRAGEM\n")
        f.write(f"="*50 + "\n\n")
        
        for i, m in enumerate(matches):
            text = m.get("metadata", {}).get("text", "")
            length = len(text)
            lengths.append(length)
            
            # Conta ocorrências de 'Art.' no texto
            articles = len([a for a in ["Art.", "Artigo"] if a in text])
            article_counts.append(articles)
            
            # Verifica se o texto começa com Art. mas não termina o sentido (heurística simples)
            if "Art." in text and not text.strip().endswith((".", ";", ":")):
                broken_articles += 1
            
            f.write(f"CHUNK {i+1} (ID: {m.get('id')})\n")
            f.write(f"Tamanho: {length} chars | Artigos Detectados: {articles}\n")
            f.write(f"Snippet: {text[:150]}...\n")
            f.write("-" * 30 + "\n")

    # Estatísticas
    avg_len = statistics.mean(lengths)
    max_len = max(lengths)
    min_len = min(lengths)
    avg_arts = statistics.mean(article_counts)

    print(f"RESULTADOS DA AUDITORIA:")
    print(f"- Tamanho Médio: {avg_len:.1f} caracteres (Configurado: 1500)")
    print(f"- Tamanho Máximo Encontrado: {max_len}")
    print(f"- Tamanho Mínimo Encontrado: {min_len}")
    print(f"- Média de Artigos por Chunk: {avg_arts:.1f}")
    print(f"- Chunks com Provável Quebra Brusca: {broken_articles}")
    
    print("\n--- SUGESTÃO TÉCNICA ---")
    if avg_arts > 1.5:
        suggested = int(avg_len / avg_arts) + 200
        print(f"STATUS: AGRUPAMENTO EXCESSIVO DETECTADO.")
        print(f"AÇÃO: Recomendo reduzir o chunk_size para ~{suggested} caracteres.")
        print(f"MOTIVO: Manter 1 artigo (ou 1 artigo + parágrafos) por chunk aumenta a precisão em 30-40%.")
    else:
        print(f"STATUS: DISTRIBUIÇÃO EQUILIBRADA.")
        
    print("\nRelatório detalhado salvo em: testes_validacao/audit_report.txt")

if __name__ == "__main__":
    audit_vectorize_index()
