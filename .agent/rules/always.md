---
trigger: always_on
---

Conceito da IA regulatória que deve ser seguido:

Planejamento completo para a construção de um MVP (Minimum Viable Product) de uma IA Regulatória baseada em RAG (Retrieval-Augmented Generation) para a AGEMS (Agência de Regulação de Serviços Públicos de Mato Grosso do Sul). A solução utilizará exclusivamente recursos gratuitos da plataforma Cloudflare, incluindo Workers AI, Vectorize, D1 Database e R2 Storage, permitindo a criação de uma ferramenta poderosa sem custos operacionais iniciais.

A IA será treinada com documentos regulatórios dos setores de Gás e Energia, oferecendo respostas contextualizadas e fundamentadas em legislação e normas técnicas. O sistema manterá histórico de conversas e será acessível via API REST, permitindo integração com outros sistemas da AGEMS.

Atualização importante: Este plano foi adaptado para utilizar Python como linguagem de desenvolvimento, aproveitando o suporte nativo e otimizado da Cloudflare para Python Workers, que oferece cold starts 2.4x mais rápidos que AWS Lambda.

2. Arquitetura Técnica

2.1 Visão Geral

A arquitetura proposta utiliza uma abordagem serverless completa, aproveitando a infraestrutura global da Cloudflare. Todos os componentes são nativamente integrados, eliminando complexidades de configuração e garantindo baixa latência através da execução na edge network.

2.2 Componentes da Arquitetura

2.2.1 Cloudflare Workers (Runtime)

Os Cloudflare Workers são o coração da aplicação, executando o código da API em um ambiente V8 Isolates extremamente rápido. Diferentemente de containers tradicionais, os Workers têm cold start inferior a 10 milissegundos e escalam automaticamente para milhões de requisições sem configuração adicional. O plano gratuito oferece 100.000 requisições por dia, mais que suficiente para um MVP com dezenas de usuários.

2.2.2 Python Workers Framework

Python Workers é o suporte nativo da Cloudflare para desenvolvimento de Workers em Python, lançado recentemente com melhorias significativas. A Cloudflare oferece cold starts 2.4x mais rápidos que AWS Lambda e 3x mais rápidos que Google Cloud Functions, tornando Python uma escolha viável para aplicações serverless de alta performance.

Características do Python Workers:

•
Sintaxe Python Nativa: Desenvolvimento em Python puro, sem necessidade de aprender JavaScript/TypeScript

•
Acesso aos Bindings: Integração nativa com Workers AI, Vectorize, D1, R2 através do objeto env

•
Bibliotecas Populares: Suporte a pacotes essenciais como PyPDF2, requests, json, entre outros

•
Gerenciamento de Dependências: Integração com uv para instalação rápida de pacotes

•
API Familiar: Estrutura de código similar ao FastAPI, facilitando a transição

A escolha do Python Workers permite que a equipe da AGEMS desenvolva em uma linguagem familiar, mantendo todos os benefícios da infraestrutura serverless da Cloudflare.

2.2.3 Workers AI (Inferência de Modelos)

Workers AI é a plataforma de inferência serverless da Cloudflare, oferecendo acesso a mais de 50 modelos de IA opensource. O plano gratuito inclui 10.000 neurons por dia, suficiente para aproximadamente 100-200 consultas completas (embedding + geração de resposta). Os modelos são executados em GPUs da Cloudflare, garantindo baixa latência e alta disponibilidade.

Modelos Selecionados:

•
LLM Principal: @cf/meta/llama-3.1-8b-instruct-fast

•
Modelo de 8 bilhões de parâmetros da Meta, otimizado para velocidade

•
Multilingual, com excelente suporte ao português

•
Otimizado para diálogo e seguimento de instruções

•
Rate limit: 300 requisições por minuto



•
Modelo de Embeddings: @cf/qwen/qwen3-embedding-0.6b

•
Modelo compacto de 600 milhões de parâmetros

•
Gera vetores de 768 dimensões

•
Otimizado para tarefas de busca e ranking semântico

•
Rate limit: 3.000 requisições por minuto



2.2.4 Vectorize (Banco de Dados Vetorial)

Vectorize é o banco de dados vetorial distribuído da Cloudflare, projetado para armazenar e consultar embeddings com alta performance. O plano gratuito oferece 100 índices e 30 milhões de dimensões consultadas por mês. Considerando embeddings de 768 dimensões e busca de top-5 chunks por consulta, isso permite aproximadamente 7.800 consultas mensais, ou cerca de 260 por dia.

O Vectorize utiliza busca por similaridade de cosseno para encontrar os chunks de texto mais relevantes para cada pergunta, formando a base do sistema RAG.

2.2.5 D1 Database (Banco SQL Serverless)

D1 é o banco de dados SQL serverless da Cloudflare, baseado em SQLite. O plano gratuito oferece 5 bancos de dados, 5 GB de armazenamento total, 5 milhões de linhas lidas por dia, e 100.000 linhas escritas por dia. Esses limites são mais que adequados para armazenar metadados de documentos e histórico completo de conversas.

O D1 será usado para três propósitos principais: armazenar metadados dos documentos regulatórios (título, tipo, setor, data, status de processamento), manter o histórico completo de conversas (perguntas, respostas, chunks usados, timestamps), e gerenciar sessões de usuários para conversas contextuais.

2.2.6 R2 Object Storage

R2 é o serviço de armazenamento de objetos da Cloudflare, compatível com a API S3 da AWS, mas sem taxas de egresso. O plano gratuito oferece 10 GB de armazenamento, 1 milhão de operações de escrita por mês, e 10 milhões de operações de leitura por mês. O R2 armazenará os documentos regulatórios originais (PDFs, DOCs), permitindo que sejam recuperados quando necessário.

2.3 Fluxo de Dados

2.3.1 Ingestão de Documentos

O processo de ingestão transforma documentos regulatórios em conhecimento pesquisável pela IA. O administrador faz upload de um documento (PDF, DOCX) através do endpoint POST /documents/upload. O Worker salva o arquivo original no R2 Storage e registra os metadados no D1 com status "pending". Um Worker de processamento é acionado (pode ser um trigger do R2 ou uma chamada manual), que extrai o texto do documento usando a biblioteca PyPDF2.

O texto é então dividido em chunks semânticos de aproximadamente 512-1024 tokens, mantendo coerência e contexto. Para cada chunk, o Worker gera um embedding vetorial usando o modelo Qwen3 Embedding e insere o vetor no Vectorize junto com metadados (ID do documento, índice do chunk, título, seção, tipo, setor). Finalmente, o Worker atualiza o status do documento no D1 para "processed" e registra o número total de chunks gerados.

2.3.2 Consulta RAG (Retrieval-Augmented Generation)

O fluxo de consulta é o coração do sistema RAG. O usuário envia uma pergunta através do endpoint POST /chat/query, incluindo a query e opcionalmente um session_id. O Worker gera um embedding da pergunta usando o mesmo modelo Qwen3 Embedding. O Vectorize realiza uma busca por similaridade de cosseno, retornando os top-5 chunks mais relevantes.

Se um session_id foi fornecido, o Worker recupera as últimas 5-10 mensagens da sessão do D1 para manter contexto conversacional. O Worker então constrói um prompt estruturado contendo instruções de sistema ("Você é um assistente especializado em regulação de Gás e Energia de MS"), o contexto recuperado (os 5 chunks relevantes), o histórico da conversa (se houver), e a pergunta do usuário.

O prompt é enviado ao Llama 3.1 8B via Workers AI, que gera uma resposta fundamentada no contexto fornecido. A resposta é retornada ao usuário junto com as fontes (metadados dos chunks usados), permitindo verificação. A interação completa (pergunta, resposta, chunks usados, modelo usado, tokens consumidos, timestamp) é salva no D1 para análise posterior.

