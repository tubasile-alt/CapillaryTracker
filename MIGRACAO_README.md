# Manual de Migrações do Banco de Dados

Este documento explica como gerenciar o banco de dados PostgreSQL e o sistema de migrações para o sistema de gestão de cirurgias capilares.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [Comandos Comuns](#comandos-comuns)
4. [Procedimentos de Reset](#procedimentos-de-reset)
5. [Solução de Problemas](#solução-de-problemas)
6. [Fluxo de Trabalho Recomendado](#fluxo-de-trabalho-recomendado)

## 🔎 Visão Geral

O sistema utiliza um banco de dados PostgreSQL com Flask-SQLAlchemy e Flask-Migrate (Alembic) para gerenciar migrações. Devido à integração com o Flask-MonitoringDashboard, foram criados scripts específicos para contornar problemas de importação circular durante o processo de migração.

### Tabelas Principais:
- `surgery`: Armazena dados das cirurgias
- `unit_progress`: Armazena metas por unidade
- Tabelas do Flask-MonitoringDashboard

## 📁 Estrutura de Arquivos

### Scripts de Migração e Manutenção:
- `reset_migrations.py`: Reset completo do sistema de migrações
- `resetdb.py`: Interface para o usuário resetar o banco de dados com backup
- `drop_tables.py`: Remover todas as tabelas do banco
- `create_migration.py`: Criar migrações contornando problemas de importação circular
- `force_initial_migration.py`: Forçar criação de migração inicial quando Alembic não detecta alterações
- `check_migrations.py`: Verificar estado das migrações
- `test_migration.py`: Testar criação de migração

### Arquivos Relacionados:
- `migrations/`: Diretório com arquivos de migração do Alembic
- `migrations/versions/`: Arquivos de migração individual
- `migrations/env.py`: Configuração do ambiente de migração
- `logs/migration_check_*.log`: Logs de verificação de migrações

## 🛠️ Comandos Comuns

### Verificar Estado das Migrações
```bash
python check_migrations.py
```

### Criar Nova Migração (quando houver alterações no modelo)
```bash
python create_migration.py
```

### Aplicar Migrações Pendentes
```bash
flask db upgrade
```

### Exibir Versão Atual da Migração
```bash
flask db current
```

## 🔄 Procedimentos de Reset

### Reset Completo do Banco de Dados (Com Backup Automático)
Este procedimento irá:
1. Fazer backup dos dados existentes
2. Remover todas as tabelas
3. Reinicializar o sistema de migrações
4. Criar e aplicar migração inicial

```bash
python resetdb.py
```

### Reset Somente das Migrações (Mantém Tabelas)
```bash
python reset_migrations.py
```

### Forçar Criação de Migração Inicial
Útil quando o Alembic não detecta alterações no esquema:
```bash
python force_initial_migration.py
```

## ⚠️ Solução de Problemas

### Problema: Alembic não detecta alterações no esquema
**Solução**: Use `force_initial_migration.py` para criar manualmente uma migração inicial.

### Problema: Erro de importação circular com Flask-MonitoringDashboard
**Solução**: Use `create_migration.py` que cria uma aplicação Flask isolada apenas para migrações.

### Problema: Tabela alembic_version desatualizada ou corrompida
**Solução**: Execute `reset_migrations.py` para reconstruir a tabela alembic_version.

### Problema: Dados perdidos após migração
**Solução**: Restaure o backup criado durante o processo de reset em `data_backup/`.

## 🔄 Fluxo de Trabalho Recomendado

### Para Alterações de Esquema:

1. **Faça backup dos dados**:
   ```bash
   python -c "from app import backup_excel_file; backup_excel_file('cirurgias.xlsx')"
   ```

2. **Verifique o estado atual**:
   ```bash
   python check_migrations.py
   ```

3. **Faça alterações nos modelos**:
   Edite app.py para adicionar/modificar definições de modelo

4. **Crie uma nova migração**:
   ```bash
   python create_migration.py
   ```

5. **Verifique e aplique a migração**:
   ```bash
   flask db upgrade
   ```

### Para Reset Completo:

1. **Execute o script resetdb.py**:
   ```bash
   python resetdb.py
   ```

2. **Confirme digitando "RESET"** quando solicitado

3. **Verifique se o reset foi bem-sucedido**:
   ```bash
   python check_migrations.py
   ```