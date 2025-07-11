import logging
from pathlib import Path
from datetime import datetime
from rich.logging import RichHandler
from .config import LOGS_DIR


def setup_logger(name: str = "vinyl_bot") -> logging.Logger:
    """Configura e retorna um logger com formatação rica"""
    
    # Cria nome do arquivo de log com timestamp
    log_file = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configura o logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove handlers existentes
    if logger.handlers:
        logger.handlers.clear()
    
    # Handler para console com Rich
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_level=True
    )
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_format)
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Adiciona handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Logger padrão da aplicação
logger = setup_logger()