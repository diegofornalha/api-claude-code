#!/bin/bash

# Script para configurar o comando claude-py

echo "🔧 Configurando comando claude-py..."

# Cria link simbólico no /usr/local/bin
if [ -w /usr/local/bin ]; then
    sudo ln -sf $(pwd)/claude-py /usr/local/bin/claude-py
    echo "✅ Link criado em /usr/local/bin/claude-py"
else
    # Alternativa: adiciona ao PATH do usuário
    echo 'export PATH="'$(pwd)':$PATH"' >> ~/.bashrc
    echo "✅ Adicionado ao PATH em ~/.bashrc"
    echo "⚠️  Execute: source ~/.bashrc"
fi

# Torna executável
chmod +x claude-py

echo ""
echo "✅ Configuração completa!"
echo ""
echo "Agora você pode usar:"
echo "  claude-py 'sua pergunta'"
echo "  claude-py  (modo interativo)"
echo ""
echo "Ou diretamente:"
echo "  ./claude-py 'sua pergunta'"