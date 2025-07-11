from pathlib import Path
from typing import List, Optional
from datetime import datetime
from src.services.google_drive import GoogleDriveService
from src.services.google_sheets import GoogleSheetsService
from src.services.gemini import GeminiService
from src.services.instagram import InstagramService
from src.utils.config import GEMINI_API_KEY, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
from src.utils.logger import logger


class CatalogService:
    """Serviço principal para catalogação e publicação de discos"""
    
    def __init__(self):
        self.drive_service = GoogleDriveService()
        self.sheets_service = GoogleSheetsService()
        self.gemini_service = GeminiService(GEMINI_API_KEY) if GEMINI_API_KEY else None
        self.instagram_service = None
        
        # Inicializa planilha
        self.sheets_service.initialize_sheet()
    
    def initialize_instagram(self):
        """Inicializa serviço do Instagram quando necessário"""
        if not self.instagram_service and INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
            try:
                self.instagram_service = InstagramService(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                return True
            except Exception as e:
                logger.error(f"Erro ao inicializar Instagram: {e}")
                return False
        return bool(self.instagram_service)
    
    def scan_and_catalog(self, limit: Optional[int] = None) -> int:
        """
        Escaneia imagens do Drive e cataloga discos na planilha
        
        Args:
            limit: Número máximo de discos para processar
            
        Returns:
            Número de discos catalogados
        """
        logger.info("🔍 Iniciando escaneamento e catalogação...")
        
        if not self.gemini_service:
            logger.error("❌ Gemini API não configurada. Configure GEMINI_API_KEY no .env")
            return 0
        
        # Busca pares de imagens
        image_pairs = self.drive_service.download_all_images()
        
        if not image_pairs:
            logger.warning("Nenhuma imagem encontrada para processar")
            return 0
        
        # Limita processamento se especificado
        if limit:
            image_pairs = image_pairs[:limit]
        
        cataloged_count = 0
        
        for i, pair in enumerate(image_pairs, 1):
            try:
                logger.info(f"\n📀 Processando disco {i}/{len(image_pairs)}")
                
                front_info = pair['front']
                back_info = pair['back']
                
                front_path = front_info['path']
                back_path = back_info['path'] if back_info else None
                
                # Analisa imagens com Gemini
                vinyl = self.gemini_service.analyze_vinyl_images(front_path, back_path)
                
                # Adiciona URLs do Drive
                vinyl.imagem1_url = self.drive_service.get_drive_url(front_info['id'])
                vinyl.imagem2_url = self.drive_service.get_drive_url(back_info['id']) if back_info else None
                
                # Gera post de venda
                vinyl.post_venda = self.gemini_service.generate_sales_post(vinyl)
                
                # Adiciona à planilha (ou atualiza se já existir)
                if self.sheets_service.add_or_update_vinyl(vinyl):
                    cataloged_count += 1
                    logger.info(f"✅ Disco catalogado: {vinyl.nome}")
                else:
                    logger.error(f"❌ Erro ao adicionar disco à planilha")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar disco {i}: {e}")
                continue
        
        logger.info(f"\n🎉 Catalogação concluída! {cataloged_count} discos adicionados")
        return cataloged_count
    
    def publish_pending(self, limit: Optional[int] = None) -> int:
        """
        Publica discos pendentes no Instagram
        
        Args:
            limit: Número máximo de posts para publicar
            
        Returns:
            Número de posts publicados
        """
        logger.info("📱 Iniciando publicação de discos pendentes...")
        
        # Inicializa Instagram se necessário
        if not self.initialize_instagram():
            logger.error("❌ Instagram não configurado. Configure credenciais no .env")
            return 0
        
        # Busca discos pendentes
        pending_vinyls = self.sheets_service.get_pending_vinyls()
        
        if not pending_vinyls:
            logger.info("Nenhum disco pendente para publicação")
            return 0
        
        # Limita publicações se especificado
        if limit:
            pending_vinyls = pending_vinyls[:limit]
        
        published_count = 0
        
        for vinyl_data in pending_vinyls:
            try:
                logger.info(f"\n📸 Publicando: {vinyl_data['Nome']} - {vinyl_data['Artista']}")
                
                # Prepara imagens
                images = []
                if vinyl_data.get('Imagem Frente'):
                    front_path = Path(vinyl_data['Imagem Frente'])
                    if front_path.exists():
                        images.append(front_path)
                
                if vinyl_data.get('Imagem Verso'):
                    back_path = Path(vinyl_data['Imagem Verso'])
                    if back_path.exists():
                        images.append(back_path)
                
                if not images:
                    logger.error("Nenhuma imagem encontrada para o post")
                    continue
                
                # Publica no Instagram
                caption = vinyl_data.get('Post Venda', '')
                media = self.instagram_service.post_album(images, caption)
                
                if media:
                    # Atualiza status na planilha
                    row_index = vinyl_data['row_index']
                    self.sheets_service.update_status(
                        row_index, 
                        'publicado', 
                        datetime.now()
                    )
                    published_count += 1
                    logger.info(f"✅ Publicado com sucesso!")
                else:
                    logger.error(f"❌ Falha ao publicar no Instagram")
                
            except Exception as e:
                logger.error(f"❌ Erro ao publicar disco: {e}")
                continue
        
        logger.info(f"\n🎉 Publicação concluída! {published_count} posts publicados")
        return published_count
    
    def list_catalog(self, status_filter: Optional[str] = None) -> List[dict]:
        """
        Lista discos catalogados com filtro opcional
        
        Args:
            status_filter: Filtro por status (pendente, publicado, vendido)
            
        Returns:
            Lista de discos
        """
        all_vinyls = self.sheets_service.get_all_vinyls()
        
        if status_filter:
            filtered = [
                v for v in all_vinyls 
                if v.get('Status', '').lower() == status_filter.lower()
            ]
            return filtered
        
        return all_vinyls
    
    def update_price(self, row_index: int, price: float) -> bool:
        """
        Atualiza preço de um disco
        
        Args:
            row_index: Índice da linha na planilha
            price: Novo preço
            
        Returns:
            True se sucesso
        """
        try:
            range_name = f"{self.sheets_service.sheet_name}!G{row_index}"
            self.sheets_service.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.sheets_service.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [[f'R$ {price:.2f}']]}
            ).execute()
            
            logger.info(f"✅ Preço atualizado na linha {row_index}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar preço: {e}")
            return False