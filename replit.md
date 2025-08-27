# Replit.md - Hair Surgery Management System

## Overview

This is a comprehensive hair surgery management system for Instituto Capilar do Brasil (ICB). The system tracks surgical procedures, patient data, medical teams, and generates detailed reports and dashboards. It's built with Flask and PostgreSQL, featuring both a web interface and a Tkinter desktop application for data entry.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL hosted on Neon (cloud database)
- **Migration System**: Flask-Migrate with Alembic
- **Monitoring**: Flask-MonitoringDashboard for system metrics
- **Authentication**: Simple password-based admin authentication

### Frontend Architecture
- **Web Interface**: Flask templates with Jinja2
- **Desktop Application**: Tkinter-based form application (main.py)
- **Styling**: Custom CSS with responsive design
- **JavaScript**: Dynamic form interactions and chart visualizations

### Data Storage
- **Primary Database**: PostgreSQL with two main tables:
  - `surgery`: Patient surgery records
  - `unit_progress`: Goal tracking per medical unit
- **File Storage**: Excel files for data backup and import/export
- **Cloud Backup**: Automated Dropbox integration for data backup

## Key Components

### 1. Database Models
- **Surgery Model**: Comprehensive patient surgery data including demographics, procedure details, follicle counts, and medical team information
- **UnitProgress Model**: Tracks performance goals for each medical unit

### 2. Web Application Routes
- **Main Routes** (app.py): Patient registration, dashboard, data visualization
- **Admin Routes** (admin_routes.py): Medical staff and team management
- **Authentication**: Separate login systems for general users and medical staff

### 3. Desktop Application
- **Tkinter Interface** (main.py): Offline data entry form with validation
- **Multi-page Form**: Paginated interface for comprehensive data collection
- **Data Sync**: Integrates with web application database

### 4. Data Management
- **Import/Export**: Excel file handling for data migration
- **Backup System**: Automated Dropbox backup with versioning
- **Migration Scripts**: Database schema management and data restoration

## Data Flow

1. **Data Entry**: Users can input data via web form or desktop application
2. **Validation**: Form validation ensures data integrity before database storage
3. **Storage**: Data is stored in PostgreSQL with automatic backup triggers
4. **Visualization**: Dashboard provides real-time analytics and reporting
5. **Backup**: Automated backup to Dropbox maintains data safety
6. **Export**: Excel export functionality for reporting and data sharing

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and connection management
- **Pandas**: Data manipulation and Excel file handling
- **Psycopg2**: PostgreSQL database adapter
- **Tkinter**: Desktop GUI framework (built-in Python)

### Additional Services
- **Dropbox API**: Cloud backup integration
- **Neon PostgreSQL**: Cloud database hosting
- **Chart.js**: Web-based data visualization
- **FuzzyWuzzy**: Name matching for duplicate detection

### Development Tools
- **Flask-Migrate**: Database migration management
- **Flask-MonitoringDashboard**: Application performance monitoring
- **Openpyxl**: Excel file processing

## Deployment Strategy

### Environment Configuration
- **Database**: Cloud-hosted PostgreSQL on Neon platform
- **Secrets Management**: Environment variables for sensitive data (tokens, passwords)
- **Static Assets**: Served directly by Flask in development

### Migration Strategy
- **Database Migrations**: Managed through Flask-Migrate with custom scripts
- **Data Restoration**: Automated deployment data restoration from Excel backups
- **Version Control**: Git-based deployment with automated setup scripts

### Backup Strategy
- **Local Backups**: Excel file exports stored in data_backup directory
- **Cloud Backups**: Automated Dropbox sync with timestamped versions
- **Database Dumps**: Migration scripts for complete database restoration

## Changelog

```
Changelog:
- August 27, 2025. CORREÇÕES CRÍTICAS DE FEEDBACK E PERSISTÊNCIA:
  - CORRIGIDO: Erro internal server error na página de resumo do paciente após cadastramento
  - MELHORADO: Sistema de feedback visual para todas as operações administrativas (adicionar/remover médicos, técnicos, unidades)
  - IMPLEMENTADO: Indicadores visuais em tempo real durante salvamento ("💾 Salvando...")
  - IMPLEMENTADO: Auto-ocultamento de mensagens de feedback após 8 segundos
  - IMPLEMENTADO: Proteção robusta contra falhas na página de resumo - SEMPRE mostra resumo mesmo com erros
  - IMPLEMENTADO: Desabilitação de botões durante salvamento para evitar duplos cliques
  - GARANTIDO: Todas as operações administrativas agora mostram mensagem clara de sucesso/falha
  - GARANTIDO: Dados administrativos são persistidos de forma segura e verificada
- August 26, 2025. RESOLUÇÃO CRÍTICA: Implementado sistema robusto de persistência administrativa:
  - Criado sistema de logs detalhados com IDs únicos para rastrear cada operação de salvamento
  - Implementado backup automático com timestamp para todas as mudanças administrativas
  - Adicionado verificação de integridade de arquivos antes e depois de cada salvamento
  - Criado sistema de monitoramento em tempo real (/admin/health_check) para detectar problemas
  - Implementado tratamento de erro robusto com fallback automático para backups
  - Adicionado endpoint de monitoramento (/admin/monitor_changes) para verificar sincronização
  - Sistema de teste automático para validar persistência de dados administrativos
  - Melhoradas mensagens de erro com feedback específico sobre o estado do salvamento
  - Garantia de que mudanças em equipes, médicos e unidades sejam SEMPRE salvas permanentemente
- August 18, 2025. Implemented automatic team synchronization for Uberlândia unit:
  - Created sync_uberlandia_teams() function to automatically combine teams from São Paulo, Goiânia, Ribeirão Preto, and Brasília
  - Any changes to team members in source units automatically updates Uberlândia
  - Uberlândia now maintains 23 combined team members from all source units
  - Added extra_person_1 and extra_person_2 database columns for Técnica Extra fields
  - Implemented /get_all_team_members API endpoint to populate Técnica Extra dropdowns with all 36 team members
  - Fixed internal server errors and added HTML form fields for Técnica Extra functionality
- August 14, 2025. Major database cleanup and surgery control system improvements:
  - Implemented comprehensive equipe field cleanup across all medical units
  - Removed 800+ duplicate entries from surgery records database
  - Created specialized surgery control dashboard with authentication (password: icb@)
  - Added individual performance tracking for Ribeirão Preto team members:
    • Aline: 119 surgeries, Ana: 84 surgeries, Natália: 72 surgeries, Lavínia: 40 surgeries
  - Simplified control dashboard to focus on surgeries by unit with filtering
  - Resolved data integrity issues affecting São Paulo (283 remaining), Campinas (83), Brasília (20)
  - Complete data cleanup for Recife, Ribeirão Preto, and Rio de Janeiro units
- July 16, 2025. Fixed administration system persistence issues:
  - Replaced hardcoded constants with dynamic JSON configuration loading
  - Implemented reload_admin_config() function for real-time updates
  - Added automatic configuration reloading after admin changes
  - Enhanced admin interface with automatic refresh after modifications
  - Created test script (test_admin.py) for troubleshooting admin functionality
  - Units, doctors, and teams now properly persist across page refreshes
- June 30, 2025. Implemented real-time search suggestion filtering with:
  - Intelligent local caching for fast filtering
  - Keyboard navigation (arrow keys, enter, escape)
  - Visual highlighting of search terms
  - Enhanced UI with patient details and icons
  - Debounced server requests for performance
  - Smart search across name, doctor, and date fields
- June 24, 2025. Initial setup
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```