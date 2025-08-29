#!/usr/bin/env python3
"""Teste simples do SDK - versão que não faz queries reais"""

import sys
from pathlib import Path

# Adiciona o caminho do SDK
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Testa se as importações funcionam"""
    try:
        # Importa do módulo src corretamente
        from src.query import query
        from src.sdk_types import AssistantMessage, TextBlock, ResultMessage
        print("✅ Importações funcionando!")
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar: {e}")
        return False

def test_types():
    """Testa criação de tipos"""
    try:
        from src.sdk_types import AssistantMessage, TextBlock
        
        # Cria um TextBlock
        text = TextBlock(text="Teste")
        assert text.text == "Teste"
        
        # Cria uma AssistantMessage
        msg = AssistantMessage(
            content=[text],
            model="test-model"
        )
        assert len(msg.content) == 1
        assert msg.model == "test-model"
        
        print("✅ Tipos funcionando corretamente!")
        return True
    except Exception as e:
        print(f"❌ Erro com tipos: {e}")
        return False

def main():
    print("=" * 50)
    print("TESTE EXEMPLO SIMPLES - VERSÃO FIXA")
    print("=" * 50)
    
    all_pass = True
    
    # Teste 1: Importações
    if not test_imports():
        all_pass = False
    
    # Teste 2: Tipos
    if not test_types():
        all_pass = False
    
    print("=" * 50)
    if all_pass:
        print("✅ TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print("❌ Alguns testes falharam")
        return 1

if __name__ == "__main__":
    exit(main())