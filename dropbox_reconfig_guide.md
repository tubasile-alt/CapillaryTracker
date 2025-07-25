# 🔧 GUIA COMPLETO: Reconfigurar Token Dropbox

## Passo 1: Acessar Console do Dropbox

1. Vá para: https://www.dropbox.com/developers/apps
2. Faça login na sua conta Dropbox
3. Você verá a lista de aplicações existentes

## Passo 2: Encontrar sua Aplicação

- Procure por uma aplicação com nome similar a:
  - "replit-relatorio-cirurgia"
  - "Hair Surgery Backup"
  - Ou qualquer app que você criou anteriormente
- Se não existir, clique em "Create app" para criar uma nova

## Passo 3: Criar Nova Aplicação (se necessário)

Se precisar criar nova aplicação:

1. **App type**: Escolha "Scoped access"
2. **Access type**: Escolha "App folder" (acesso limitado)
3. **Name**: Use "replit-hair-surgery-backup" (ou similar)
4. Clique "Create app"

## Passo 4: Configurar Permissões

Na aba **"Permissions"** da sua aplicação:

Marque as seguintes permissões:
- ✅ `files.metadata.read`
- ✅ `files.metadata.write` 
- ✅ `files.content.read`
- ✅ `files.content.write`

Clique "Submit" para salvar as permissões.

## Passo 5: Gerar Novo Token

Na aba **"Settings"**:

1. Role até a seção "OAuth 2"
2. Em "Generated access token", clique "Generate"
3. **IMPORTANTE**: Copie o token COMPLETO que aparece
   - Ele começa com "sl." 
   - É uma string longa (~1300 caracteres)
   - Copie tudo até o final

## Passo 6: Configurar no Replit

1. No Replit, clique no ícone de cadeado (🔒) no painel lateral
2. Procure por "DROPBOX_ACCESS_TOKEN"
3. **Se existir**: Clique para editar
4. **Se não existir**: Clique "+ New secret"
5. **Key**: `DROPBOX_ACCESS_TOKEN`
6. **Value**: Cole o token completo que você copiou
7. Clique "Save"

## Passo 7: Reiniciar o Servidor

No Replit:
1. Pare o servidor atual (se estiver rodando)
2. Reinicie clicando no botão "Run" novamente
3. Aguarde o servidor inicializar

## Passo 8: Testar a Configuração

Execute um dos comandos:

### Opção A: Via navegador
Acesse: `https://seu-replit.replit.app/test_backup`

### Opção B: Via script
```bash
python test_backup_system.py
```

## ✅ Verificação de Sucesso

Você verá mensagens como:
- ✅ "Token configurado"
- ✅ "Conexão Dropbox OK"
- ✅ "Backup realizado com sucesso"

## ❌ Possíveis Problemas

### Token inválido
- Verifique se copiou o token completo
- Certifique-se de que não há espaços extras
- Regere o token se necessário

### Permissões insuficientes
- Volte nas configurações da app
- Confirme todas as permissões marcadas
- Clique "Submit" novamente

### App não encontrada
- Crie uma nova aplicação
- Siga todos os passos de configuração

## 📱 Importante

- O token não expira automaticamente
- Mas pode ser revogado se você recriar a aplicação
- Mantenha as permissões sempre configuradas
- O backup local continuará funcionando independentemente do Dropbox

## 🔄 Backup Automático

Após configurar corretamente:
- Todo registro de necrose criará backup automático
- Arquivo será salvo na pasta raiz da aplicação Dropbox
- Formato: `backup_automatico_YYYYMMDD_HHMMSS.xlsx`
- Contém planilhas separadas para cirurgias e necroses