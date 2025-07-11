from typing import List, Dict, Optional
from datetime import datetime
from src.services.google_auth import GoogleAuthService
from src.models.vinyl import Vinyl
from src.utils.config import GOOGLE_SHEETS_ID, SHEET_NAME
from src.utils.logger import logger


class GoogleSheetsService:
    """Serviço para interagir com Google Sheets"""
    
    def __init__(self):
        self.auth_service = GoogleAuthService()
        self.sheets_service = self.auth_service.get_sheets_service()
        self.spreadsheet_id = GOOGLE_SHEETS_ID
        self.sheet_name = SHEET_NAME
    
    def _get_headers(self) -> List[str]:
        """Retorna os cabeçalhos da planilha"""
        return [
            "#", "Nome", "Artista", "Ano", "Descrição", "Condição", 
            "Preço", "Post Venda", "Status", "imagem1", "imagem2", 
            "Data Publicação"
        ]
    
    def initialize_sheet(self):
        """Inicializa a planilha com cabeçalhos se necessário"""
        try:
            # Verifica se a planilha existe
            result = self.sheets_service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = result.get('sheets', [])
            sheet_exists = any(
                sheet['properties']['title'] == self.sheet_name 
                for sheet in sheets
            )
            
            if not sheet_exists:
                # Cria a aba
                request = {
                    'addSheet': {
                        'properties': {
                            'title': self.sheet_name
                        }
                    }
                }
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': [request]}
                ).execute()
                logger.info(f"Aba '{self.sheet_name}' criada")
            
            # Verifica se há cabeçalhos
            range_name = f"{self.sheet_name}!A1:L1"
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                # Adiciona cabeçalhos
                headers = [self._get_headers()]
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': headers}
                ).execute()
                logger.info("Cabeçalhos adicionados à planilha")
                
                # Formata cabeçalhos
                self._format_headers()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar planilha: {e}")
            raise
    
    def _format_headers(self):
        """Formata os cabeçalhos da planilha"""
        try:
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': self._get_sheet_id(),
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.2,
                                'green': 0.2,
                                'blue': 0.2
                            },
                            'textFormat': {
                                'foregroundColor': {
                                    'red': 1.0,
                                    'green': 1.0,
                                    'blue': 1.0
                                },
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }]
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        except Exception as e:
            logger.warning(f"Erro ao formatar cabeçalhos: {e}")
    
    def _get_sheet_id(self) -> int:
        """Obtém o ID da aba"""
        result = self.sheets_service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id
        ).execute()
        
        for sheet in result['sheets']:
            if sheet['properties']['title'] == self.sheet_name:
                return sheet['properties']['sheetId']
        
        return 0
    
    def _generate_vinyl_id(self, vinyl: Vinyl) -> str:
        """Gera ID único baseado no nome e artista"""
        import hashlib
        text = f"{vinyl.nome}_{vinyl.artista}".lower().replace(" ", "_")
        # Gera hash MD5 dos primeiros 8 caracteres
        hash_obj = hashlib.md5(text.encode())
        return hash_obj.hexdigest()[:8].upper()
    
    def find_vinyl_by_id(self, vinyl_id: str) -> Optional[int]:
        """Busca um vinil por ID e retorna o número da linha (None se não encontrado)"""
        try:
            all_vinyls = self.get_all_vinyls()
            for i, vinyl_data in enumerate(all_vinyls):
                if vinyl_data.get('#', '') == vinyl_id:
                    return i + 2  # +2 por causa do cabeçalho e índice 0
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar vinil por ID: {e}")
            return None
    
    def update_vinyl(self, row_index: int, vinyl: Vinyl) -> bool:
        """Atualiza um vinil existente na linha especificada"""
        try:
            vinyl_data = vinyl.to_dict()
            row_data = [[
                vinyl_data.get(header, "") 
                for header in self._get_headers()
            ]]
            
            range_name = f"{self.sheet_name}!A{row_index}:L{row_index}"
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': row_data}
            ).execute()
            
            logger.info(f"✅ Disco atualizado: {vinyl.nome} - {vinyl.artista}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar disco: {e}")
            return False
    
    def add_or_update_vinyl(self, vinyl: Vinyl) -> bool:
        """Adiciona um novo disco ou atualiza se já existir"""
        try:
            # Gera ID se não existir
            if not vinyl.vinyl_id:
                vinyl.vinyl_id = self._generate_vinyl_id(vinyl)
            
            # Verifica se já existe
            existing_row = self.find_vinyl_by_id(vinyl.vinyl_id)
            
            if existing_row:
                # Atualiza disco existente
                logger.info(f"🔄 Disco já existe (ID: {vinyl.vinyl_id}), atualizando...")
                return self.update_vinyl(existing_row, vinyl)
            else:
                # Adiciona novo disco
                logger.info(f"➕ Novo disco (ID: {vinyl.vinyl_id}), adicionando...")
                return self.add_vinyl(vinyl)
                
        except Exception as e:
            logger.error(f"Erro ao adicionar/atualizar disco: {e}")
            return False
    
    def add_vinyl(self, vinyl: Vinyl) -> bool:
        """Adiciona um novo disco à planilha (método interno)"""
        try:
            # Busca próxima linha vazia
            range_name = f"{self.sheet_name}!A:A"
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            next_row = len(values) + 1
            
            # Prepara dados
            vinyl_data = vinyl.to_dict()
            row_data = [[
                vinyl_data.get(header, "") 
                for header in self._get_headers()
            ]]
            
            # Adiciona à planilha
            range_name = f"{self.sheet_name}!A{next_row}:L{next_row}"
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': row_data}
            ).execute()
            
            logger.info(f"✅ Disco adicionado: {vinyl.nome} - {vinyl.artista}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar disco: {e}")
            return False
    
    def get_pending_vinyls(self) -> List[Dict]:
        """Retorna discos com status 'pendente' para publicação"""
        try:
            range_name = f"{self.sheet_name}!A2:L"
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            headers = self._get_headers()
            
            pending = []
            for i, row in enumerate(values):
                # Garante que a linha tenha todos os campos
                while len(row) < len(headers):
                    row.append("")
                
                vinyl_dict = dict(zip(headers, row))
                
                # Verifica se está pendente e tem as informações mínimas
                if (vinyl_dict.get('Status', '').lower() == 'pendente' and
                    vinyl_dict.get('Nome') and 
                    vinyl_dict.get('Post Venda')):
                    
                    vinyl_dict['row_index'] = i + 2  # +2 por causa do cabeçalho e índice 0
                    pending.append(vinyl_dict)
            
            logger.info(f"Encontrados {len(pending)} discos pendentes para publicação")
            return pending
            
        except Exception as e:
            logger.error(f"Erro ao buscar discos pendentes: {e}")
            return []
    
    def update_status(self, row_index: int, status: str, published_date: datetime = None):
        """Atualiza o status de um disco na planilha"""
        try:
            # Atualiza status (coluna I, pois agora # é a primeira)
            status_range = f"{self.sheet_name}!I{row_index}"
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=status_range,
                valueInputOption='RAW',
                body={'values': [[status]]}
            ).execute()
            
            # Atualiza data de publicação se fornecida (agora na coluna L)
            if published_date:
                date_range = f"{self.sheet_name}!L{row_index}"
                date_str = published_date.strftime("%d/%m/%Y %H:%M")
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=date_range,
                    valueInputOption='RAW',
                    body={'values': [[date_str]]}
                ).execute()
            
            logger.info(f"Status atualizado na linha {row_index}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")
            return False
    
    def get_all_vinyls(self) -> List[Dict]:
        """Retorna todos os discos da planilha"""
        try:
            range_name = f"{self.sheet_name}!A2:L"
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            headers = self._get_headers()
            
            vinyls = []
            for i, row in enumerate(values):
                # Garante que a linha tenha todos os campos
                while len(row) < len(headers):
                    row.append("")
                
                vinyl_dict = dict(zip(headers, row))
                vinyl_dict['row_index'] = i + 2
                vinyls.append(vinyl_dict)
            
            return vinyls
            
        except Exception as e:
            logger.error(f"Erro ao buscar todos os discos: {e}")
            return []