# Como Obter Credenciais da Cloudflare

## 1. CLOUDFLARE_ACCOUNT_ID

1. Acesse: https://dash.cloudflare.com/
2. Faça login na sua conta
3. No menu lateral esquerdo, clique em "Workers & Pages"
4. O Account ID aparecerá no canto direito da página
5. Copie o ID (formato: 92f68f3c9c9a16e73e85032d64303ddc)

## 2. CLOUDFLARE_API_TOKEN

### Opção A: Criar um Token Personalizado (Recomendado)

1. Acesse: https://dash.cloudflare.com/profile/api-tokens
2. Clique em "Create Token"
3. Clique em "Create Custom Token"
4. Configure:
   - **Token name**: "AGEMS RAG API - Workers AI"
   - **Permissions**: 
     - Account > Workers AI > Read
   - **Account Resources**: 
     - Include > Sua conta
5. Clique em "Continue to summary"
6. Clique em "Create Token"
7. **IMPORTANTE**: Copie o token AGORA (você não poderá vê-lo novamente!)

### Opção B: Usar API Key Global (Menos Seguro)

1. Acesse: https://dash.cloudflare.com/profile/api-tokens
2. Role até "API Keys"
3. Em "Global API Key", clique em "View"
4. Digite sua senha
5. Copie a chave

## 3. Configurar o Arquivo .env

1. Na raiz do projeto, crie um arquivo chamado `.env` (sem extensão)
2. Cole o seguinte conteúdo, substituindo pelos seus valores:

```
CLOUDFLARE_ACCOUNT_ID=seu_account_id_aqui
CLOUDFLARE_API_TOKEN=seu_token_aqui
```

3. Salve o arquivo

## 4. Testar

Execute o ingest.py novamente:

```bash
py ingest.py
```

Se as credenciais estiverem corretas, você verá:
```
-> Gerando 689 embeddings via Cloudflare AI API...
```

Se houver erro, você verá:
```
ERRO: Credenciais da Cloudflare não encontradas!
Usando vetores aleatórios como fallback...
```

## Notas Importantes

- ⚠️ **NUNCA** faça commit do arquivo `.env` no Git!
- ✅ O arquivo `.env` já está no `.gitignore`
- 🔒 Mantenha suas credenciais em segredo
- 📊 Rate Limit: 300 requisições/minuto (o script já respeita isso)
