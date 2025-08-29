#!/usr/bin/env python3
"""
🔍 VERIFICADOR DE PROBLEMAS COMUNS
Detecta e sugere soluções para erros frequentes
"""

import sys
import subprocess
import importlib.util
from pathlib import Path

# Cores
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BLUE = '\033[94m'

def check_python_version():
    """Verifica versão do Python"""
    print(f"\n{BLUE}📌 Verificando Python...{RESET}")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"{GREEN}✅ Python {version.major}.{version.minor} OK{RESET}")
        return True
    else:
        print(f"{RED}❌ Python {version.major}.{version.minor} - Precisa ser 3.10+{RESET}")
        print(f"   Solução: sudo apt install python3.10")
        return False

def check_claude_cli():
    """Verifica se Claude CLI está instalado"""
    print(f"\n{BLUE}📌 Verificando Claude CLI...{RESET}")
    try:
        result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{GREEN}✅ Claude CLI encontrado{RESET}")
            return True
        else:
            print(f"{YELLOW}⚠️  Claude CLI não encontrado{RESET}")
            print(f"   Solução: npm install -g @anthropic-ai/claude-code")
            return False
    except:
        print(f"{RED}❌ Erro ao verificar Claude CLI{RESET}")
        return False

def check_sdk_imports():
    """Verifica se o SDK pode ser importado"""
    print(f"\n{BLUE}📌 Verificando imports do SDK...{RESET}")
    
    # Adiciona src ao path
    src_path = Path(__file__).parent.parent / 'src'
    sys.path.insert(0, str(src_path))
    
    modules_to_check = [
        ('src', 'Módulo principal'),
        ('src.client', 'Cliente'),
        ('src.sdk_types', 'Tipos'),
        ('src.query', 'Query function')
    ]
    
    all_ok = True
    for module, desc in modules_to_check:
        try:
            spec = importlib.util.find_spec(module)
            if spec:
                print(f"{GREEN}✅ {desc} ({module}){RESET}")
            else:
                print(f"{RED}❌ {desc} ({module}) não encontrado{RESET}")
                all_ok = False
        except ImportError as e:
            print(f"{RED}❌ {desc} ({module}): {e}{RESET}")
            all_ok = False
    
    if not all_ok:
        print(f"{YELLOW}   Solução: pip install -e .{RESET}")
    
    return all_ok

def check_venv():
    """Verifica se está em ambiente virtual"""
    print(f"\n{BLUE}📌 Verificando ambiente virtual...{RESET}")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"{GREEN}✅ Ambiente virtual ativo{RESET}")
        return True
    else:
        print(f"{YELLOW}⚠️  Não está em ambiente virtual{RESET}")
        print(f"   Recomendado: python3 -m venv venv && source venv/bin/activate")
        return False

def check_permissions():
    """Verifica permissões dos scripts"""
    print(f"\n{BLUE}📌 Verificando permissões...{RESET}")
    
    scripts = [
        'wrappers_cli/claude',
        'scripts/setup_iniciante.sh'
    ]
    
    all_ok = True
    for script in scripts:
        script_path = Path(__file__).parent.parent / script
        if script_path.exists():
            if script_path.stat().st_mode & 0o111:
                print(f"{GREEN}✅ {script} executável{RESET}")
            else:
                print(f"{YELLOW}⚠️  {script} sem permissão de execução{RESET}")
                print(f"   Solução: chmod +x {script}")
                all_ok = False
        else:
            print(f"{YELLOW}⚠️  {script} não existe{RESET}")
    
    return all_ok

def check_common_errors():
    """Verifica erros conhecidos do Neo4j"""
    print(f"\n{BLUE}📌 Verificando erros conhecidos...{RESET}")
    
    # Verifica se types.py foi renomeado
    types_file = Path(__file__).parent.parent / 'src' / 'types.py'
    sdk_types_file = Path(__file__).parent.parent / 'src' / 'sdk_types.py'
    
    if types_file.exists():
        print(f"{RED}❌ Arquivo 'types.py' ainda existe (conflito com módulo Python){RESET}")
        print(f"   Solução: Renomear para 'sdk_types.py'")
        return False
    elif sdk_types_file.exists():
        print(f"{GREEN}✅ Arquivo 'sdk_types.py' correto{RESET}")
        return True
    else:
        print(f"{YELLOW}⚠️  Nem types.py nem sdk_types.py encontrados{RESET}")
        return False

def main():
    """Executa todas as verificações"""
    print("=" * 60)
    print(f"{BLUE}🔍 VERIFICADOR DE PROBLEMAS - CLAUDE SDK PYTHON{RESET}")
    print("=" * 60)
    
    results = {
        'Python': check_python_version(),
        'Claude CLI': check_claude_cli(),
        'Ambiente Virtual': check_venv(),
        'Imports SDK': check_sdk_imports(),
        'Permissões': check_permissions(),
        'Erros Conhecidos': check_common_errors()
    }
    
    # Resumo
    print("\n" + "=" * 60)
    print(f"{BLUE}📊 RESUMO:{RESET}")
    print("-" * 40)
    
    all_ok = True
    for item, status in results.items():
        if status:
            print(f"  {GREEN}✅ {item}{RESET}")
        else:
            print(f"  {RED}❌ {item}{RESET}")
            all_ok = False
    
    print("=" * 60)
    if all_ok:
        print(f"{GREEN}🎉 TUDO CERTO! SDK pronto para uso!{RESET}")
        print(f"\nTeste com: python -m src 'Olá mundo!'")
    else:
        print(f"{YELLOW}⚠️  ALGUNS PROBLEMAS DETECTADOS{RESET}")
        print(f"Execute as soluções sugeridas acima")
        print(f"\nOu execute: ./scripts/setup_iniciante.sh")
    print("=" * 60)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())