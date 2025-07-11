from pathlib import Path
from typing import List, Optional
from instagrapi import Client
from instagrapi.types import Media
from src.utils.logger import logger


class InstagramService:
    """Serviço para publicação no Instagram"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.client = Client()
        self._login()
    
    def _login(self):
        """Realiza login no Instagram"""
        try:
            # Tenta fazer login
            logger.info(f"Fazendo login no Instagram como @{self.username}...")
            self.client.login(self.username, self.password)
            logger.info("✅ Login realizado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao fazer login: {e}")
            raise
    
    def post_album(
        self, 
        images: List[Path], 
        caption: str
    ) -> Optional[Media]:
        """
        Posta um álbum (carousel) de imagens no Instagram
        
        Args:
            images: Lista de caminhos das imagens (máx 10)
            caption: Legenda do post
        
        Returns:
            Media object se sucesso, None se falhar
        """
        try:
            # Valida número de imagens
            if not images:
                logger.error("Nenhuma imagem fornecida")
                return None
            
            if len(images) > 10:
                logger.warning("Instagram permite máximo 10 imagens, usando apenas as 10 primeiras")
                images = images[:10]
            
            # Verifica se as imagens existem
            valid_images = []
            for img_path in images:
                if img_path and img_path.exists():
                    valid_images.append(str(img_path))
                else:
                    logger.warning(f"Imagem não encontrada: {img_path}")
            
            if not valid_images:
                logger.error("Nenhuma imagem válida encontrada")
                return None
            
            # Posta o álbum
            if len(valid_images) == 1:
                # Post único
                logger.info("Postando imagem única...")
                media = self.client.photo_upload(
                    valid_images[0],
                    caption=caption
                )
            else:
                # Carousel
                logger.info(f"Postando álbum com {len(valid_images)} imagens...")
                media = self.client.album_upload(
                    valid_images,
                    caption=caption
                )
            
            logger.info(f"✅ Post publicado com sucesso! ID: {media.pk}")
            return media
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar no Instagram: {e}")
            return None
    
    def post_single_image(
        self, 
        image_path: Path, 
        caption: str
    ) -> Optional[Media]:
        """
        Posta uma única imagem no Instagram
        
        Args:
            image_path: Caminho da imagem
            caption: Legenda do post
        
        Returns:
            Media object se sucesso, None se falhar
        """
        return self.post_album([image_path], caption)
    
    def check_connection(self) -> bool:
        """Verifica se está conectado ao Instagram"""
        try:
            # Tenta obter informações do próprio usuário
            user = self.client.user_info_by_username(self.username)
            logger.info(f"✅ Conectado como @{user.username}")
            return True
        except Exception as e:
            logger.error(f"❌ Não conectado: {e}")
            return False
    
    def get_recent_posts(self, limit: int = 10) -> List[Media]:
        """Retorna posts recentes do usuário"""
        try:
            user_id = self.client.user_id_from_username(self.username)
            medias = self.client.user_medias(user_id, amount=limit)
            return medias
        except Exception as e:
            logger.error(f"Erro ao buscar posts recentes: {e}")
            return []