# 🎵 Vinyl Instagram Bot

Automatização para venda de discos de vinil no Instagram. O bot escaneia fotos do Google Drive, cataloga discos usando IA (Gemini) e publica automaticamente no Instagram.

## 🚀 Instalação

1. **Clone o repositório e instale dependências:**
```bash
pip install -r requirements.txt
```

2. **Configure as credenciais:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

3. **Configure o Google Cloud:**
   - Acesse [Google Cloud Console](https://console.cloud.google.com)
   - Crie um novo projeto ou selecione um existente
   - Ative as APIs: Google Drive API e Google Sheets API
   - Crie credenciais OAuth 2.0 para aplicação desktop
   - Baixe o arquivo JSON e salve como `credentials/credentials.json`

## 📋 Comandos

### Configuração inicial
```bash
python main.py setup
```

### Escanear e catalogar discos
```bash
python main.py scan              # Escaneia todos os discos
python main.py scan --limit 5    # Escaneia apenas 5 discos
```

### Publicar no Instagram
```bash
python main.py publish           # Publica todos os pendentes
python main.py publish -l 3      # Publica apenas 3 posts
python main.py publish --dry-run # Simula publicação
```

### Listar discos
```bash
python main.py list                      # Lista todos
python main.py list --status pendente    # Apenas pendentes
python main.py list --status publicado   # Apenas publicados
```

### Atualizar preço
```bash
python main.py price 10 49.90   # Define R$ 49,90 na linha 10
```

### Ver estatísticas
```bash
python main.py stats
```

## 🔧 Configuração do .env

```env
# Google APIs
GOOGLE_DRIVE_FOLDER_ID=ID_PASTA
GOOGLE_SHEETS_ID=ID_PLANILHA

# Gemini API
GEMINI_API_KEY=TOKEN

# Instagram
INSTAGRAM_USERNAME=seu_usuario
INSTAGRAM_PASSWORD=sua_senha
```

## 📁 Estrutura do Projeto

```
vinyl-instagram-bot/
├── main.py              # CLI principal
├── src/
│   ├── models/         # Modelos de dados
│   ├── services/       # Serviços (Drive, Sheets, Gemini, Instagram)
│   └── utils/          # Utilitários (config, logger)
├── credentials/        # Credenciais do Google (gitignore)
├── downloads/          # Imagens baixadas (gitignore)
└── logs/              # Arquivos de log (gitignore)
```

## 🌟 Fluxo de Trabalho

1. **Organização no Drive**: Coloque fotos dos discos (frente e verso) na pasta do Drive
2. **Escaneamento**: Execute `scan` para baixar e catalogar automaticamente
3. **Revisão**: Verifique a planilha, ajuste preços e textos se necessário
4. **Publicação**: Execute `publish` para postar no Instagram

## ⚠️ Notas Importantes

- As imagens devem estar em pares (frente/verso) ordenadas por data
- A planilha é atualizada automaticamente com status de publicação
- O bot gera posts otimizados para venda usando IA
- Recomenda-se revisar os textos antes de publicar

## 🤝 Suporte

Em caso de problemas:
1. Verifique os logs em `logs/`
2. Execute `python main.py setup` para testar conexões
3. Confirme que todas as credenciais estão corretas no `.env`