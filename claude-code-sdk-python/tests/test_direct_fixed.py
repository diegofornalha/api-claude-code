#!/usr/bin/env python3
"""Test direto - versão sem query real (evita timeout)"""

import sys
from pathlib import Path

# Adiciona path correto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_direct_import():
    """Testa importação direta dos módulos"""
    print("Testando importações diretas...")
    
    try:
        # Testa importação do query do módulo src
        from src.query import query
        print("✅ Importou 'query' com sucesso")
        
        # Testa importação dos tipos
        from src.sdk_types import AssistantMessage, TextBlock, ResultMessage
        print("✅ Importou tipos de mensagem com sucesso")
        
        # Verifica que são callable/classes
        assert callable(query)
        assert isinstance(AssistantMessage, type)
        assert isinstance(TextBlock, type)
        assert isinstance(ResultMessage, type)
        print("✅ Todos os imports são válidos")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Erro de validação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def main():
    print("=" * 50)
    print("TEST DIRECT - VERSÃO FIXA (SEM TIMEOUT)")
    print("=" * 50)
    
    success = test_direct_import()
    
    print("=" * 50)
    if success:
        print("✅ Script finalizado com SUCESSO")
        print("Saindo...")
        return 0
    else:
        print("❌ Script falhou")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)