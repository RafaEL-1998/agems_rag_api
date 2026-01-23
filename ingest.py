import sys
import os

# Adiciona o diretório 'src' ao path para importar as utilidades oficiais do projeto
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import requests
import pypdf
import json
from utils.chunking import chunk_text

# Configurações
WORKER_BASE_URL = "https://agems-rag-api.dgeagems.workers.dev"
FOLDER_PATH = "./documentos_para_processar"

def extract_text_locally(filepath):
    """ Extrai o texto do PDF localmente usando pypdf """
    with open(filepath, 'rb') as f:
        reader = pypdf.PdfReader(f)
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                # Limpeza básica de caracteres nulos ou problemáticos
                clean_t = t.replace('\x00', '').strip()
                if clean_t:
                    text_parts.append(clean_t)
    return "\n\n".join(text_parts)


def generate_embeddings_locally(chunks):
    """
    Gera embeddings localmente usando a API da Cloudflare Workers AI.
    Retorna uma lista de chunks com embeddings incluídos.
    """
    import os
    from dotenv import load_dotenv
    import time
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
    
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        print("      ERRO: Credenciais da Cloudflare não encontradas!")
        print("      Crie um arquivo .env com CLOUDFLARE_ACCOUNT_ID e CLOUDFLARE_API_TOKEN")
        print("      Usando vetores aleatórios como fallback...")
        return generate_embeddings_fallback(chunks)
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/baai/bge-m3"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"      -> Gerando {len(chunks)} embeddings via Cloudflare AI API...")
    chunks_with_embeddings = []
    errors = 0
    
    for i, chunk_text in enumerate(chunks):
        try:
            # Sanitizar o texto antes de enviar
            clean_text = chunk_text.replace('\x00', '').strip()
            if len(clean_text) < 10:
                print(f"         WARN: Chunk {i} muito curto, pulando...")
                continue
            
            response = requests.post(
                url, 
                headers=headers, 
                json={"text": clean_text},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result["result"]["data"][0]
                
                chunks_with_embeddings.append({
                    "id": f"chunk-{i}",
                    "embedding": embedding,
                    "text": clean_text,
                    "chunk_index": i
                })
                
                if (i + 1) % 50 == 0:
                    print(f"         -> {i + 1}/{len(chunks)} embeddings gerados...")
            else:
                print(f"         ERRO chunk {i}: HTTP {response.status_code} - {response.text[:100]}")
                errors += 1
                if errors > 10:
                    print("         Muitos erros, abortando...")
                    break
            
            # Rate limiting: 300 req/min = ~5 req/s, então esperamos 0.2s entre chamadas
            time.sleep(0.25)
            
        except Exception as e:
            print(f"         ERRO chunk {i}: {str(e)}")
            errors += 1
            if errors > 10:
                break
    
    print(f"      -> {len(chunks_with_embeddings)} embeddings gerados com sucesso!")
    if errors > 0:
        print(f"      -> {errors} erros encontrados")
    
    return chunks_with_embeddings

def generate_embeddings_fallback(chunks):
    """
    Fallback: Gera vetores aleatórios para teste quando as credenciais não estão disponíveis.
    """
    import random
    
    print("      -> Gerando embeddings com vetores aleatórios (MODO TESTE)...")
    chunks_with_embeddings = []
    
    for i, chunk_text in enumerate(chunks):
        random.seed(hash(chunk_text))
        embedding = [random.random() for _ in range(1024)]
        
        chunks_with_embeddings.append({
            "id": f"chunk-{i}",
            "embedding": embedding,
            "text": chunk_text,
            "chunk_index": i
        })
        
        if (i + 1) % 100 == 0:
            print(f"         -> {i + 1}/{len(chunks)} embeddings gerados...")
    
    return chunks_with_embeddings


def ingest_documents():

    if not os.path.exists(FOLDER_PATH):
        print(f"Erro: Pasta '{FOLDER_PATH}' não encontrada.")
        return

    files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith(".pdf")]
    if not files:
        print("Nenhum PDF encontrado.")
        return

    print(f"Iniciando ingestão de {len(files)} arquivos...\n")

    for filename in files:
        filepath = os.path.join(FOLDER_PATH, filename)
        print(f"--- Processando: {filename} ---")
        
        try:
            # 1. Extração Local
            print("   [1/4] Extraindo texto localmente...")
            full_text = extract_text_locally(filepath)
            
            # 2. Chunking Local usando a lógica oficial do projeto
            print("   [2/4] Realizando chunking local...")
            chunks = chunk_text(full_text)
            print(f"      -> Gerados {len(chunks)} chunks.")

            # 3. Gerar Embeddings Localmente
            print("   [3/5] Gerando embeddings localmente...")
            chunks_with_embeddings = generate_embeddings_locally(chunks)

            # 4. Upload do PDF (R2 + D1 registration)
            print("   [4/5] Enviando PDF para armazenamento...")
            metadata = {
                "title": filename.replace(".pdf", ""),
                "type": "Resolução" if "REN" in filename.upper() else "Documento",
                "sector": "Energia" if "ANEEL" in filename.upper() else "Geral"
            }
            with open(filepath, 'rb') as f:
                resp = requests.post(f"{WORKER_BASE_URL}/documents/upload", files={'file': f}, data=metadata)
            
            if resp.status_code not in [200, 201]:
                print(f"      ERRO no upload: {resp.text}"); continue
            
            doc_id = resp.json().get("document_id")
            print(f"      -> ID Gerado: {doc_id}")

            # 5. Enviar Chunks com Embeddings em Lotes
            print("   [5/5] Enviando vetores para o Vectorize...")
            batch_size = 10  # Agora podemos enviar mais porque não há IA no Worker
            all_batches_success = True
            
            for i in range(0, len(chunks_with_embeddings), batch_size):
                batch = chunks_with_embeddings[i:i + batch_size]
                print(f"      -> Enviando lote {i//batch_size + 1} ({len(batch)} vetores)...")

                chunk_resp = requests.post(
                    f"{WORKER_BASE_URL}/documents/{doc_id}/chunks",
                    json={"chunks": batch, "metadata": metadata}
                )
                
                if chunk_resp.status_code != 200:
                    print(f"      ERRO no lote {i//batch_size + 1}: {chunk_resp.text}")
                    all_batches_success = False
                    break
                
                progress = ((i + len(batch)) / len(chunks_with_embeddings)) * 100
                print(f"      -> Progresso: {progress:.1f}%")

            if all_batches_success:
                print(f"SUCESSO: {filename} concluído!")
            else:
                print(f"FALHA: {filename} não foi processado completamente.")



        except Exception as e:
            print(f"FALHA em {filename}: {str(e)}")
        print("-" * 30)

if __name__ == "__main__":
    ingest_documents()
