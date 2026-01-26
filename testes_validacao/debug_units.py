import sys
import os
import re

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.chunking import clean_pdf_text
import pypdf

def debug_units(filepath):
    reader = pypdf.PdfReader(filepath)
    text_parts = []
    for page in reader.pages[:10]: # 10 páginas
        t = page.extract_text()
        if t:
            text_parts.append(t.replace('\x00', '').strip())
    text = "\n\n".join(text_parts)
    text = clean_pdf_text(text)

    pattern = r'(\s(?:TÍTULO\s*[IVXLCDM\d]+|CAPÍTULO\s*[IVXLCDM\d]+|SEÇÃO\s*[IVXLCDM\d]+|SUBSEÇÃO\s*[IVXLCDM\d]+|Art\.\s?\d+|Artigo\s?\d+|§\s?\d+|Parágrafo\s?único|[IVXLCDM]+\s?-))'
    raw_parts = re.split(pattern, text)
    
    units = []
    if raw_parts[0].strip():
        units.append(raw_parts[0].strip())
    
    for i in range(1, len(raw_parts), 2):
        delimiter = raw_parts[i]
        content = raw_parts[i+1] if i+1 < len(raw_parts) else ""
        units.append((delimiter + content).strip())

    print(f"Total de unidades detectadas: {len(units)}")
    for i, u in enumerate(units[:20]):
        print(f"UNIT {i} (first 100 chars): {u[:100].replace('\n', ' ')}")

if __name__ == "__main__":
    debug_units("documentos_para_processar/REN_1000_ANEEL.pdf")
