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

                # Prepara imagens baixando do Google Drive
                images = []
                
                # Baixa imagem frontal
                if vinyl_data.get("imagem1"):
                    front_url = vinyl_data["imagem1"]
                    front_file_id = self._extract_file_id_from_url(front_url)
                    if front_file_id:
                        try:
                            # Gera nome único para o arquivo temporário
                            front_filename = f"temp_front_{front_file_id}.jpg"
                            front_path = self.drive_service.download_image(front_file_id, front_filename)
                            images.append(front_path)
                        except Exception as e:
                            logger.error(f"Erro ao baixar imagem frontal: {e}")

                # Baixa imagem traseira
                if vinyl_data.get("imagem2"):
                    back_url = vinyl_data["imagem2"]
                    back_file_id = self._extract_file_id_from_url(back_url)
                    if back_file_id:
                        try:
                            # Gera nome único para o arquivo temporário
                            back_filename = f"temp_back_{back_file_id}.jpg"
                            back_path = self.drive_service.download_image(back_file_id, back_filename)
                            images.append(back_path)
                        except Exception as e:
                            logger.error(f"Erro ao baixar imagem traseira: {e}")

                if not images:
                    logger.error("Nenhuma imagem pôde ser baixada para o post")
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

    def _extract_file_id_from_url(self, drive_url: str) -> Optional[str]:
        """
        Extrai o file_id de uma URL do Google Drive
        
        Args:
            drive_url: URL do Google Drive no formato https://drive.google.com/file/d/{file_id}/view
            
        Returns:
            file_id ou None se não conseguir extrair
        """
        import re
        
        if not drive_url:
            return None
            
        # Padrão para extrair file_id da URL do Drive
        pattern = r'https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)'
        match = re.search(pattern, drive_url)
        
        if match:
            return match.group(1)
        
        logger.warning(f"Não foi possível extrair file_id da URL: {drive_url}")
        return None

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
