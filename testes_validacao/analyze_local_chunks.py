import sys
import os
import re

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.chunking import chunk_text
import pypdf

def analyze_local_doc(filepath):
    print(f"--- Analisando Chunkeamento Adaptativo de: {filepath} ---")
    
    # 1. Extração de texto (mesma lógica do ingest.py)
    reader = pypdf.PdfReader(filepath)
    text_parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t.replace('\x00', '').strip())
    full_text = "\n\n".join(text_parts)
    
    # 2. Executar o Chunking
    # A função agora vai imprimir o Size e Overlap detectado por causa do meu print de DEBUG
    chunks = chunk_text(full_text)
    
    print(f"\nTotal de Chunks Gerados: {len(chunks)}")
    
    # 3. Auditoria Detalhada
    lengths = [len(c["text"]) for c in chunks]
    
    with open("testes_validacao/local_chunk_report.txt", "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE AUDITORIA LOCAL - CHUNKING ADAPTATIVO\n")
        f.write(f"Documento: {os.path.basename(filepath)}\n")
        f.write("="*60 + "\n\n")
        
        broken_count = 0
        multi_article_count = 0
        
        for i, chunk_data in enumerate(chunks):
            chunk = chunk_data["text"]
            meta = chunk_data["metadata"]
            
            # Procura por padrões de Artigos
            articles = re.findall(r'(?:Art\.|Artigo)\s?\d+', chunk)
            
            is_broken = False
            # Heurística: se tem Art. mas termina sem pontuação final forte
            if "Art." in chunk and not chunk.strip()[-1] in ".!;":
                is_broken = True
                broken_count += 1
                
            if len(articles) > 1:
                multi_article_count += 1
                
            f.write(f"--- CHUNK {i} ({len(chunk)} chars) ---\n")
            f.write(f"Hierarquia: {meta}\n")
            f.write(f"Artigos detectados ({len(articles)}): {', '.join(articles)}\n")
            if is_broken:
                f.write("!!! Alerta: Provável quebra no meio de frase/artigo !!!\n")
            
            # Mostrar os primeiros e últimos 100 caracteres para ver a transição
            f.write(f"INÍCIO: {chunk[:100].replace('\n', ' ')}\n")
            f.write(f"FIM:    {chunk[-100:].replace('\n', ' ')}\n")
            f.write("-" * 40 + "\n\n")

    print(f"\nResumo da Auditoria:")
    print(f"- Média de caracteres: {sum(lengths)/len(lengths):.1f}")
    print(f"- Maior chunk: {max(lengths)}")
    print(f"- Menor chunk: {min(lengths)}")
    print(f"- Chunks com múltiplos artigos: {multi_article_count}")
    print(f"- Chunks com provável quebra brusca: {broken_count}")
    print(f"\nRelatório completo gerado em: testes_validacao/local_chunk_report.txt")

if __name__ == "__main__":
    pdf_path = "documentos_para_processar/REN_1000_ANEEL.pdf"
    if os.path.exists(pdf_path):
        analyze_local_doc(pdf_path)
    else:
        print(f"Erro: Arquivo {pdf_path} não encontrado.")
