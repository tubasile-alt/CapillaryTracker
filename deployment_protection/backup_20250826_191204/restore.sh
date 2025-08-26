#!/bin/bash
# Script de restauração automática
# Criado em: 2025-08-26T19:12:07.095554

echo "🔄 Restaurando dados após deployment..."

# Restaurar arquivos de configuração
cp deployment_protection/backup_20250826_191204/admin_config.json .
cp deployment_protection/backup_20250826_191204/admin_config_backup.json .
cp deployment_protection/backup_20250826_191204/admin_config_safe_backup.json .

# Restaurar arquivos Excel


# Restaurar banco de dados (se necessário)
if [ -f "deployment_protection/backup_20250826_191204/database_backup.sql" ] && [ ! -z "$DATABASE_URL" ]; then
    echo "Restaurando banco de dados..."
    psql "$DATABASE_URL" < deployment_protection/backup_20250826_191204/database_backup.sql
fi

echo "✅ Restauração concluída!"
