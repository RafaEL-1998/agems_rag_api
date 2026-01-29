"""
Chunker Hierárquico e Semântico para Documentos Regulatórios
Módulo principal de segmentação e processamento
"""

import re
import json
import os
from typing import List, Dict, Optional
from hierarchy_semantics import (
    AnalisadorRegulatorio,
    TipoElemento,
    ElementoRegulatorio,
    PadroesRegulatorios,
    LimpadorTexto,
    UtilitariosHierarquia
)


class ChunkerRegulatorio:
    """
    Classe principal para segmentação hierárquica de documentos regulatórios.
    Processa texto e cria chunks mantendo contexto hierárquico e semântico.
    """
    
    def __init__(
        self,
        tamanho_max_chunk: int = 1200,
        overlap_chars: int = 200,
        manter_contexto: bool = True
    ):
        self.tamanho_max_chunk = tamanho_max_chunk
        self.overlap_chars = overlap_chars
        self.manter_contexto = manter_contexto
        self.analisador = AnalisadorRegulatorio()
        self.padroes_obj = PadroesRegulatorios()
        self.padroes = self.padroes_obj.padroes
        self.limpador = LimpadorTexto()
        self.utils = UtilitariosHierarquia()

    def limpar_texto(self, texto: str) -> str:
        """Limpa e normaliza o texto do documento"""
        return self.limpador.limpar(texto)

    def _normalizar_estrutura(self, texto: str) -> str:
        """Normaliza a estrutura do texto para melhor parsing"""
        return self.limpador.normalizar_estrutura(texto)

    def parse_documento(self, texto: str) -> List[ElementoRegulatorio]:
        """
        Analisa o documento e extrai sua estrutura hierárquica.
        
        Args:
            texto: Texto do documento a ser processado
            
        Returns:
            Lista de ElementoRegulatorio com a estrutura hierárquica
        """
        texto = self.limpar_texto(texto)
        texto = self._normalizar_estrutura(texto)
        
        elementos = []
        linhas = texto.split('\n')
        elemento_atual = None
        texto_acumulado = []
        pagina_atual = 1
        sequencias = {}  # Rastreia numeração sequencial por contexto
        em_inclusao_resolucao = False

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Verifica marcador de página
            if m_pag := self.padroes['marcador_pagina'].match(linha):
                pagina_atual = int(m_pag.group(1))
                continue
            
            # Limpeza do PDF
            if any(re.search(p, linha) for p in self.padroes['trash']):
                continue

            if self.padroes['inicio_inclusao'].search(linha):
                if texto_acumulado:
                    texto_acumulado[-1] += " " + linha
                else:
                    texto_acumulado.append(linha)
                em_inclusao_resolucao = True
                continue

            if em_inclusao_resolucao:
                if texto_acumulado:
                    texto_acumulado[-1] += " " + linha
                else:
                    texto_acumulado.append(linha)

                if self.padroes['fim_inclusao'].search(linha):
                    em_inclusao_resolucao = False
                continue

            elemento_identificado = None
    
            # Funções auxiliares para validação de sequência
            def obter_contexto(tipo):
                """Determina o contexto para validação de sequência"""
                nivel_alvo = self.utils.obter_nivel_por_tipo(tipo)
                # Artigos e acima são globais
                if nivel_alvo <= 5:
                    return "doc"
                curr = elemento_atual
                while curr and curr.nivel >= nivel_alvo:
                    curr = curr.pai
                if not curr:
                    return "doc"
                return f"{curr.contexto_hierarquico} > {curr.tipo.value}_{curr.numero}"

            def validar_sequencia(tipo, num_str):
                """Valida se a numeração está em sequência válida"""
                if num_str == "único":
                    return True
                
                try:
                    # Extrai apenas o número base (ignora sufixos como -A, -B)
                    if tipo == TipoElemento.INCISO:
                        # Pega apenas os algarismos romanos, ignora sufixos
                        match = re.match(r'([IVXLCDM]+)', num_str, re.I)
                        if not match:
                            return True
                        num = self.utils.romano_para_valor(match.group(1))
                    elif tipo == TipoElemento.ALINEA:
                        num = ord(num_str.lower()[0]) - ord('a') + 1
                    else:
                        # Para artigos e parágrafos, pega apenas o número base
                        match = re.match(r'(\d+)', num_str)
                        if not match:
                            return True
                        num = int(match.group(1))
                    
                    key = f"{obter_contexto(tipo)}|{tipo.value}"
                    ultimo = sequencias.get(key, 0)
                    
                    # Aceita se:
                    # - É o primeiro (num == 1)
                    # - É sequencial (num == ultimo + 1)
                    # - É repetição do mesmo número (num == ultimo) - para variações tipo I, I-A
                    # - É um salto pequeno (até 5) - para elementos revogados
                    if (num == 1 or num == ultimo + 1 or num == ultimo or 
                        (num > ultimo and num < ultimo + 5)):
                        # Só atualiza a sequência se for maior (para aceitar I e I-A no mesmo contexto)
                        if num > ultimo:
                            sequencias[key] = num
                        return True
                    return False
                except:
                    return True

            # Identificação de elementos estruturais
            if m := self.padroes['resolucao'].match(linha):
                elemento_identificado = ElementoRegulatorio(
                    TipoElemento.RESOLUCAO, m.group(1), linha, 0, pagina_atual
                )
            
            elif m := self.padroes['titulo'].match(linha):
                elemento_identificado = ElementoRegulatorio(
                    TipoElemento.TITULO, m.group(1), linha, 1, pagina_atual
                )
            
            elif m := self.padroes['capitulo'].match(linha):
                elemento_identificado = ElementoRegulatorio(
                    TipoElemento.CAPITULO, m.group(1), linha, 2, pagina_atual
                )
            
            elif m := self.padroes['secao'].match(linha):
                elemento_identificado = ElementoRegulatorio(
                    TipoElemento.SECAO, m.group(1), linha, 3, pagina_atual
                )
            
            elif m := self.padroes['artigo'].match(linha):
                if validar_sequencia(TipoElemento.ARTIGO, m.group(1)):
                    elemento_identificado = ElementoRegulatorio(
                        TipoElemento.ARTIGO, m.group(1), linha, 5, pagina_atual
                    )
            
            elif m := self.padroes['clausula'].match(linha):
                elemento_identificado = ElementoRegulatorio(
                    TipoElemento.CLAUSULA, m.group(1).strip(':'), linha, 5, pagina_atual
                )
            
            elif m := self.padroes['anexo'].match(linha):
                # Tratamento especial para Anexo III (preâmbulo) e Anexo IV
                if m.group(1) == "III" or (m.group(1) == "I" and "CONTRATO" in linha.upper()):
                    elemento_identificado = ElementoRegulatorio(
                        TipoElemento.PREAMBULO, m.group(1), linha, 0, pagina_atual
                    )
                else:
                    elemento_identificado = ElementoRegulatorio(
                        TipoElemento.ANEXO, m.group(1), linha, 1, pagina_atual
                    )
                # Limpa sequências ao entrar em anexo
                for k in list(sequencias.keys()):
                    if "|" in k and not (k.startswith("doc|") or "anexo" in k.lower()):
                        del sequencias[k]
            
            elif m := self.padroes['paragrafo_unico'].match(linha):
                elemento_identificado = ElementoRegulatorio(
                    TipoElemento.PARAGRAFO, "único", linha, 6, pagina_atual
                )
            
            elif m := self.padroes['paragrafo'].match(linha):
                if validar_sequencia(TipoElemento.PARAGRAFO, m.group(1)):
                    elemento_identificado = ElementoRegulatorio(
                        TipoElemento.PARAGRAFO, m.group(1), linha, 6, pagina_atual
                    )
            
            elif m := self.padroes['inciso'].match(linha):
                if validar_sequencia(TipoElemento.INCISO, m.group(1)):
                    elemento_identificado = ElementoRegulatorio(
                        TipoElemento.INCISO, m.group(1), linha, 7, pagina_atual
                    )
            
            elif m := self.padroes['alinea'].match(linha):
                if validar_sequencia(TipoElemento.ALINEA, m.group(1)):
                    elemento_identificado = ElementoRegulatorio(
                        TipoElemento.ALINEA, m.group(1), linha, 8, pagina_atual
                    )
            
            elif m := self.padroes['item'].match(linha):
                elemento_identificado = ElementoRegulatorio(
                    TipoElemento.ITEM, m.group(1).strip('.'), linha, 9, pagina_atual
                )

            # Se identificou novo elemento, salva o anterior
            if elemento_identificado:
                if elemento_atual:
                    elemento_atual.texto = '\n'.join(texto_acumulado)
                    elementos.append(elemento_atual)
                else:
                    # Texto antes do primeiro elemento = preâmbulo
                    if texto_acumulado:
                        elementos.append(
                            ElementoRegulatorio(
                                TipoElemento.PREAMBULO,
                                "0",
                                '\n'.join(texto_acumulado),
                                0,
                                1,
                                contexto_hierarquico="Preâmbulo"
                            )
                        )
                
                elemento_identificado.texto = linha
                elemento_atual = elemento_identificado
                texto_acumulado = [linha]
                self._estabelecer_hierarquia(elementos + [elemento_atual])
            else:
                texto_acumulado.append(linha)
        
        # Salva o último elemento
        if elemento_atual:
            elemento_atual.texto = '\n'.join(texto_acumulado)
            elementos.append(elemento_atual)

        self._estabelecer_hierarquia(elementos)
        return self._deduplicar_elementos(elementos)

    def _deduplicar_elementos(self, elementos: List[ElementoRegulatorio]) -> List[ElementoRegulatorio]:
        """Remove duplicatas mantendo versões mais recentes"""
        mapa_final = {}
        vistos = set()
        
        for e in elementos:
            if e.tipo == TipoElemento.PREAMBULO:
                continue
            
            chave = f"{e.tipo.value}|{e.numero}|{e.contexto_hierarquico}"
            # Prioriza versões com "redação dada" ou "incluído"
            if (chave not in mapa_final or 
                any(x in e.texto.lower() for x in ["redação dada", "incluído"])):
                mapa_final[chave] = e
        
        resultado = []
        for e in elementos:
            if e.tipo == TipoElemento.PREAMBULO:
                resultado.append(e)
                continue
            
            chave = f"{e.tipo.value}|{e.numero}|{e.contexto_hierarquico}"
            if chave not in vistos:
                resultado.append(mapa_final[chave])
                vistos.add(chave)
        
        return resultado

    def _estabelecer_hierarquia(self, elementos: List[ElementoRegulatorio]):
        """Estabelece relações pai-filho e constrói contexto hierárquico"""
        pilha = []
        
        for e in elementos:
            # Remove elementos de nível maior ou igual da pilha
            while pilha and pilha[-1].nivel >= e.nivel:
                pilha.pop()
            
            # Define pai
            if pilha:
                e.pai = pilha[-1]
            
            # Constrói contexto hierárquico
            partes = []
            curr = e
            while curr and curr.pai:
                curr = curr.pai
                if curr.tipo in [TipoElemento.TITULO, TipoElemento.CAPITULO,
                                TipoElemento.SECAO, TipoElemento.SUBSECAO,
                                TipoElemento.ARTIGO, TipoElemento.PARAGRAFO,
                                TipoElemento.INCISO, TipoElemento.ALINEA,
                                TipoElemento.ITEM, TipoElemento.ANEXO,
                                TipoElemento.CLAUSULA]:
                    
                    num_display = curr.numero
                    nome = self.utils.obter_nome_exibicao(curr.tipo)
                    
                    # Formatação especial para alguns tipos
                    if curr.tipo == TipoElemento.PARAGRAFO:
                        if num_display == "único":
                            prefix = "Parágrafo Único"
                        else:
                            prefix = f"§ {num_display}"
                    elif curr.tipo == TipoElemento.INCISO:
                        prefix = f"Inc. {num_display}"
                    else:
                        prefix = f"{nome} {num_display}"
                    
                    partes.insert(0, prefix)
            
            e.contexto_hierarquico = " > ".join(partes)
            pilha.append(e)

    def criar_chunks(self, texto: str, verbose: bool = False) -> List[Dict]:
        """
        Cria chunks do documento mantendo contexto hierárquico.
        
        Args:
            texto: Texto do documento a ser segmentado
            verbose: Se True, mostra progresso no terminal
            
        Returns:
            Lista de dicionários contendo os chunks e seus metadados
        """
        if verbose:
            print("🔍 Analisando estrutura hierárquica...", end="", flush=True)
        
        elementos = self.parse_documento(texto)
        
        if verbose:
            print(f" ✓ {len(elementos)} elementos identificados")
            print("📦 Gerando chunks: ", end="", flush=True)
        
        # Remove elementos revogados (com marcação no texto)
        elementos = [
            e for e in elementos
            if not self.padroes['revogado'].search(e.texto)
        ]
        
        # Remove parágrafos únicos revogados (lista manual)
        elementos = [
            e for e in elementos
            if not (e.tipo == TipoElemento.PARAGRAFO and 
                   e.numero == "único" and 
                   self.padroes_obj.is_paragrafo_unico_revogado(e.texto))
        ]
        
        chunks = []
        chunk_id = 0
        total_elementos = len(elementos)
        
        for idx, e in enumerate(elementos):
            if verbose and idx % 10 == 0:
                pct = (idx + 1) / total_elementos * 100
                barra = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
                print(f"\r📦 Gerando chunks: [{pct:5.1f}%] {barra} ({idx+1}/{total_elementos})", end="", flush=True)
            
            # Tratamento especial para Anexo IV (linha por linha)
            if ("ANEXO IV" in e.contexto_hierarquico.upper() or
                (e.tipo == TipoElemento.ANEXO and e.numero == "IV")):
                for line in e.texto.split('\n'):
                    if line.strip():
                        chunks.append(
                            self._formatar_chunk(line.strip(), e, chunk_id)
                        )
                        chunk_id += 1
                continue
            
            # Tratamento especial para Anexo III (completo)
            if ("ANEXO III" in e.contexto_hierarquico.upper() or
                (e.tipo == TipoElemento.ANEXO and e.numero == "III")):
                chunks.append(self._formatar_chunk(e.texto, e, chunk_id))
                chunk_id += 1
                continue
            
            # Marcadores estruturais curtos
            if e.tipo in [TipoElemento.TITULO, TipoElemento.CAPITULO,
                         TipoElemento.SECAO, TipoElemento.ANEXO]:
                if len(e.texto) < 500:
                    chunks.append(
                        self._formatar_chunk(
                            f"MARCADOR_ESTRUTURAL: {e.texto}",
                            e,
                            chunk_id
                        )
                    )
                    chunk_id += 1
                    continue
            
            # Chunk normal ou dividido
            if len(e.texto) <= self.tamanho_max_chunk:
                chunks.append(self._formatar_chunk(e.texto, e, chunk_id))
                chunk_id += 1
            else:
                # Divide elemento grande
                for sub_texto in self._dividir_texto(e):
                    chunks.append(
                        self._formatar_chunk(sub_texto, e, chunk_id, parte=True)
                    )
                    chunk_id += 1
        
        if verbose:
            print(f"\r📦 Gerando chunks: [100.0%] ████████████████████ ({total_elementos}/{total_elementos})")
        
        return chunks

    def _formatar_chunk(
        self,
        texto: str,
        elemento: ElementoRegulatorio,
        chunk_id: int,
        parte: bool = False
    ) -> Dict:
        """Formata um chunk com todos os metadados necessários"""
        prefix = ""
        if elemento.contexto_hierarquico:
            prefix = f"[{elemento.contexto_hierarquico}] "
        
        return {
            'chunk_id': f"chunk_{chunk_id}",
            'texto': f"{prefix}{texto}",
            'tipo': elemento.tipo.value,
            'numero': elemento.numero,
            'nivel': elemento.nivel,
            'contexto_hierarquico': elemento.contexto_hierarquico,
            'pagina': elemento.pagina,
            'tamanho': len(texto),
            'parte_de_elemento_maior': parte,
            'semantica': {
                'obrigacoes': self.analisador.identificar_obrigacoes(texto),
                'vedacoes': self.analisador.identificar_vedacoes(texto),
                'referencias': self.analisador.extrair_referencias_cruzadas(texto),
                'valores': self.analisador.extrair_valores_numericos(texto)
            }
        }

    def _dividir_texto(self, elemento: ElementoRegulatorio) -> List[str]:
        """Divide texto grande em partes menores respeitando sentenças"""
        sentencas = re.split(r'(?<=[.;!?])\s+', elemento.texto)
        chunks = []
        atual = ""
        
        for sentenca in sentencas:
            if len(atual) + len(sentenca) > self.tamanho_max_chunk:
                if atual:
                    chunks.append(atual)
                atual = sentenca
            else:
                if atual:
                    atual += ' ' + sentenca
                else:
                    atual = sentenca
        
        if atual:
            chunks.append(atual)
        
        return chunks


# ================================================================================
# MODO LOCAL E TESTES
# ================================================================================

def exportar_txt(chunks: List[Dict], path: str):
    """Exporta chunks para arquivo de texto para inspeção"""
    with open(path, "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE CHUNKS CONSOLIDADO\n")
        f.write("=" * 80 + "\n")
        
        for c in chunks:
            f.write(f"\nCHUNK {c['chunk_id']} | PÁG: {c['pagina']} | TIPO: {c['tipo']}\n")
            f.write(f"CONTEXTO: {c['contexto_hierarquico']}\n")
            f.write("-" * 80 + "\n")
            f.write(f"{c['texto']}\n")


if __name__ == "__main__":
    from extract_from_pdf import extract_text_from_pdf_local
    
    pdf_local = r"c:/Users/rlazaro/Documents/Projetos_AGEMS/agems-rag-api/documentos_para_processar/REN_1000_ANEEL.pdf"
    
    if os.path.exists(pdf_local):
        print("🚀 Processando localmente com PDFPLUMBER...")
        
        # Extrai texto do PDF
        full_text = extract_text_from_pdf_local(pdf_local, verbose=True)
        
        # Salva texto bruto extraído
        raw_output_path = pdf_local.replace(".pdf", "_raw_text_extract.txt")
        with open(raw_output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"📝 Texto bruto extraído salvo em: {raw_output_path}")
        
        # Analisa e gera chunks com animação
        chunker = ChunkerRegulatorio()
        chunks = chunker.criar_chunks(full_text, verbose=True)
        
        print(f"✅ {len(chunks)} chunks gerados com sucesso.")
        
        # Exporta chunks para inspeção
        output_path = pdf_local.replace(".pdf", "_consolidado.txt")
        exportar_txt(chunks, output_path)
        print(f"💾 Relatório consolidado salvo em: {output_path}")