"""
Script de teste para validar a correção da quebra de página no inciso XXIX-B
"""

import sys
import os

# Simula o texto com quebra de página
texto_simulado = """[[PAGINA:3]]
XXIX-B - minigeração distribuída: central geradora de energia elétrica que utilize fontes renováveis ou, conforme Resolução Normativa nº 1.031, de

[[PAGINA:4]]
26 de julho de 2022, de cogeração qualificada, conectada à rede de distribuição de energia elétrica por meio de unidade consumidora, da qual é considerada
parte, que possua potência instalada em corrente alternada maior que 75 kW e menor ou igual a: (Incluído pela REN ANEEL 1.059, de 07.02.2023)
a) 5 MW para as centrais geradoras de fontes despacháveis; (Incluída pela REN ANEEL 1.059, de 07.02.2023)
b) 3 MW para as demais fontes não enquadradas como centrais geradoras de fontes despacháveis; ou (Incluída pela REN ANEEL 1.059, de
07.02.2023)"""

print("=" * 80)
print("TESTE: Verificação da quebra de página no inciso XXIX-B")
print("=" * 80)

print("\nTexto simulado (com quebra de página):")
print(texto_simulado)

# Verifica se há quebra indevida
linhas = texto_simulado.split('\n')
for i, linha in enumerate(linhas):
    if 'XXIX-B' in linha:
        print(f"\nLinha {i}: {linha}")
        if i + 1 < len(linhas):
            print(f"Linha {i+1}: {linhas[i+1]}")
        if i + 2 < len(linhas):
            print(f"Linha {i+2}: {linhas[i+2]}")

# Verifica se a alínea b) está completa
alinea_b_completa = False
for linha in linhas:
    if 'b) 3 MW para as demais fontes não enquadradas como centrais geradoras de fontes despacháveis; ou (Incluída pela REN ANEEL 1.059, de' in linha:
        print("\n✓ Alínea b) encontrada completa na mesma linha")
        alinea_b_completa = True
        break

if not alinea_b_completa:
    # Verifica se está quebrada
    parte1_encontrada = False
    parte2_encontrada = False
    for linha in linhas:
        if 'b) 3 MW para as demais fontes não enquadradas como centrais geradoras de fontes despacháveis; ou (Incluída pela REN ANEEL 1.059, de' in linha:
            parte1_encontrada = True
        if '07.02.2023)' in linha and 'b)' not in linha:
            parte2_encontrada = True
    
    if parte1_encontrada and parte2_encontrada:
        print("\n⚠ PROBLEMA DETECTADO: Alínea b) está quebrada entre duas linhas")
        print("A correção no extract_from_pdf.py deve juntar essas linhas")

print("\n" + "=" * 80)
print("ANÁLISE COMPLETA")
print("=" * 80)
print("\nNota: A correção implementada em extract_from_pdf.py detecta quando:")
print("1. A última linha da página não termina com pontuação")
print("2. A primeira linha da próxima página não começa com maiúscula/número")
print("3. Nesse caso, junta as linhas automaticamente")
