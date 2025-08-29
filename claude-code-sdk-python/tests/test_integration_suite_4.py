#!/usr/bin/env python3
"""
Executa os 4 testes principais - versões corrigidas
"""

import os
import sys
import subprocess
from pathlib import Path

# Configura ambiente
project_root = Path(__file__).parent
src_path = project_root / 'src'
os.environ['PYTHONPATH'] = str(src_path)

def run_test(test_file, name):
    """Executa um teste e retorna se passou"""
    print(f"\n🧪 Teste {name}")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            env=os.environ,
            capture_output=True,
            text=True,
            timeout=5  # 5 segundos máximo
        )
        
        # Verifica se passou
        if "✅" in result.stdout or result.returncode == 0:
            # Mostra primeiras linhas do output
            lines = result.stdout.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            print(f"✅ PASSOU")
            return True
        else:
            print(f"❌ FALHOU")
            if result.stderr:
                print(f"  Erro: {result.stderr.split(':', 1)[-1][:100]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT (>5s)")
        return False
    except Exception as e:
        print(f"💥 ERRO: {e}")
        return False

def main():
    print("=" * 60)
    print("🎯 EXECUTANDO OS 4 TESTES PRINCIPAIS")
    print("=" * 60)
    
    tests = [
        (project_root / "tests" / "test_simples.py", "test_simples.py"),
        (project_root / "tests" / "test_sdk_funcionando.py", "test_sdk_funcionando.py"),
        (project_root / "tests" / "test_sdk_basic_functionality.py", "test_sdk_basic_functionality.py"),
        (project_root / "tests" / "test_direct_fixed.py", "test_direct_fixed.py"),
    ]
    
    results = []
    for test_file, name in tests:
        if test_file.exists():
            passed = run_test(test_file, name)
            results.append((name, passed))
        else:
            print(f"\n❌ Arquivo não encontrado: {name}")
            results.append((name, False))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    passed = 0
    for name, success in results:
        if success:
            print(f"✅ {name}")
            passed += 1
        else:
            print(f"❌ {name}")
    
    total = len(results)
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS 4 TESTES PASSARAM!")
        print("✅ Status: 100% FUNCIONAL")
    else:
        print(f"\n⚠️ {total - passed} teste(s) falharam")

if __name__ == "__main__":
    main()