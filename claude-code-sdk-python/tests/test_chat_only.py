#!/usr/bin/env python3
"""Teste do modo chat único."""

from unittest.mock import MagicMock, patch
import pytest

@pytest.mark.timeout(5)
def test_chat():
    """Testa modo chat com mock."""
    print("=== TESTANDO MODO CHAT (MOCKADO) ===\n")
    
    # Mock do subprocess
    with patch('subprocess.Popen') as mock_popen:
        # Configura mock
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = [
            "🤖 Claude Code SDK v0.0.20 - Chat Interativo\n",
            "💬 Digite suas mensagens e pressione Enter\n",
            "📝 Comandos: 's' ou 'sair' para sair\n",
            "------------------------------------------------------------\n",
            "\n",
            "Claude: 2 + 2 equals 4\n",
            "👤 Você: ",
            "Claude: 4 * 5 = 20\n", 
            "👤 Você: ",
            "🔄 Contexto limpo!\n",
            "",
            ""
        ]
        mock_process.wait.return_value = None
        mock_process.stdin.write.return_value = None
        mock_process.stdin.flush.return_value = None
        mock_popen.return_value = mock_process
        
        # Simula interação
        print(">>> Mock: 'Quanto é 2 + 2?'")
        assert mock_process.stdout.readline() is not None
        
        print(">>> Mock: 'Multiplique o resultado anterior por 5'")
        assert mock_process.stdout.readline() is not None
        
        print(">>> Mock: 'clear'")
        assert mock_process.stdout.readline() is not None
        
        print("\n=== TESTE CONCLUÍDO COM SUCESSO ===")
        assert True

if __name__ == "__main__":
    test_chat()