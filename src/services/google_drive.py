import io
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from googleapiclient.http import MediaIoBaseDownload
from src.services.google_auth import GoogleAuthService
from src.utils.config import GOOGLE_DRIVE_FOLDER_ID, DOWNLOADS_DIR, IMAGE_EXTENSIONS
from src.utils.logger import logger


class GoogleDriveService:
    """Serviço para interagir com Google Drive"""
    
    def __init__(self):
        self.auth_service = GoogleAuthService()
        self.drive_service = self.auth_service.get_drive_service()
    
    def list_images(self, folder_id: str | None = None) -> List[Dict]:
        """Lista todas as imagens na pasta do Drive"""
        folder_id = folder_id or GOOGLE_DRIVE_FOLDER_ID
        
        try:
            # Query para buscar apenas imagens
            mime_types = [
                "image/jpeg",
                "image/jpg", 
                "image/png"
            ]
            mime_query = " or ".join([f"mimeType='{mt}'" for mt in mime_types])
            query = f"'{folder_id}' in parents and ({mime_query}) and trashed=false"
            
            results = []
            page_token = None
            
            while True:
                response = self.drive_service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, modifiedTime)',
                    pageToken=page_token,
                    orderBy='modifiedTime desc'
                ).execute()
                
                results.extend(response.get('files', []))
                page_token = response.get('nextPageToken', None)
                
                if page_token is None:
                    break
            
            logger.info(f"Encontradas {len(results)} imagens no Google Drive")
            return results
            
        except Exception as e:
            logger.error(f"Erro ao listar imagens: {e}")
            raise
    
    def download_image(self, file_id: str, file_name: str) -> Path:
        """Baixa uma imagem do Drive para o diretório local"""
        try:
            # Define caminho de destino
            file_path = DOWNLOADS_DIR / file_name
            
            # Se arquivo já existe, não baixa novamente
            if file_path.exists():
                logger.debug(f"Arquivo já existe: {file_name}")
                return file_path
            
            # Faz o download
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {int(status.progress() * 100)}% completo")
            
            # Salva o arquivo
            fh.seek(0)
            with open(file_path, 'wb') as f:
                f.write(fh.read())
            
            logger.info(f"✅ Download concluído: {file_name}")
            return file_path
            
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo {file_name}: {e}")
            raise
    
    def download_all_images(self) -> List[Dict]:
        """
        Baixa todas as imagens da pasta e agrupa em pares (frente/verso)
        Retorna lista de dicionários com informações completas
        """
        images = self.list_images()
        
        if not images:
            logger.warning("Nenhuma imagem encontrada no Drive")
            return []
        
        # Baixa todas as imagens
        downloaded_files = []
        for img in images:
            try:
                file_path = self.download_image(img['id'], img['name'])
                downloaded_files.append({
                    'path': file_path,
                    'name': img['name'],
                    'id': img['id'],
                    'modified': img['modifiedTime']
                })
            except Exception as e:
                logger.error(f"Erro ao baixar {img['name']}: {e}")
                continue
        
        # Agrupa em pares (assumindo ordem por data de modificação)
        pairs = []
        for i in range(0, len(downloaded_files), 2):
            if i + 1 < len(downloaded_files):
                # Par completo (frente e verso)
                pairs.append({
                    'front': downloaded_files[i],
                    'back': downloaded_files[i + 1]
                })
            else:
                # Imagem sozinha (apenas frente)
                logger.warning(f"Imagem sem par: {downloaded_files[i]['name']}")
                pairs.append({
                    'front': downloaded_files[i],
                    'back': None
                })
        
        logger.info(f"Total de {len(pairs)} discos identificados")
        return pairs
    
    def get_drive_url(self, file_id: str) -> str:
        """Gera URL de visualização do Google Drive"""
        return f"https://drive.google.com/file/d/{file_id}/view"
    
    def get_image_pairs(self) -> List[Dict]:
        """
        Retorna informações sobre os pares de imagens sem baixar
        Útil para verificar o que está disponível
        """
        images = self.list_images()
        
        if not images:
            return []
        
        # Agrupa em pares
        pairs = []
        for i in range(0, len(images), 2):
            pair = {
                'index': i // 2 + 1,
                'frente': images[i] if i < len(images) else None,
                'verso': images[i + 1] if i + 1 < len(images) else None
            }
            pairs.append(pair)
        
        return pairs