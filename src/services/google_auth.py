from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.utils.config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE, GOOGLE_SHEETS_ID
from src.utils.logger import logger


class GoogleAuthService:
    """Serviço de autenticação para Google APIs"""
    
    # Escopos necessários para Drive e Sheets
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    def __init__(self):
        self.creds = None
        self._authenticate()
    
    def _authenticate(self):
        """Realiza autenticação com Google OAuth2"""
        # Token existe e é válido
        if GOOGLE_TOKEN_FILE.exists():
            self.creds = Credentials.from_authorized_user_file(
                str(GOOGLE_TOKEN_FILE), 
                self.SCOPES
            )
            logger.debug("Token carregado do arquivo")
        
        # Se não há credenciais válidas
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                logger.info("Renovando token expirado...")
                self.creds.refresh(Request())
            else:
                if not GOOGLE_CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"Arquivo de credenciais não encontrado: {GOOGLE_CREDENTIALS_FILE}\n"
                        "Por favor, baixe as credenciais do Google Cloud Console e "
                        f"salve em {GOOGLE_CREDENTIALS_FILE}"
                    )
                
                logger.info("Iniciando fluxo de autenticação OAuth2...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(GOOGLE_CREDENTIALS_FILE), 
                    self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Salva as credenciais para próxima execução
            with open(GOOGLE_TOKEN_FILE, 'w') as token:
                token.write(self.creds.to_json())
            logger.info("Token salvo com sucesso")
    
    def get_drive_service(self):
        """Retorna serviço autenticado do Google Drive"""
        return build('drive', 'v3', credentials=self.creds)
    
    def get_sheets_service(self):
        """Retorna serviço autenticado do Google Sheets"""
        return build('sheets', 'v4', credentials=self.creds)
    
    def test_connection(self):
        """Testa a conexão com as APIs do Google"""
        try:
            # Testa Drive
            drive_service = self.get_drive_service()
            drive_service.files().list(pageSize=1).execute()
            logger.info("✅ Conexão com Google Drive estabelecida")
            
            # Testa Sheets
            sheets_service = self.get_sheets_service()
            sheets_service.spreadsheets().get(
                spreadsheetId=GOOGLE_SHEETS_ID
            ).execute()
            logger.info("✅ Conexão com Google Sheets estabelecida")
            
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao testar conexão: {e}")
            return False