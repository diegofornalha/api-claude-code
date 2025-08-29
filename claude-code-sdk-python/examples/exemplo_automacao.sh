#!/bin/bash

echo "=== EXEMPLO DE AUTOMAÇÃO COM CLAUDE ==="
echo ""

# Navega para o diretório correto
cd /home/codable/terminal/claude-code-sdk-python/wrappers_cli

# Pergunta 1
echo "📌 Perguntando sobre matemática..."
RESPOSTA1=$(./claude "Quanto é 15 x 8?")
echo "$RESPOSTA1"
echo ""

# Pergunta 2
echo "📌 Perguntando sobre Python..."
RESPOSTA2=$(./claude "O que é uma lista em Python em uma frase?")
echo "$RESPOSTA2"
echo ""

# Pergunta 3
echo "📌 Perguntando sobre o dia..."
RESPOSTA3=$(./claude "Que dia da semana é hoje?")
echo "$RESPOSTA3"
echo ""

echo "=== SCRIPT FINALIZADO ==="
echo "✅ Todas as perguntas foram respondidas sem travar!"