import sys
import os
import re
import pypdf

# Adiciona o diretório 'src' ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.chunking import clean_pdf_text

filepath = "documentos_para_processar/REN_1000_ANEEL.pdf"
reader = pypdf.PdfReader(filepath)
text = "\n".join([p.extract_text() or "" for p in reader.pages[:5]])
text = clean_pdf_text(text)

with open("testes_validacao/raw_text_dump.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("Dumped first 5 pages to raw_text_dump.txt")
