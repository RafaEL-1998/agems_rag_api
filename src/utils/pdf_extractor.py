import io

async def extract_text_from_pdf(env, r2_key, start_page=0, limit_pages=50):
    """ Extrai texto de um range de páginas de um PDF no R2 """
    import PyPDF2
    
    # Recuperar arquivo do R2
    r2_object = await env.agems_docs.get(r2_key)
    if not r2_object:
        raise Exception(f"Arquivo não encontrado no R2: {r2_key}")

    # arrayBuffer() retorna o conteúdo do arquivo
    array_buffer = await r2_object.arrayBuffer()
    
    # IMPORTANTE: Converter JS ArrayBuffer para bytes de forma eficiente
    from js import Uint8Array
    pdf_bytes = bytes(Uint8Array.new(array_buffer))
    
    # Agora sim podemos usar io.BytesIO
    pdf_file = io.BytesIO(pdf_bytes)

    # Extrair texto usando PyPDF2
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    total_pages = len(pdf_reader.pages)
    
    end_page = min(start_page + limit_pages, total_pages)
    pages_text = []

    for i in range(start_page, end_page):
        page = pdf_reader.pages[i]
        text = page.extract_text()
        if text:
            pages_text.append(text)

    return "\n\n".join(pages_text), total_pages


