import pypdf
import os

filepath = "documentos_para_processar/REN_1000_ANEEL.pdf"
reader = pypdf.PdfReader(filepath)
text_parts = []
for page in reader.pages[:2]: # Só as 2 primeiras páginas
    t = page.extract_text()
    if t:
        text_parts.append(t.replace('\x00', '').strip())
full_text = "\n\n".join(text_parts)

print("--- INÍCIO DO TEXTO EXTRAÍDO (Pág 1-2) ---")
print(full_text[:3000])
print("--- FIM DO TEXTO ---")
