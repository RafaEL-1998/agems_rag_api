import PyPDF2
import io

async def extract_text_from_pdf(env, r2_key):
    """ Extrai texto de um PDF armazenado no R2 """
    
    # Recuperar arquivo do R2
    r2_object = await env.R2_BUCKET.get(r2_key)
    # arrayBuffer() é a sequência de bytes do arquivo compatível com Workers
    pdf_bytes = await r2_object.arrayBuffer() 

    # Converter para bytes Python
    pdf_file = io.BytesIO(bytes(pdf_bytes))

    # Extrair texto usando PyPDF2
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    full_text = ""

    # Percorre todas as páginas do PDF, extrai o texto de cada uma, 
    # junta tudo em uma única string e remove espaços extras do começo e do fim.
    for page in pdf_reader.pages:
        full_text += page.extract_text() + "\n\n"

    return full_text.strip()