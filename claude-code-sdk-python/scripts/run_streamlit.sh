#!/bin/bash

# Script para executar o aplicativo Streamlit do Claude Chat

echo "🚀 Iniciando Claude Chat - Streamlit App..."
echo "================================================"

# Verifica se o streamlit está instalado
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit não encontrado. Instalando..."
    pip install streamlit
fi

# Diretório do projeto
PROJECT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$PROJECT_DIR"

echo "📁 Diretório: $PROJECT_DIR"
echo "🌐 Interface será aberta automaticamente no navegador"
echo "🔌 Porta padrão: 8501"
echo ""
echo "💡 Para parar o servidor: Ctrl+C"
echo "================================================"

# Executa o streamlit (versão robusta)
echo "📋 Escolha a versão:"
echo "1. Robusta (CLI subprocess) - Recomendada"
echo "2. Avançada (asyncio completo)"
read -p "Digite 1 ou 2: " version

if [ "$version" = "2" ]; then
    echo "🚀 Iniciando versão avançada..."
    streamlit run examples/streamlit_chat_app.py \
        --server.port=8504 \
        --server.address=0.0.0.0 \
        --browser.gatherUsageStats=false \
        --server.headless=false
else
    echo "🛡️ Iniciando versão robusta..."
    streamlit run examples/streamlit_chat_simple.py \
        --server.port=8504 \
        --server.address=0.0.0.0 \
        --browser.gatherUsageStats=false \
        --server.headless=false
fi

echo ""
echo "👋 Aplicativo encerrado!"