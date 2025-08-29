#!/usr/bin/env python3
"""
🧪 Teste Específico - Primeira Mensagem
Verifica se há problema na primeira execução
"""

import time
from claude_subprocess_simple import query_claude

def test_first_message():
    """Testa especificamente a primeira mensagem"""
    print("🔍 Testando primeira mensagem...")
    
    # Primeira query
    print("1️⃣ Primeira query: 'olá'")
    start_time = time.time()
    result1 = query_claude("olá")
    time1 = time.time() - start_time
    
    print(f"⏱️  Tempo: {time1:.2f}s")
    if result1["success"]:
        print(f"✅ Sucesso: {result1['content'][:100]}...")
        print(f"🔢 Tokens: {result1.get('input_tokens', 0)}↑ {result1.get('output_tokens', 0)}↓")
        print(f"💰 Custo: ${result1.get('cost', 0):.6f}")
    else:
        print(f"❌ Erro: {result1['error']}")
        return False
    
    # Segunda query
    print("\n2️⃣ Segunda query: 'tudo bem?'")
    start_time = time.time()
    result2 = query_claude("tudo bem?")
    time2 = time.time() - start_time
    
    print(f"⏱️  Tempo: {time2:.2f}s")
    if result2["success"]:
        print(f"✅ Sucesso: {result2['content'][:100]}...")
        print(f"🔢 Tokens: {result2.get('input_tokens', 0)}↑ {result2.get('output_tokens', 0)}↓")
        print(f"💰 Custo: ${result2.get('cost', 0):.6f}")
    else:
        print(f"❌ Erro: {result2['error']}")
        return False
    
    print(f"\n📊 Comparação:")
    print(f"Tempo 1ª: {time1:.2f}s | Tempo 2ª: {time2:.2f}s")
    print(f"Diferença: {abs(time1 - time2):.2f}s")
    
    return True

def test_empty_or_short():
    """Testa mensagens muito curtas"""
    print("\n🔍 Testando mensagens curtas...")
    
    test_cases = [
        ("oi", "Mensagem muito curta"),
        ("a", "Letra única"),
        ("123", "Números"),
        ("?", "Símbolo"),
        ("", "Vazia (deve falhar)")
    ]
    
    for prompt, description in test_cases:
        print(f"\n🧪 {description}: '{prompt}'")
        
        if not prompt.strip():
            print("⚠️  Mensagem vazia - esperado que falhe")
            continue
        
        start_time = time.time()
        result = query_claude(prompt)
        exec_time = time.time() - start_time
        
        if result["success"]:
            print(f"✅ Sucesso ({exec_time:.1f}s): {result['content'][:50]}...")
        else:
            print(f"❌ Erro ({exec_time:.1f}s): {result['error']}")

if __name__ == "__main__":
    print("🚀 Teste Específico da Primeira Mensagem")
    print("=" * 50)
    
    try:
        success = test_first_message()
        test_empty_or_short()
        
        if success:
            print("\n🎉 TESTE CONCLUÍDO - Primeira mensagem funciona!")
        else:
            print("\n❌ TESTE FALHOU - Problema identificado")
    except Exception as e:
        print(f"\n💥 ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()