#!/usr/bin/env python3
"""Teste simulado do modo chat."""

import subprocess
import sys
import time

def test_chat_mode():
    print("=== TESTANDO MODO CHAT ===\n")
    
    # Inicia o processo do claude sem argumentos (modo chat)
    process = subprocess.Popen(
        ["./claude"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd="/home/codable/terminal/claude-code-sdk-python/wrappers_cli"
    )
    
    # Lê o cabeçalho inicial
    for _ in range(5):  # Lê as primeiras linhas do cabeçalho
        line = process.stdout.readline()
        if line:
            print(line.rstrip())
    
    # Envia primeira mensagem
    print("\n>>> Enviando: 'Olá, tudo bem?'")
    process.stdin.write("Olá, tudo bem?\n")
    process.stdin.flush()
    time.sleep(3)  # Aguarda resposta
    
    # Lê resposta
    while True:
        line = process.stdout.readline()
        if not line or "👤 Você:" in line:
            break
        print(line.rstrip())
    
    # Envia segunda mensagem
    print("\n>>> Enviando: 'Quanto é 10 + 10?'")
    process.stdin.write("Quanto é 10 + 10?\n")
    process.stdin.flush()
    time.sleep(3)  # Aguarda resposta
    
    # Lê resposta
    while True:
        line = process.stdout.readline()
        if not line or "👤 Você:" in line:
            break
        print(line.rstrip())
    
    # Envia comando de saída
    print("\n>>> Enviando: 'sair'")
    process.stdin.write("sair\n")
    process.stdin.flush()
    
    # Aguarda processo terminar
    process.wait(timeout=5)
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == "__main__":
    test_chat_mode()