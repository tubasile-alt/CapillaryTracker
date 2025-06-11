# Guia de Configuração do Dropbox - Passo a Passo

## Problema Atual
O token está sendo truncado (apenas 15 caracteres). Tokens válidos do Dropbox têm mais de 1000 caracteres.

## Solução Completa

### 1. Configurar Aplicação no Dropbox

1. Acesse: https://www.dropbox.com/developers/apps
2. Clique em "Create app"
3. Selecione:
   - **API**: Dropbox API
   - **Type of access**: App folder
   - **Name**: replit-relatorio-cirurgia (ou outro nome único)
4. Clique em "Create app"

### 2. Configurar Permissões

Na página da sua aplicação:
1. Vá na aba **"Permissions"**
2. Marque as seguintes opções:
   - ✅ files.metadata.write
   - ✅ files.content.write
   - ✅ files.content.read
   - ✅ files.metadata.read
3. Clique em **"Submit"** para salvar

### 3. Gerar Token de Acesso

1. Vá na aba **"Settings"**
2. Role até a seção **"OAuth 2"**
3. Clique em **"Generate access token"**
4. **IMPORTANTE**: Copie o token COMPLETO (deve ter mais de 1000 caracteres)

### 4. Configurar no Replit

1. No Replit, clique no ícone do **cadeado** (Secrets)
2. Se já existe `DROPBOX_ACCESS_TOKEN`, clique em **"Edit"**
3. Se não existe, clique em **"New Secret"**
4. Configure:
   - **Key**: `DROPBOX_ACCESS_TOKEN`
   - **Value**: Cole o token COMPLETO (não truncado)
5. Clique em **"Add secret"** ou **"Save"**

### 5. Verificar Token

O token correto deve:
- Começar com `sl.` 
- Ter mais de 1000 caracteres
- Conter letras, números, pontos, hífens e underscores

### 6. Testar

Após configurar:
1. Reinicie o servidor Flask
2. Acesse `/test_backup` para verificar

## Diagnóstico de Problemas

- **Token truncado (15 chars)**: Reconfigurar no Replit
- **"Token expirado"**: Gerar novo token no Dropbox
- **"Permissões insuficientes"**: Verificar permissões na aplicação
- **"Token inválido"**: Verificar se copiou o token completo