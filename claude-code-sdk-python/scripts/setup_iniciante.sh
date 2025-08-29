#!/bin/bash
# 🚀 Script de Setup Automático para Iniciantes
# Configura tudo que o iniciante precisa em 1 comando

echo "🎯 SETUP AUTOMÁTICO DO CLAUDE CODE SDK PYTHON"
echo "============================================="

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Verifica Python
echo -e "\n${YELLOW}📌 Verificando Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python $PYTHON_VERSION instalado${NC}"
else
    echo -e "${RED}❌ Python 3.10+ não encontrado!${NC}"
    echo "   Instale com: sudo apt install python3"
    exit 1
fi

# 2. Verifica Node.js
echo -e "\n${YELLOW}📌 Verificando Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js $NODE_VERSION instalado${NC}"
else
    echo -e "${RED}❌ Node.js não encontrado!${NC}"
    echo "   Instale com: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -"
    echo "                sudo apt-get install -y nodejs"
    exit 1
fi

# 3. Verifica Claude Code
echo -e "\n${YELLOW}📌 Verificando Claude Code CLI...${NC}"
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✅ Claude Code já instalado${NC}"
else
    echo -e "${YELLOW}⚠️  Claude Code não encontrado. Instalando...${NC}"
    npm install -g @anthropic-ai/claude-code
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Claude Code instalado com sucesso${NC}"
    else
        echo -e "${RED}❌ Falha ao instalar Claude Code${NC}"
        exit 1
    fi
fi

# 4. Cria ambiente virtual
echo -e "\n${YELLOW}📌 Configurando ambiente virtual Python...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Ambiente virtual já existe${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Ambiente virtual criado${NC}"
fi

# 5. Ativa venv e instala SDK
echo -e "\n${YELLOW}📌 Instalando SDK...${NC}"
source venv/bin/activate
pip install -e . -q
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SDK instalado com sucesso${NC}"
else
    echo -e "${RED}❌ Falha ao instalar SDK${NC}"
    exit 1
fi

# 6. Cria alias úteis
echo -e "\n${YELLOW}📌 Criando comandos rápidos...${NC}"

# Cria script de ativação rápida
cat > quick_start.sh << 'EOF'
#!/bin/bash
# Ativa o ambiente e mostra comandos disponíveis
source venv/bin/activate
echo "🚀 Claude SDK ativado!"
echo ""
echo "Comandos disponíveis:"
echo "  claude-ask 'pergunta'     - Pergunta rápida"
echo "  claude-chat               - Modo chat interativo"
echo "  claude-demo               - Executa demonstração"
echo ""
EOF
chmod +x quick_start.sh

# 7. Testa instalação
echo -e "\n${YELLOW}📌 Testando instalação...${NC}"
python3 -c "from src import query; print('✅ Import OK')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Tudo funcionando!${NC}"
else
    echo -e "${RED}❌ Problema com imports${NC}"
fi

# 8. Resumo final
echo ""
echo "============================================="
echo -e "${GREEN}🎉 SETUP COMPLETO!${NC}"
echo "============================================="
echo ""
echo "📚 COMO USAR:"
echo ""
echo "1. Ative o ambiente:"
echo "   source venv/bin/activate"
echo ""
echo "2. Use o SDK:"
echo "   python -m src 'sua pergunta'"
echo ""
echo "3. Ou use o wrapper rápido:"
echo "   ./wrappers_cli/claude 'sua pergunta'"
echo ""
echo "4. Veja exemplos em:"
echo "   examples/exemplo_hello_world.py"
echo ""
echo "============================================="
echo "Digite './quick_start.sh' para começar!"