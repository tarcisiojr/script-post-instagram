from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Vinyl:
    """Modelo para representar um disco de vinil"""
    nome: str
    artista: str
    vinyl_id: Optional[str] = None  # ID único do vinil
    ano: Optional[str] = None
    descricao: Optional[str] = None
    condicao: Optional[str] = None
    preco: Optional[float] = None
    post_venda: Optional[str] = None
    status: str = "pendente"  # pendente, publicado, vendido
    data_publicacao: Optional[datetime] = None
    imagem_frente: Optional[str] = None
    imagem_verso: Optional[str] = None
    drive_file_ids: Optional[List[str]] = None
    imagem1_url: Optional[str] = None  # URL do Drive para imagem frente
    imagem2_url: Optional[str] = None  # URL do Drive para imagem verso
    
    def __post_init__(self):
        if self.drive_file_ids is None:
            self.drive_file_ids = []
    
    def to_dict(self):
        """Converte o objeto para dicionário para salvar na planilha"""
        return {
            "#": self.vinyl_id or "",
            "Nome": self.nome,
            "Artista": self.artista,
            "Ano": self.ano or "",
            "Descrição": self.descricao or "",
            "Condição": self.condicao or "",
            "Preço": f"R$ {self.preco:.2f}" if self.preco else "",
            "Post Venda": self.post_venda or "",
            "Status": self.status,
            "Data Publicação": self.data_publicacao.strftime("%d/%m/%Y %H:%M") if self.data_publicacao else "",
            "imagem1": self.imagem1_url or "",
            "imagem2": self.imagem2_url or ""
        }