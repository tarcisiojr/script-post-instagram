#!/bin/bash

echo "🎵 Instalando Vinyl Instagram Bot..."
echo ""

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p credentials downloads logs

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cp .env.example .env
    echo "⚠️  Por favor, edite o arquivo .env com suas credenciais!"
fi

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "Próximos passos:"
echo "1. Configure suas credenciais no arquivo .env"
echo "2. Baixe credentials.json do Google Cloud Console"
echo "3. Execute: python main.py setup"
echo ""