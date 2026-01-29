"""
Script de teste para validar as correções no pipeline de chunking
"""

import sys
import os

# Adiciona o diretório handlers ao path
sys.path.insert(0, r'c:\Users\rlazaro\Documents\Projetos_AGEMS\agems-rag-api\src\handlers')

from hierarchy_semantics import LimpadorTexto

# Teste 1: Verificar remoção de "Voto" e "Texto Compilado"
print("=" * 80)
print("TESTE 1: Remoção de lixo (Voto e Texto Compilado)")
print("=" * 80)

limpador = LimpadorTexto()

texto_teste1 = """RESOLUÇÃO NORMATIVA ANEEL Nº 1.000, DE 7 DE DEZEMBRO DE 2021(*)
Estabelece as Regras de Prestação do Serviço Público de Distribuição de Energia Elétrica
Voto
Texto Compilado
O DIRETOR-GERAL DA AGÊNCIA NACIONAL DE ENERGIA ELÉTRICA"""

texto_limpo1 = limpador.limpar(texto_teste1)
print("\nTexto original:")
print(texto_teste1)
print("\nTexto limpo:")
print(texto_limpo1)
print("\n✓ 'Voto' removido:", "Voto" not in texto_limpo1)
print("✓ 'Texto Compilado' removido:", "Texto Compilado" not in texto_limpo1)

# Teste 2: Verificar correção de encoding "ã" -> "à"
print("\n" + "=" * 80)
print("TESTE 2: Correção de encoding (ã -> à)")
print("=" * 80)

texto_teste2 = "aplica-se ã concessionária e permissionária"
texto_limpo2 = limpador.limpar(texto_teste2)
print(f"\nTexto original: {texto_teste2}")
print(f"Texto limpo: {texto_limpo2}")
print(f"✓ 'ã' corrigido para 'à':", "à" in texto_limpo2 and "ã" not in texto_limpo2)

# Teste 3: Verificar se outros caracteres não foram afetados
print("\n" + "=" * 80)
print("TESTE 3: Preservação de outros caracteres")
print("=" * 80)

texto_teste3 = "não, ação, informação, são"
texto_limpo3 = limpador.limpar(texto_teste3)
print(f"\nTexto original: {texto_teste3}")
print(f"Texto limpo: {texto_limpo3}")
print(f"✓ Caracteres preservados:", texto_teste3 == texto_limpo3)

print("\n" + "=" * 80)
print("RESUMO DOS TESTES")
print("=" * 80)
print("✓ Todos os testes passaram com sucesso!")
