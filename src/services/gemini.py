import google.generativeai as genai
from pathlib import Path
from typing import Dict, Optional
from PIL import Image
from src.models.vinyl import Vinyl
from src.utils.logger import logger


class GeminiService:
    """Serviço para análise de imagens usando Gemini AI"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_vinyl_images(
        self, 
        front_image_path: Path, 
        back_image_path: Optional[Path] = None
    ) -> Vinyl:
        """
        Analisa imagens de capa e contracapa para extrair informações do disco
        """
        try:
            # Carrega imagens
            images = []
            front_img = Image.open(front_image_path)
            images.append(front_img)
            
            if back_image_path and back_image_path.exists():
                back_img = Image.open(back_image_path)
                images.append(back_img)
            
            # Prompt detalhado para análise
            prompt = """
            Analise as imagens de capa (e contracapa se disponível) deste disco de vinil.
            
            Extraia as seguintes informações:
            1. Nome do álbum/disco
            2. Nome do artista/banda
            3. Ano de lançamento (se visível)
            4. Lista de músicas (se visível na contracapa)
            5. Gravadora/selo (se visível)
            6. Condição aparente do disco e capa (baseado nas fotos)
            
            Retorne as informações no seguinte formato JSON:
            {
                "nome": "nome do álbum",
                "artista": "nome do artista",
                "ano": "ano ou null",
                "musicas": ["lista", "de", "músicas"],
                "gravadora": "nome da gravadora ou null",
                "condicao": "descrição da condição",
                "detalhes": "outros detalhes relevantes"
            }
            
            Seja preciso e extraia apenas informações visíveis nas imagens.
            """
            
            # Gera resposta
            response = self.model.generate_content([prompt] + images)
            
            # Parse do JSON da resposta
            import json
            # Extrai JSON da resposta (pode estar entre ```json e ```)
            text = response.text
            if '```json' in text:
                json_start = text.find('```json') + 7
                json_end = text.find('```', json_start)
                json_text = text[json_start:json_end].strip()
            else:
                json_text = text.strip()
            
            data = json.loads(json_text)
            
            # Cria objeto Vinyl
            vinyl = Vinyl(
                nome=data.get('nome', 'Desconhecido'),
                artista=data.get('artista', 'Desconhecido'),
                ano=data.get('ano'),
                condicao=data.get('condicao', 'A verificar'),
                descricao=self._format_description(data),
                imagem_frente=str(front_image_path),
                imagem_verso=str(back_image_path) if back_image_path else None
            )
            
            logger.info(f"✅ Análise concluída: {vinyl.nome} - {vinyl.artista}")
            return vinyl
            
        except Exception as e:
            logger.error(f"Erro ao analisar imagens: {e}")
            # Retorna vinyl com informações básicas em caso de erro
            return Vinyl(
                nome="[Erro na análise]",
                artista="[Verificar manualmente]",
                descricao=f"Erro ao analisar: {str(e)}",
                imagem_frente=str(front_image_path),
                imagem_verso=str(back_image_path) if back_image_path else None
            )
    
    def _format_description(self, data: Dict) -> str:
        """Formata descrição detalhada do disco"""
        parts = []
        
        if data.get('gravadora'):
            parts.append(f"Gravadora: {data['gravadora']}")
        
        if data.get('musicas'):
            musicas = "\n".join(f"• {m}" for m in data['musicas'][:10])  # Limita a 10
            parts.append(f"Principais faixas:\n{musicas}")
        
        if data.get('detalhes'):
            parts.append(f"Observações: {data['detalhes']}")
        
        return "\n\n".join(parts) if parts else ""
    
    def generate_sales_post(self, vinyl: Vinyl) -> str:
        """
        Gera post para venda no Instagram baseado nas informações do disco
        """
        try:
            prompt = f"""
            Crie um post atrativo para venda deste disco de vinil no Instagram.
            
            Informações do disco:
            - Nome: {vinyl.nome}
            - Artista: {vinyl.artista}
            - Ano: {vinyl.ano or 'não informado'}
            - Condição: {vinyl.condicao}
            - Descrição: {vinyl.descricao or 'sem descrição adicional'}
            - Preço: {f'R$ {vinyl.preco:.2f}' if vinyl.preco else 'a definir'}
            
            O post deve:
            1. Ser conciso e atrativo (máximo 300 caracteres principais)
            2. Destacar pontos positivos do disco
            3. INCLUIR AS PRINCIPAIS MÚSICAS/FAIXAS do disco na descrição
            4. Incluir emojis relevantes
            5. Ter call-to-action (chamar no direct, etc)
            6. Incluir hashtags relevantes no final
            
            IMPORTANTE: Retorne APENAS o post final, sem introduções como "Aqui está..." ou explicações.
            
            Formato desejado:
            [Texto principal atrativo]
            
            🎵 Principais faixas:
            [Lista das principais músicas do disco]
            
            💿 Detalhes:
            [Informações importantes sobre condição, gravadora, etc]
            
            📩 Interessado? Chama no direct!
            
            [Hashtags relevantes]
            """
            
            response = self.model.generate_content(prompt)
            post = response.text.strip()
            
            # Remove introduções indesejadas
            intro_patterns = [
                "Aqui está uma sugestão de post para o Instagram:",
                "Aqui está o post para o Instagram:",
                "Aqui está uma proposta de post para o Instagram:",
                "Sugestão de post:",
                "Post para Instagram:",
                "---"
            ]
            
            for pattern in intro_patterns:
                if post.startswith(pattern):
                    post = post[len(pattern):].strip()
                # Remove também se estiver no meio do texto seguido de quebra de linha
                post = post.replace(f"{pattern}\n", "").replace(f"{pattern}\n\n", "")
            
            # Remove linhas com apenas "---" 
            lines = post.split('\n')
            lines = [line for line in lines if line.strip() != "---"]
            post = '\n'.join(lines)
            
            # Limita tamanho se necessário
            if len(post) > 2000:  # Limite do Instagram
                post = post[:1997] + "..."
            
            logger.info("✅ Post de venda gerado")
            return post
            
        except Exception as e:
            logger.error(f"Erro ao gerar post: {e}")
            # Post genérico em caso de erro
            return f"""
🎵 {vinyl.nome} - {vinyl.artista} 🎵

💿 Disco em {vinyl.condicao or 'ótima condição'}
{'📅 Ano: ' + vinyl.ano if vinyl.ano else ''}
{'💰 R$ ' + f'{vinyl.preco:.2f}' if vinyl.preco else '💰 Preço especial'}

📩 Interessado? Chama no direct!

#vinil #discosdevinil #vinilbrasil #colecionadores #música
            """.strip()