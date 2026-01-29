"""
Módulo de Extração de Texto de PDF
Responsável por processar PDFs e converter para texto com marcadores de página
"""

import pdfplumber


def extract_text_from_pdf_local(pdf_path: str, verbose: bool = True) -> str:
    """
    Extrai texto de um PDF local com animação de progresso.
    Junta linhas quebradas por mudança de página para evitar fragmentação.
    
    Args:
        pdf_path: Caminho do arquivo PDF
        verbose: Se True, mostra progresso no terminal
        
    Returns:
        str: Texto extraído com marcadores de página
    """
    with pdfplumber.open(pdf_path) as pdf:
        total_paginas = len(pdf.pages)
        text_parts = []
        
        for i, p in enumerate(pdf.pages):
            if verbose:
                pct = (i + 1) / total_paginas * 100
                barra = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
                print(
                    f"\r📄 Extraindo texto: página {i+1}/{total_paginas} "
                    f"[{pct:5.1f}%] {barra}",
                    end="",
                    flush=True
                )
            
            texto = p.extract_text(layout=True) or ''
            
            # Se não é a primeira página, verifica se deve juntar com a anterior
            if i > 0 and text_parts:
                ultima_parte = text_parts[-1]
                linhas_anteriores = ultima_parte.split('\n')
                
                # Pega a última linha da página anterior (ignorando vazias)
                ultima_linha = ''
                for linha in reversed(linhas_anteriores):
                    if linha.strip():
                        ultima_linha = linha.strip()
                        break
                
                # Pega a primeira linha da página atual (ignorando vazias)
                primeira_linha = ''
                for linha in texto.split('\n'):
                    if linha.strip():
                        primeira_linha = linha.strip()
                        break
                
                # Verifica se deve juntar as linhas
                deve_juntar = False
                
                if ultima_linha and primeira_linha:
                    # Caso 1: Última linha não termina com pontuação e primeira não começa com maiúscula/número
                    if (not ultima_linha.endswith(('.', ';', ':', '!', '?', ')')) and
                        not primeira_linha[0].isupper() and
                        not primeira_linha[0].isdigit()):
                        deve_juntar = True
                    
                    # Caso 2: Última linha termina com preposição ou conjunção curta
                    preposicoes_curtas = ['de', 'da', 'do', 'em', 'ou', 'e', 'a', 'o', 'à', 'ao']
                    ultima_palavra = ultima_linha.split()[-1].lower().rstrip(',;')
                    if ultima_palavra in preposicoes_curtas:
                        deve_juntar = True
                    
                    # Caso 3: Primeira linha começa com data/número entre parênteses (continuação de referência)
                    if primeira_linha.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')) and ')' in primeira_linha[:15]:
                        deve_juntar = True
                
                if deve_juntar:
                    # Junta as linhas removendo a quebra
                    texto_anterior_sem_ultima = '\n'.join(linhas_anteriores[:-1])
                    text_parts[-1] = texto_anterior_sem_ultima + '\n' + ultima_linha + ' ' + texto
                    continue
            
            text_parts.append(f"[[PAGINA:{i+1}]]\n{texto}")
        
        if verbose:
            print()  # Nova linha após a barra de progresso
            
        return "\n\n".join(text_parts)