
import os
import shutil
import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_checkpoint():
    # Obter data e hora atual para nome do checkpoint
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_dir = f"checkpoints/checkpoint_{timestamp}"
    
    # Criar diretório de checkpoint se não existir
    os.makedirs(checkpoint_dir, exist_ok=True)
    os.makedirs(os.path.join(checkpoint_dir, "templates"), exist_ok=True)
    os.makedirs(os.path.join(checkpoint_dir, "static"), exist_ok=True)
    
    # Lista de arquivos principais para backup
    main_files = [
        "app.py", 
        "main.py", 
        "utils.py", 
        "cirurgias.xlsx", 
        "necroses.xlsx",
        "import_data.py",
        "import_attached_data.py"
    ]
    
    # Copiar arquivos principais
    for file in main_files:
        if os.path.exists(file):
            shutil.copy2(file, checkpoint_dir)
            logger.info(f"✅ Arquivo {file} copiado para o checkpoint")
    
    # Copiar templates
    template_files = os.listdir("templates")
    for file in template_files:
        if file.endswith(".html"):
            shutil.copy2(os.path.join("templates", file), os.path.join(checkpoint_dir, "templates"))
            logger.info(f"✅ Template {file} copiado para o checkpoint")
    
    # Copiar CSS
    if os.path.exists("static/style.css"):
        os.makedirs(os.path.join(checkpoint_dir, "static"), exist_ok=True)
        shutil.copy2("static/style.css", os.path.join(checkpoint_dir, "static"))
        logger.info(f"✅ CSS copiado para o checkpoint")
    
    # Criar arquivo de informações do checkpoint
    with open(os.path.join(checkpoint_dir, "checkpoint_info.txt"), "w") as f:
        f.write(f"Checkpoint criado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("Aplicativo funcionando perfeitamente\n")
        f.write("Arquivos incluídos neste checkpoint:\n")
        for file in main_files:
            if os.path.exists(file):
                f.write(f"- {file}\n")
        f.write("\nTemplates:\n")
        for file in template_files:
            if file.endswith(".html"):
                f.write(f"- templates/{file}\n")
    
    logger.info(f"✅ Checkpoint criado com sucesso em: {checkpoint_dir}")
    return checkpoint_dir

if __name__ == "__main__":
    checkpoint_path = create_checkpoint()
    print("\n==============================================")
    print(f"✅ CHECKPOINT CRIADO COM SUCESSO!")
    print(f"📁 Local: {checkpoint_path}")
    print("==============================================\n")
