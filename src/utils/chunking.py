import re

def identify_document_type(text):
    """
    Identifica se o documento é uma norma jurídica ou um texto comum.
    Utiliza uma contagem de ocorrências para evitar que relatórios com simples 
    citações sejam classificados como 'legal'.
    """
    # Padrões que indicam estrutura de lei/resolução
    structural_patterns = [
        r"\bArt\.\s?\d+",           # Art. 1
        r"\bArtigo\s?\d+",         # Artigo 1
        r"\b§\s?\d+",               # Símbolo de parágrafo único/seguinte
    ]
    
    # Padrões de cabeçalho (peso maior)
    header_patterns = [
        r"RESOLUÇÃO\s?N[º°]", 
        r"LEI\s?N[º°]",
        r"DECRETA",
        r"CONSIDERANDO"
    ]
    
    total_matches = 0
    # Conta quantos "Artigos" ou "Parágrafos" existem (indica alta densidade)
    for pattern in structural_patterns:
        total_matches += len(re.findall(pattern, text, re.IGNORECASE))
        
    has_header = False
    for pattern in header_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            has_header = True
            break
            
    # CRITÉRIO:
    # Se tiver um cabeçalho oficial E pelo menos 3 artigos, OU
    # Se não tiver cabeçalho mas tiver mais de 10 referências a artigos (densidade alta)
    if (has_header and total_matches >= 3) or (total_matches >= 10):
        return "legal"
    
    return "normal"

def recursive_internal_split(text, chunk_size, chunk_overlap, separators=None):
    """
    Divide um bloco de texto (como um Artigo muito longo) de forma recursiva 
    para garantir que não ultrapasse o limite de caracteres.
    """
    if separators is None:
        separators = ["\n", ". ", " ", ""]
        
    if len(text) <= chunk_size:
        return [text.strip()]
    
    separator = separators[0]
    remaining = separators[1:]
    
    if separator == "":
        parts = list(text)
    else:
        parts = text.split(separator)
        
    final_chunks = []
    current_buffer = ""
    
    for part in parts:
        s = separator if part != parts[-1] else ""
        item = part + s
        
        if len(item) > chunk_size:
            if current_buffer:
                final_chunks.append(current_buffer.strip())
                current_buffer = ""
            final_chunks.extend(recursive_internal_split(item, chunk_size, chunk_overlap, remaining))
        elif len(current_buffer) + len(item) <= chunk_size:
            current_buffer += item
        else:
            if current_buffer:
                final_chunks.append(current_buffer.strip())
            overlap_start = max(0, len(current_buffer) - chunk_overlap)
            current_buffer = current_buffer[overlap_start:] + item
            
    if current_buffer:
        final_chunks.append(current_buffer.strip())
        
    return [c for c in final_chunks if c]

def calculate_adaptive_chunk_size(text, default_size=1500):
    """
    Analisa a estrutura do documento para sugerir um tamanho de chunk ideal.
    Para documentos jurídicos, tenta encontrar o tamanho médio dos artigos.
    """
    doc_type = identify_document_type(text)
    if doc_type != "legal":
        return default_size

    # Encontrar posições de "Art."
    matches = list(re.finditer(r'\n\s*(?:Art\.|Artigo)\s?\d+', text))
    if len(matches) < 2:
        return default_size

    # Calcular distâncias entre artigos
    distances = []
    for i in range(len(matches) - 1):
        dist = matches[i+1].start() - matches[i].start()
        if dist > 50: # Evita erros de captura muito próximos
            distances.append(dist)

    if not distances:
        return default_size

    # Usar a média das distâncias para definir o chunk_size
    import statistics
    avg_dist = statistics.mean(distances)
    
    # O chunk ideal deve ser um pouco maior que a média para garantir que 
    # a maioria dos artigos caiba inteira, mas não tão grande que agrupe demais.
    # Fator de 1.2x a 1.5x é o ideal para documentos legais.
    adaptive_size = int(avg_dist * 1.3)
    
    # Limites de segurança para não criar chunks minúsculos ou gigantes
    return max(600, min(adaptive_size, 3000))

def chunk_text(text, chunk_size=None, chunk_overlap=None):
    """
    Função principal adaptativa: Detecta o tipo de documento, 
    calcula o tamanho ideal e aplica a melhor estratégia de quebra.
    """
    # 1. Ajuste Adaptativo de Parâmetros
    if chunk_size is None:
        chunk_size = calculate_adaptive_chunk_size(text)
    
    if chunk_overlap is None:
        chunk_overlap = int(chunk_size * 0.2) # 20% de overlap é o padrão ouro

    print(f"DEBUG CHUNKING: Usando Size={chunk_size} Overlap={chunk_overlap}")

    doc_type = identify_document_type(text)
    
    if doc_type == "legal":
        # Estratégia Jurídica: Quebra primária por Artigos
        raw_parts = re.split(r'(\n\s*(?:Art\.|Artigo)\s?\d+)', text)
        
        parts = []
        if raw_parts:
            parts.append(raw_parts[0]) 
            for i in range(1, len(raw_parts), 2):
                delimiter = raw_parts[i]
                content = raw_parts[i+1] if i+1 < len(raw_parts) else ""
                parts.append(delimiter + content)
    else:
        # Estratégia Normal: Quebra por parágrafos duplos
        parts = text.split('\n\n')

    chunks = []
    current_chunk = ""

    for part in parts:
        if len(part) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            sub_chunks = recursive_internal_split(part, chunk_size, chunk_overlap)
            chunks.extend(sub_chunks)
            
        elif len(current_chunk) + len(part) <= chunk_size:
            current_chunk += part if doc_type == "legal" else part + "\n\n"
            
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            overlap_start = max(0, len(current_chunk) - chunk_overlap)
            current_chunk = current_chunk[overlap_start:] + part

    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return [c for c in chunks if c]

