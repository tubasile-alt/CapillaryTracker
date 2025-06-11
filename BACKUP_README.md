# Sistema de Backup Automático para Dropbox

## Visão Geral

O sistema CapillaryTracker agora inclui backup automático para o Dropbox que:
- Exporta todos os dados do banco para um arquivo Excel (.xlsx)
- Faz upload automático para sua conta Dropbox
- Executa sempre que novos dados são inseridos
- Mantém duas versões: uma com timestamp e outra "latest"

## Configuração Inicial

### 1. Criar Aplicação no Dropbox

1. Acesse [Dropbox Developers](https://www.dropbox.com/developers/apps)
2. Clique em "Create app"
3. Escolha "Scoped access"
4. Escolha "App folder" (acesso limitado à pasta da aplicação)
5. Nome sugerido: `replit-relatorio-cirurgia`

### 2. Configurar Permissões

Na aba "Permissions", marque:
- `files.metadata.write`
- `files.content.write` 
- `files.content.read`

### 3. Gerar Token de Acesso

1. Na aba "Settings", role até "OAuth 2"
2. Clique em "Generate access token"
3. Copie o token gerado (importante: salve-o em local seguro)

### 4. Configurar no Replit

1. No Replit, clique no ícone de cadeado (Secrets)
2. Adicione uma nova secret:
   - **Key:** `DROPBOX_ACCESS_TOKEN`
   - **Value:** cole o token que você copiou

## Como Funciona

### Backup Automático
- Executado automaticamente sempre que dados são salvos no sistema
- Não interfere no processo normal de salvamento
- Se falhar, não afeta o funcionamento do app

### Arquivos Criados no Dropbox
1. `relatorio_cirurgias_backup_YYYYMMDD_HHMMSS.xlsx` - Versão com timestamp
2. `relatorio_cirurgias_latest.xlsx` - Sempre a versão mais recente

### Dados Incluídos no Backup
- Dados básicos da cirurgia (data, nome, unidade, médico, equipe)
- Informações detalhadas (folículos, densidade, quadrantes)
- Dados de extração e técnicas
- Informações sobre pelos corporais
- Timestamps de criação

## Testando o Sistema

### Teste Manual
Acesse a rota de teste: `https://seu-app.replit.app/test_backup`

### Teste via Script
Execute o script de configuração:
```bash
python dropbox_config.py
```

### Verificar Logs
Os logs mostrarão:
- Conexão com Dropbox
- Criação do arquivo Excel
- Status do upload
- Possíveis erros

## Estrutura dos Arquivos

### Formato Excel
- **Planilha:** "Cirurgias"
- **Campos:** Todos os campos do banco de dados
- **Formato de Data:** DD/MM/YYYY
- **Codificação:** UTF-8

### Localização no Dropbox
- Pasta raiz da aplicação
- Acesso via Dropbox web ou aplicativo
- Sincronização automática se configurada

## Solução de Problemas

### Token Inválido ou Expirado
- Gere um novo token na aplicação Dropbox
- Atualize a secret `DROPBOX_ACCESS_TOKEN` no Replit

### Erro de Permissões
- Verifique as permissões na aplicação Dropbox
- Certifique-se de que `files.content.write` está marcado

### Falha na Conexão
- Verifique sua conexão com internet
- Confirme se o token está correto
- Execute o teste manual: `/test_backup`

### Arquivo Não Aparece no Dropbox
- Aguarde alguns minutos para sincronização
- Verifique se está na pasta correta da aplicação
- Confirme se não há erro nos logs

## Logs e Monitoramento

### Logs de Sucesso
```
✅ Backup realizado com sucesso no Dropbox: relatorio_cirurgias_backup_20250611_141530.xlsx
```

### Logs de Erro
```
⚠️ DROPBOX_ACCESS_TOKEN não configurado - backup desabilitado
❌ Erro no backup para Dropbox: [detalhes do erro]
```

## Segurança

- Token de acesso armazenado como secret no Replit
- Acesso limitado apenas à pasta da aplicação
- Dados criptografados em trânsito (HTTPS)
- Backup não interfere no funcionamento principal

## Manutenção

### Rotação de Tokens
- Tokens do Dropbox não expiram automaticamente
- Recomendado renovar periodicamente por segurança
- Processo: gerar novo token → atualizar secret

### Limpeza de Arquivos
- Arquivos antigos ficam acumulados no Dropbox
- Considere limpeza manual periódica
- Mantenha sempre a versão "latest"

## Suporte

Para problemas específicos:
1. Verifique os logs do aplicativo
2. Execute o teste manual
3. Confirme a configuração das secrets
4. Valide as permissões da aplicação Dropbox