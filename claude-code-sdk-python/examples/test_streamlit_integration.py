#!/usr/bin/env python3
"""
🧪 Teste de Integração Streamlit
Verifica se o wrapper funciona corretamente
"""

import time
from claude_cli_wrapper import query_claude, disconnect_claude

def test_basic_query():
    """Testa query básica"""
    print("🔍 Testando query básica...")
    
    start_time = time.time()
    result = query_claude("Você está funcionando corretamente? Responda em uma linha.")
    execution_time = time.time() - start_time
    
    print(f"⏱️  Tempo de execução: {execution_time:.2f}s")
    
    if result["success"]:
        print("✅ Query bem-sucedida!")
        print(f"📝 Resposta: {result['content'][:100]}...")
        
        if result.get("usage"):
            usage = result["usage"]
            if hasattr(usage, 'input_tokens'):
                print(f"🔢 Tokens: {usage.input_tokens}↑ {usage.output_tokens}↓")
        
        if result.get("cost"):
            print(f"💰 Custo: ${result['cost']:.6f}")
        
        return True
    else:
        print(f"❌ Erro: {result['error']}")
        return False

def test_multiple_queries():
    """Testa múltiplas queries"""
    print("\n🔍 Testando múltiplas queries...")
    
    queries = [
        "Quanto é 2 + 2?",
        "Qual é a capital do Brasil?",
        "Diga 'OK' se você está funcionando"
    ]
    
    success_count = 0
    total_time = 0
    
    for i, query in enumerate(queries, 1):
        print(f"📤 Query {i}: {query}")
        
        start_time = time.time()
        result = query_claude(query)
        execution_time = time.time() - start_time
        total_time += execution_time
        
        if result["success"]:
            print(f"✅ Resposta {i}: {result['content'][:50]}...")
            success_count += 1
        else:
            print(f"❌ Erro {i}: {result['error']}")
        
        print(f"⏱️  Tempo: {execution_time:.2f}s\n")
    
    print(f"📊 Resultado: {success_count}/{len(queries)} queries bem-sucedidas")
    print(f"⏱️  Tempo total: {total_time:.2f}s")
    print(f"⏱️  Tempo médio: {total_time/len(queries):.2f}s")
    
    return success_count == len(queries)

def test_error_handling():
    """Testa tratamento de erros"""
    print("\n🔍 Testando tratamento de erros...")
    
    # Força desconexão para simular erro
    disconnect_result = disconnect_claude()
    print(f"🔌 Desconexão: {'✅' if disconnect_result['success'] else '❌'}")
    
    # Tenta query após desconexão (deve reconectar automaticamente)
    result = query_claude("Teste após desconexão - você consegue reconectar?")
    
    if result["success"]:
        print("✅ Reconexão automática funcionou!")
        print(f"📝 Resposta: {result['content'][:100]}...")
        return True
    else:
        print(f"❌ Falha na reconexão: {result['error']}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes de integração do Streamlit...")
    print("=" * 60)
    
    tests = [
        ("Query Básica", test_basic_query),
        ("Múltiplas Queries", test_multiple_queries),
        ("Tratamento de Erros", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Teste: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            results.append((test_name, False))
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_name:.<40} {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 TODOS OS TESTES PASSARAM! Integração funcionando perfeitamente.")
        return 0
    else:
        print("⚠️  ALGUNS TESTES FALHARAM. Verifique os logs acima.")
        return 1

if __name__ == "__main__":
    exit(main())