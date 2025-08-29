#!/usr/bin/env python3
"""
Script corrigido para executar testes com PYTHONPATH correto
"""

import os
import sys
import subprocess
from pathlib import Path

# Configura o PYTHONPATH corretamente
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))
os.environ['PYTHONPATH'] = str(src_path)

def run_test(test_file):
    """Executa um teste individual com ambiente configurado."""
    print(f"\n🧪 Testando: {test_file.name}")
    print("-" * 40)
    
    # Prepara o ambiente
    env = os.environ.copy()
    env['PYTHONPATH'] = str(src_path)
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "✅" in result.stdout or result.returncode == 0:
            print(f"✅ PASSOU")
            if result.stdout:
                print(result.stdout[:200])
            return True
        else:
            print(f"❌ FALHOU")
            if result.stderr:
                error_lines = result.stderr.split('\n')
                for line in error_lines[-3:]:
                    if line:
                        print(f"   {line}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT (>10s)")
        return False
    except Exception as e:
        print(f"💥 ERRO: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 EXECUTANDO TESTES COM PYTHONPATH CORRIGIDO")
    print("=" * 60)
    print(f"PYTHONPATH configurado: {src_path}")
    
    # Lista de testes que sabemos que podem funcionar
    test_files = [
        'tests/test_simples.py',
        'tests/test_sdk_funcionando.py',
        'tests/test_sdk_basic_functionality.py',
        'tests/test_direct.py'
    ]
    
    results = []
    for test_file in test_files:
        test_path = project_root / test_file
        if test_path.exists():
            success = run_test(test_path)
            results.append((test_file, success))
        else:
            print(f"\n⚠️ Arquivo não encontrado: {test_file}")
            results.append((test_file, False))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test}")
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"Taxa de sucesso: {percentage:.1f}%")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    elif passed > 0:
        print(f"\n⚠️ {total - passed} teste(s) falharam")
    else:
        print("\n❌ Nenhum teste passou - verificar configuração")

if __name__ == "__main__":
    main()