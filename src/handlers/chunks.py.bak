"""
Chunker Hierárquico e Semântico para Documentos Regulatórios
Otimizado para Resoluções ANEEL e textos legais brasileiros

Este é o módulo central de processamento documental da AGEMS.
Consolida extração de PDF, análise semântica e segmentação hierárquica.
"""

import re
import json
import io
import uuid
import os
import sys
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import pdfplumber

# ================================================================================
# 1. ANÁLISE SEMÂNTICA & AUXILIARES
# ================================================================================

class AnalisadorRegulatorio:
    """Classe para análise e extração de informações regulatórias semânticas"""
    
    @staticmethod
    def extrair_referencias_cruzadas(texto: str) -> List[str]:
        """Extrai referências cruzadas a outros artigos, parágrafos ou leis"""
        referencias = []
        padroes = [
            r'art(?:igo)?\.?\s+(\d+(?:-[A-Z])?)[ºo°]?',
            r'§\s*(\d+(?:-[A-Z])?)[ºo°]?',
            r'inciso\s+([IVXLCDM]+(?:-[A-Z])?)',
            r'Lei\s+n[ºo°]?\s*[\d.]+/\d{4}',
            r'Decreto\s+n[ºo°]?\s*[\d.]+/\d{4}',
            r'Resolução\s+(?:Normativa\s+)?n[ºo°]?\s*[\d.]+/\d{4}',
        ]
        for padrao in padroes:
            matches = re.finditer(padrao, texto, re.IGNORECASE)
            referencias.extend([m.group(0) for m in matches])
        return list(set(referencias))
    
    @staticmethod
    def extrair_valores_numericos(texto: str) -> Dict[str, List]:
        """Extrai valores numéricos importantes (potências, prazos, multas, porcentagens)"""
        valores = {
            'potencias_mw': [],
            'porcentagens': [],
            'prazos_dias': [],
            'valores_monetarios': []
        }
        
        # Potências em MW/kW
        potencias = re.finditer(r'(\d+(?:[.,]\d+)?)\s*(?:MW|kW)', texto, re.IGNORECASE)
        valores['potencias_mw'] = [m.group(0) for m in potencias]
        
        # Porcentagens
        porcentagens = re.finditer(r'(\d+(?:[.,]\d+)?)\s*%', texto)
        valores['porcentagens'] = [m.group(0) for m in porcentagens]
        
        # Prazos em dias/meses
        prazos = re.finditer(r'(\d+)\s*(?:dias|meses)', texto, re.IGNORECASE)
        valores['prazos_dias'] = [m.group(0) for m in prazos]
        
        # Valores monetários
        monetarios = re.finditer(r'R\$\s*[\d.,]+', texto)
        valores['valores_monetarios'] = [m.group(0) for m in monetarios]
        
        return valores
    
    @staticmethod
    def identificar_obrigacoes(texto: str) -> List[str]:
        """Identifica verbos e locuções que indicam obrigatoriedade"""
        obrigacoes = []
        padroes = [
            r'deverá\s+[^.;]+',
            r'é\s+obrigat[oó]rio\s+[^.;]+',
            r'deve\s+[^.;]+',
            r'fica\s+obrigad[oa]\s+[^.;]+',
        ]
        for padrao in padroes:
            matches = re.finditer(padrao, texto, re.IGNORECASE)
            obrigacoes.extend([m.group(0) for m in matches])
        return obrigacoes
    
    @staticmethod
    def identificar_vedacoes(texto: str) -> List[str]:
        """Identifica proibições e vedações"""
        vedacoes = []
        padroes = [
            r'não\s+poder[áa]\s+[^.;]+',
            r'é\s+vedado\s+[^.;]+',
            r'fica\s+proibid[oa]\s+[^.;]+',
            r'não\s+ser[áa]\s+permitido\s+[^.;]+',
        ]
        for padrao in padroes:
            matches = re.finditer(padrao, texto, re.IGNORECASE)
            vedacoes.extend([m.group(0) for m in matches])
        return vedacoes

class OtimizadorConsultas:
    """Otimizador para expansão de termos de busca em regulação"""
    @staticmethod
    def expandir_query(query: str) -> List[str]:
        queries = [query]
        sinonimos = {
            'autorização': ['outorga', 'permissão', 'concessão'],
            'empreendimento': ['projeto', 'instalação', 'usina'],
            'potência': ['capacidade instalada', 'geração'],
            'consumidor': ['usuário', 'titular'],
            'faturamento': ['cobrança', 'conta de luz']
        }
        query_lower = query.lower()
        for termo, s_list in sinonimos.items():
            if termo in query_lower:
                for s in s_list:
                    queries.append(query_lower.replace(termo, s))
        return queries

# ================================================================================
# 2. EXTRAÇÃO DE PDF (PDFPLUMBER)
# ================================================================================

async def extract_text_from_pdf(env, r2_key, start_page=1, limit_pages=100):
    """
    Extrai texto de um PDF armazenado no R2 usando pdfplumber.
    Injeta marcadores de página para preservação de metadados.
    """
    obj = await env.agems_docs.get(r2_key)
    if not obj: raise Exception(f"Arquivo não encontrado: {r2_key}")

    from js import Uint8Array
    pdf_bytes = bytes(Uint8Array.new(await obj.arrayBuffer()))
    texto_acumulado = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        total_pages = len(pdf.pages)
        end_page = min(start_page + limit_pages - 1, total_pages)
        for i in range(start_page - 1, end_page):
            text = pdf.pages[i].extract_text(x_tolerance=2, y_tolerance=3, layout=True)
            if text: texto_acumulado.append(f"[[PAGINA:{i+1}]]\n{text}")
                
    return "\n\n".join(texto_acumulado), total_pages

# ================================================================================
# 3. SEGMENTAÇÃO HIERÁRQUICA (CHUNKING)
# ================================================================================

class TipoElemento(Enum):
    PREAMBULO = "preambulo"
    RESOLUCAO = "resolucao"
    TITULO = "titulo"
    CAPITULO = "capitulo"
    SECAO = "secao"
    SUBSECAO = "subsecao"
    ARTIGO = "artigo"
    PARAGRAFO = "paragrafo"
    INCISO = "inciso"
    ALINEA = "alinea"
    ITEM = "item"
    ANEXO = "anexo"
    CLAUSULA = "clausula"

@dataclass
class ElementoRegulatorio:
    tipo: TipoElemento
    numero: str
    texto: str
    nivel: int
    pagina: int = 1
    revogado: bool = False
    pai: Optional['ElementoRegulatorio'] = None
    contexto_hierarquico: str = ""

class ChunkerRegulatorio:
    def __init__(self, tamanho_max_chunk: int = 1200, overlap_chars: int = 200, manter_contexto: bool = True):
        self.tamanho_max_chunk = tamanho_max_chunk
        self.overlap_chars = overlap_chars
        self.manter_contexto = manter_contexto
        self.analisador = AnalisadorRegulatorio()
        self.padroes = {
            'resolucao': re.compile(r'^RESOLUÇ[ÃãA]O\s+NORMATIVA\s+ANEEL\s+Nº\s+([\d.]+)', re.IGNORECASE | re.MULTILINE),
            'titulo': re.compile(r'^TÍTULO\s+([IVXLCDM\dºª]+)(?:\s*[-–—]?\s*(.*))?$', re.IGNORECASE | re.MULTILINE),
            'capitulo': re.compile(r'^CAPÍTULO\s+([IVXLCDM\dºª]+)(?:\s*[-–—]?\s*(.*))?$', re.IGNORECASE | re.MULTILINE),
            'secao': re.compile(r'^SEÇÃO\s+([IVXLCDM\dºª]+)(?:\s*[-–—]?\s*(.*))?$', re.IGNORECASE | re.MULTILINE),
            'subsecao': re.compile(r'^SUBSEÇÃO\s+([IVXLCDM\dºª]+)(?:\s*[-–—]?\s*(.*))?$', re.IGNORECASE | re.MULTILINE),
            'artigo': re.compile(r'^Art\.\s*(\d+[A-Z-]*)\.?\s*(.*)$', re.IGNORECASE | re.MULTILINE),
            'paragrafo': re.compile(r'^[§õ]\s*(\d+)[-º]*\s*(.*)$', re.MULTILINE),
            'paragrafo_unico': re.compile(r'^Parágrafo único\.\s*(.*)$', re.IGNORECASE | re.MULTILINE),
            'inciso': re.compile(r'^([IVXLCDM]+)\s*[–—\-]\s*(.*)$', re.MULTILINE),
            'alinea': re.compile(r'^([a-z])\)\s*(.*)$', re.MULTILINE),
            'item': re.compile(r'^\s*(\d+(?:\.\d+)*)\s*[\-–—.]\s*(.*)$', re.MULTILINE),
            'anexo': re.compile(r'^ANEXO\s+([IVXLCDM]+|[0-9]+|[A-Z])\s*[-–—]?\s*(.*)$', re.IGNORECASE | re.MULTILINE),
            'clausula': re.compile(r'^CLÁUSULA\s+([A-ZÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ0-9ºª]+(?:\s+[A-ZÁÉÍÓÚÀÈÌÒÙÃÕÂÊÎÔÛÇ0-9ºª]+){0,5})\s*[:–—]?\s*(.*)$', re.IGNORECASE | re.MULTILINE),
            'revogado': re.compile(r'\((?:revogad[oa]|suprimid[oa]|exclu[íi]d[oa]|eliminad[oa])(?:[\s\S]*?)\)', re.IGNORECASE),
            'marcador_pagina': re.compile(r'\[\[PAGINA:(\d+)\]\]', re.MULTILINE),
            'trash': [
                r'Este texto não substitui o (?:publicado|republicado) no Diário Oficial.*',
                r'Publicado no DOU de \d{2}/\d{2}/\d{2}.*',
                r'Diário Oficial da União\s?-\s?Seção\s?\d+.*',
                r'Page \d+ of \d+.*',
                r'^\s*\d+\s*$',
                r'\d{2}/\d{2}/\d{2},?\s*\d{2}:\d{2}'
            ]
        }

    def limpar_texto(self, texto: str) -> str:
        padrões_lixo = [
            r'(?i)ANDRÉ\s+PEPITONE\s+DA\s+NÓBREGA.*',
            r'(?i)HÉLVIO\s+NEVES\s+GUERRA.*',
            r'(?i)SANDRO\s+LAZZARI.*',
            r'(?i)ÍNDICE.*',
            r'(?i)Este texto não substitui o (?:publicado|republicado).*',
            r'(?i)retificado no D\.O\. de .*',
            r'(?i)\(\*\)\s*Republicado em razão de incorreções.*'
        ]
        for p in padrões_lixo: texto = re.sub(p, '', texto, flags=re.MULTILINE)
        for p in self.padroes['trash']: texto = re.sub(p, '', texto, flags=re.IGNORECASE | re.MULTILINE)
        
        cf = {'TÃTULO': 'TÍTULO', 'CAPÃTULO': 'CAPÍTULO', 'Ã§Ã£o': 'ção', 'Ã§Ãµes': 'ções',
              'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú', 'Ã': 'à', 'Ãª': 'ê', 
              'Ã´': 'ô', 'Ã§': 'ç', 'à': 'ã', '┴': 'Á', '╔': 'É', 'Ý': 'í', 
              'þ': 'ã', 'ú': 'í', 'Ò': 'Õ', 'Ó': 'à', 'û': '–'}
        for b, f in cf.items(): texto = texto.replace(b, f)
        texto = re.sub(r'õ(\s*\d)', r'§\1', texto)
        return texto.strip()

    def _normalizar_estrutura(self, texto: str) -> str:
        quebras = [r'([.;!?])\s*(TÍTULO\s+)', r'([.;!?])\s*(CAPÍTULO\s+)', r'([.;!?])\s*(SEÇÃO\s+)', 
                   r'([.;!?])\s*(SUBSEÇÃO\s+)', r'([.;!?])\s*(CLÁUSULA\s+)']
        for p in quebras: texto = re.sub(p, r'\1\n\2', texto)
        texto = re.sub(r'([.;!?])\s*(ANEXO\s+[IVXLCDM0-9A-Z]+)', r'\1\n\n\2', texto)
        texto = re.sub(r'(?m)^ *(ANEXO\s+[IVXLCDM0-9A-Z]+)', r'\n\1', texto) 
        texto = re.sub(r'(?m)^ *(CLÁUSULA\s+)', r'\n\1', texto) 
        return re.sub(r'([a-z0-9áàâãéêíóôõúç);:])\s+(Art\.?\s*\d+)', r'\1\n\2', texto)

    def parse_documento(self, texto: str) -> List[ElementoRegulatorio]:
        texto = self.limpar_texto(texto)
        texto = self._normalizar_estrutura(texto)
        elementos, linhas = [], texto.split('\n')
        elemento_atual, texto_acumulado, pagina_atual, sequencias = None, [], 1, {}

        for linha in linhas:
            linha = linha.strip()
            if not linha: continue
            if m_pag := self.padroes['marcador_pagina'].match(linha):
                pagina_atual = int(m_pag.group(1))
                continue

            elemento_id = None
            def romano_v(s):
                val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
                res, s = 0, s.upper()
                for i in range(len(s)):
                    if i > 0 and val[s[i]] > val[s[i-1]]: res += val[s[i]] - 2 * val[s[i-1]]
                    else: res += val[s[i]]
                return res

            def get_ctx(tipo):
                niv = {TipoElemento.RESOLUCAO: 0, TipoElemento.TITULO: 1, TipoElemento.ANEXO: 1,
                       TipoElemento.CAPITULO: 2, TipoElemento.SECAO: 3, TipoElemento.SUBSECAO: 4, 
                       TipoElemento.ARTIGO: 5, TipoElemento.CLAUSULA: 5, TipoElemento.PARAGRAFO: 6, 
                       TipoElemento.INCISO: 7, TipoElemento.ALINEA: 8, TipoElemento.ITEM: 9}
                n_alvo = niv.get(tipo, 10)
                # Artigos e acima são globais (Título, Capítulo, Seção etc)
                # Para evitar cortes em documentos longos onde a numeração se mantém única
                if n_alvo <= 5: return "doc"
                curr = elemento_atual
                while curr and curr.nivel >= n_alvo: curr = curr.pai
                if not curr: return "doc"
                return f"{curr.contexto_hierarquico} > {curr.tipo.value}_{curr.numero}"

            def val_seq(tipo, num_str):
                if num_str == "único": return True
                try: 
                    if tipo == TipoElemento.INCISO: num = romano_v(re.findall(r'[IVXLCDM]+', num_str, re.I)[0])
                    elif tipo == TipoElemento.ALINEA: num = ord(num_str.lower()[0]) - ord('a') + 1
                    else: num = int(re.findall(r'\d+', num_str)[0])
                    key = f"{get_ctx(tipo)}|{tipo.value}"
                    ult = sequencias.get(key, 0)
                    # Permite saltos de até 5 para ser leniente com documentos irregulares
                    if num == 1 or num == ult + 1 or num == ult or (num > ult and num < ult + 5):
                        sequencias[key] = num
                        return True
                    return False
                except: return True 

            if m := self.padroes['resolucao'].match(linha):
                elemento_id = ElementoRegulatorio(TipoElemento.RESOLUCAO, m.group(1), linha, 0, pagina_atual)
            elif m := self.padroes['titulo'].match(linha):
                elemento_id = ElementoRegulatorio(TipoElemento.TITULO, m.group(1), linha, 1, pagina_atual)
            elif m := self.padroes['capitulo'].match(linha):
                elemento_id = ElementoRegulatorio(TipoElemento.CAPITULO, m.group(1), linha, 2, pagina_atual)
            elif m := self.padroes['secao'].match(linha):
                elemento_id = ElementoRegulatorio(TipoElemento.SECAO, m.group(1), linha, 3, pagina_atual)
            elif m := self.padroes['artigo'].match(linha):
                if val_seq(TipoElemento.ARTIGO, m.group(1)):
                    elemento_id = ElementoRegulatorio(TipoElemento.ARTIGO, m.group(1), linha, 5, pagina_atual)
            elif m := self.padroes['clausula'].match(linha):
                elemento_id = ElementoRegulatorio(TipoElemento.CLAUSULA, m.group(1).strip(':'), linha, 5, pagina_atual)
            elif m := self.padroes['anexo'].match(linha):
                if m.group(1) == "III" or (m.group(1) == "I" and "CONTRATO" in linha.upper()):
                    elemento_id = ElementoRegulatorio(TipoElemento.PREAMBULO, m.group(1), linha, 0, pagina_atual)
                else:
                    elemento_id = ElementoRegulatorio(TipoElemento.ANEXO, m.group(1), linha, 1, pagina_atual)
                for k in list(sequencias.keys()): 
                    if "|" in k and not (k.startswith("doc|") or "anexo" in k.lower()): del sequencias[k]
            elif m := self.padroes['paragrafo_unico'].match(linha):
                elemento_id = ElementoRegulatorio(TipoElemento.PARAGRAFO, "único", linha, 6, pagina_atual)
            elif m := self.padroes['paragrafo'].match(linha):
                if val_seq(TipoElemento.PARAGRAFO, m.group(1)):
                    elemento_id = ElementoRegulatorio(TipoElemento.PARAGRAFO, m.group(1), linha, 6, pagina_atual)
            elif m := self.padroes['inciso'].match(linha):
                if val_seq(TipoElemento.INCISO, m.group(1)):
                    elemento_id = ElementoRegulatorio(TipoElemento.INCISO, m.group(1), linha, 7, pagina_atual)
            elif m := self.padroes['alinea'].match(linha):
                if val_seq(TipoElemento.ALINEA, m.group(1)):
                    elemento_id = ElementoRegulatorio(TipoElemento.ALINEA, m.group(1), linha, 8, pagina_atual)
            elif m := self.padroes['item'].match(linha):
                elemento_id = ElementoRegulatorio(TipoElemento.ITEM, m.group(1).strip('.'), linha, 9, pagina_atual)

            if elemento_id:
                if elemento_atual: 
                    elemento_atual.texto = '\n'.join(texto_acumulado)
                    elementos.append(elemento_atual)
                else:
                    if texto_acumulado:
                        elementos.append(ElementoRegulatorio(TipoElemento.PREAMBULO, "0", '\n'.join(texto_acumulado), 0, 1, contexto_hierarquico="Preâmbulo"))
                elemento_id.texto = linha
                elemento_atual, texto_acumulado = elemento_id, [linha]
                self._estabelecer_hierarquia(elementos + [elemento_atual])
            else:
                texto_acumulado.append(linha)
        
        if elemento_atual: 
            elemento_atual.texto = '\n'.join(texto_acumulado)
            elementos.append(elemento_atual)
            
        self._estabelecer_hierarquia(elementos)
        return self._deduplicar_elementos(elementos)

    def _deduplicar_elementos(self, elementos):
        mapa_final, vistos = {}, set()
        for e in elementos:
            if e.tipo == TipoElemento.PREAMBULO: continue
            chave = f"{e.tipo.value}|{e.numero}|{e.contexto_hierarquico}"
            if chave not in mapa_final or any(x in e.texto.lower() for x in ["redação dada", "incluído"]):
                mapa_final[chave] = e
        
        res = []
        for e in elementos:
            if e.tipo == TipoElemento.PREAMBULO:
                res.append(e)
                continue
            chave = f"{e.tipo.value}|{e.numero}|{e.contexto_hierarquico}"
            if chave not in vistos:
                res.append(mapa_final[chave])
                vistos.add(chave)
        return res

    def _estabelecer_hierarquia(self, elementos):
        pilha, nomes = [], {
            TipoElemento.TITULO: "Título", TipoElemento.CAPITULO: "Capítulo",
            TipoElemento.SECAO: "Seção", TipoElemento.SUBSECAO: "Subseção", TipoElemento.ARTIGO: "Artigo",
            TipoElemento.PARAGRAFO: "Parágrafo", TipoElemento.INCISO: "Inciso", TipoElemento.ALINEA: "Alínea",
            TipoElemento.ITEM: "Item", TipoElemento.ANEXO: "Anexo", TipoElemento.CLAUSULA: "Cláusula"
        }
        for e in elementos:
            while pilha and pilha[-1].nivel >= e.nivel: pilha.pop()
            if pilha: e.pai = pilha[-1]
            parts, curr = [], e
            while curr and curr.pai:
                curr = curr.pai
                if curr.tipo in nomes:
                    num_display = curr.numero
                    prefix = f"{nomes[curr.tipo]} {num_display}"
                    if curr.tipo == TipoElemento.PARAGRAFO: prefix = f"§ {num_display}" if num_display != "único" else "Parágrafo Único"
                    elif curr.tipo == TipoElemento.INCISO: prefix = f"Inc. {num_display}"
                    parts.insert(0, prefix)
            e.contexto_hierarquico = " > ".join(parts)
            pilha.append(e)

    def criar_chunks(self, texto: str) -> List[Dict]:
        elementos = [e for e in self.parse_documento(texto) if not self.padroes['revogado'].search(e.texto)]
        chunks, chunk_id = [], 0
        for e in elementos:
            if "ANEXO IV" in e.contexto_hierarquico.upper() or (e.tipo == TipoElemento.ANEXO and e.numero == "IV"):
                for line in e.texto.split('\n'):
                    if line.strip():
                        chunks.append(self._formatar_chunk(line.strip(), e, chunk_id))
                        chunk_id += 1
                continue
            if "ANEXO III" in e.contexto_hierarquico.upper() or (e.tipo == TipoElemento.ANEXO and e.numero == "III"):
                chunks.append(self._formatar_chunk(e.texto, e, chunk_id))
                chunk_id += 1
                continue
            if e.tipo in [TipoElemento.TITULO, TipoElemento.CAPITULO, TipoElemento.SECAO, TipoElemento.ANEXO]:
                if len(e.texto) < 500:
                    chunks.append(self._formatar_chunk(f"MARCADOR_ESTRUTURAL: {e.texto}", e, chunk_id))
                    chunk_id += 1
                    continue
            if len(e.texto) <= self.tamanho_max_chunk:
                chunks.append(self._formatar_chunk(e.texto, e, chunk_id))
                chunk_id += 1
            else:
                for sub in self._dividir_texto(e):
                    chunks.append(self._formatar_chunk(sub, e, chunk_id, parte=True))
                    chunk_id += 1
        return chunks

    def _formatar_chunk(self, texto, e, cid, parte=False):
        prefix = f"[{e.contexto_hierarquico}] " if e.contexto_hierarquico else ""
        return {'chunk_id': f"chunk_{cid}", 'texto': f"{prefix}{texto}", 'tipo': e.tipo.value, 'numero': e.numero,
                'nivel': e.nivel, 'contexto_hierarquico': e.contexto_hierarquico, 'pagina': e.pagina,
                'tamanho': len(texto), 'parte_de_elemento_maior': parte,
                'semantica': {'obrigacoes': self.analisador.identificar_obrigacoes(texto),
                             'vedacoes': self.analisador.identificar_vedacoes(texto),
                             'referencias': self.analisador.extrair_referencias_cruzadas(texto),
                             'valores': self.analisador.extrair_valores_numericos(texto)}}

    def _dividir_texto(self, e):
        sentencas = re.split(r'(?<=[.;!?])\s+', e.texto)
        chunks, atual = [], ""
        for s in sentencas:
            if len(atual) + len(s) > self.tamanho_max_chunk:
                if atual: chunks.append(atual)
                atual = s
            else: atual += (' ' if atual else '') + s
        if atual: chunks.append(atual)
        return chunks

# ================================================================================
# 4. HANDLERS E UTILITÁRIOS DE EXECUÇÃO
# ================================================================================

async def handle_process(request, env):
    try:
        from js import JSON
        from pyodide.ffi import to_js
        from utils.vectorize import process_and_vectorize_chunks
        body = (await request.json()).to_py()
        document_id = body.get("document_id")
        start_chunk = body.get("start_chunk", 0)
        limit_chunks = body.get("limit_chunks", 50)
        if not document_id: return Response.new(json.dumps({"error": "document_id is required"}), to_js({"status": 400}))
        doc_result = (await env.agems_rag_db.prepare("SELECT * FROM documents WHERE id = ?").bind(document_id).first()).to_py()
        if not doc_result: return Response.new(json.dumps({"error": "Document not found"}), to_js({"status": 404}))
        full_text, total_pages = await extract_text_from_pdf(env, doc_result["r2_key"], limit_pages=100)
        chunker = ChunkerRegulatorio()
        chunks = chunker.criar_chunks(full_text)
        processed = await process_and_vectorize_chunks(env, document_id, doc_result, chunks, start_chunk, limit_chunks)
        total = len(chunks)
        current = start_chunk + processed
        finished = current >= total
        status = 'processed' if finished else 'processing'
        await env.agems_rag_db.prepare("UPDATE documents SET status = ?, chunk_count = ? WHERE id = ?").bind(status, current, document_id).run()
        return Response.new(json.dumps({"success": True, "total_processed": current, "total_chunks": total, "is_finished": finished, "chunks_in_batch": processed}), JSON.parse(json.dumps({"headers": {"Content-Type": "application/json"}})))
    except Exception as e:
        import traceback
        return Response.new(json.dumps({"error": str(e), "trace": traceback.format_exc()}), to_js({"status": 500}))

async def handle_add_chunks(request, env):
    try:
        from js import JSON
        from utils.vectorize import process_and_vectorize_chunks
        body = (await request.json()).to_py()
        document_id = request.url.split("/documents/")[1].split("/chunks")[0]
        chunks_data = body.get("chunks", [])
        doc_db = (await env.agems_rag_db.prepare("SELECT * FROM documents WHERE id = ?").bind(document_id).first()).to_py()
        meta = {**body.get("metadata", {}), **doc_db}
        processed = await process_and_vectorize_chunks(env, document_id, meta, chunks_data)
        await env.agems_rag_db.prepare("UPDATE documents SET chunk_count = chunk_count + ? WHERE id = ?").bind(processed, document_id).run()
        return Response.new(json.dumps({"success": True, "processed": processed}), to_js({"headers": {"Content-Type": "application/json"}}))
    except Exception as e: return Response.new(json.dumps({"error": str(e)}), to_js({"status": 500}))

# ================================================================================
# 5. MODO LOCAL E TESTES
# ================================================================================

def exportar_txt(chunks: List[Dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE CHUNKS CONSOLIDADO\n" + "="*80 + "\n")
        for c in chunks:
            f.write(f"\nCHUNK {c['chunk_id']} | PÁG: {c['pagina']} | TIPO: {c['tipo']}\n")
            f.write(f"CONTEXTO: {c['contexto_hierarquico']}\n" + "-"*80 + f"\n{c['texto']}\n")

if __name__ == "__main__":
    pdf_local = r"c:/Users/rlazaro/Documents/Projetos_AGEMS/agems-rag-api/documentos_para_processar/REN_1000_ANEEL.pdf"
    if os.path.exists(pdf_local):
        print("🚀 Processando localmente com PDFPLUMBER...")
        with pdfplumber.open(pdf_local) as pdf:
            total_paginas = len(pdf.pages)
            text_parts = []
            for i, p in enumerate(pdf.pages):
                pct = (i + 1) / total_paginas * 100
                print(f"\r📄 Extraindo texto: página {i+1}/{total_paginas} [{pct:5.1f}%] {'█' * int(pct/5)}{'░' * (20 - int(pct/5))}", end="", flush=True)
                text_parts.append(f"[[PAGINA:{i+1}]]\n{p.extract_text(layout=True) or ''}")
            
            print("\n🔍 Analisando estrutura hierárquica e gerando chunks...")
            full_text = "\n\n".join(text_parts)
            chunks = ChunkerRegulatorio().criar_chunks(full_text)
            print(f"✅ {len(chunks)} chunks gerados com sucesso.")
            exportar_txt(chunks, pdf_local.replace(".pdf", "_consolidado.txt"))
            print(f"💾 Relatório consolidado salvo em: {pdf_local.replace('.pdf', '_consolidado.txt')}")