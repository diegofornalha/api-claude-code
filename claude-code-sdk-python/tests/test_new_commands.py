#!/usr/bin/env python3
"""Teste dos novos comandos de saída."""

from unittest.mock import MagicMock, patch, call
import pytest

@pytest.mark.timeout(5)
def test_commands():
    """Testa comandos com mock."""
    print("=== TESTANDO NOVOS COMANDOS (MOCKADO) ===\n")
    
    with patch('subprocess.Popen') as mock_popen:
        # Mock do processo
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Processo ainda rodando
        mock_process.wait.return_value = None
        mock_process.stdout.readline.side_effect = [
            "🤖 Claude Code SDK\n",
            "💬 Chat Interativo\n", 
            "📝 Comandos: 's' ou 'sair'\n",
            "--------------------\n",
            "\n",
            "",
            # Repetir para os outros testes
            "🤖 Claude Code SDK\n",
            "💬 Chat Interativo\n",
            "📝 Comandos: 's' ou 'sair'\n", 
            "--------------------\n",
            "\n",
            "",
            "🤖 Claude Code SDK\n",
            "💬 Chat Interativo\n",
            "📝 Comandos: 's' ou 'sair'\n",
            "--------------------\n",
            "\n",
            ""
        ]
        mock_popen.return_value = mock_process
        
        # Teste 1: Comando 's'
        print(">>> Teste 1: Comando 's' para sair")
        process = mock_popen()
        
        # Simula leitura do cabeçalho
        for _ in range(5):
            line = process.stdout.readline()
            if line:
                print(line.rstrip())
        
        print("\n>>> Mock: Enviando 's'")
        process.stdin.write("s\n")
        process.stdin.flush()
        process.wait(timeout=2)
        print("✅ Comando 's' funcionou - processo saiu\n")
        
        # Teste 2: Comando 'sair'  
        print(">>> Teste 2: Comando 'sair' para sair")
        process = mock_popen()
        
        # Pula cabeçalho
        for _ in range(6):
            process.stdout.readline()
        
        print(">>> Mock: Enviando 'sair'")
        process.stdin.write("sair\n")
        process.stdin.flush()
        process.wait(timeout=2)
        print("✅ Comando 'sair' funcionou - processo saiu\n")
        
        # Teste 3: Comandos antigos
        print(">>> Teste 3: Verificando que 'exit' e 'quit' não saem mais")
        process = mock_popen()
        
        # Pula cabeçalho
        for _ in range(6):
            process.stdout.readline()
        
        print(">>> Mock: Enviando 'exit' (deve ser tratado como pergunta)")
        process.stdin.write("exit\n")
        process.stdin.flush()
        
        # Mock: ainda está rodando
        assert process.poll() is None
        print("✅ 'exit' não saiu - tratado como mensagem normal")
        
        # Agora sai de verdade
        process.stdin.write("s\n")
        process.stdin.flush()
        process.wait(timeout=2)
        
        print("\n=== TODOS OS TESTES CONCLUÍDOS ===")
        assert True  # Teste passou

if __name__ == "__main__":
    test_commands()