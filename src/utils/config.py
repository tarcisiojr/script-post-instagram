import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Diretórios
BASE_DIR = Path(__file__).parent.parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
CREDENTIALS_DIR = BASE_DIR / "credentials"
LOGS_DIR = BASE_DIR / "logs"

# Criar diretórios se não existirem
DOWNLOADS_DIR.mkdir(exist_ok=True)
CREDENTIALS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Google APIs
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
GOOGLE_CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
GOOGLE_TOKEN_FILE = CREDENTIALS_DIR / "token.json"

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Instagram
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Configurações da aplicação
SHEET_NAME = "Página1"
BATCH_SIZE = 10  # Número de discos para processar por vez
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]