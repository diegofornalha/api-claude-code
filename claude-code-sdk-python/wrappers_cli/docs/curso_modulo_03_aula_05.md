# 🎯 Módulo 3 - Aula 5: Engenharia de Sessão Única e Monitor de Persistência

## 📋 Visão Geral da Aula

**Duração:** 150 minutos (2h30min)  
**Nível:** Avançado  
**Pré-requisitos:** Aulas 1-4 do Módulo 3

### Objetivos de Aprendizagem
- 🎯 Entender o problema de múltiplos arquivos JSONL
- 🔍 Diagnosticar comportamento do CLI vs SDK
- 🛠️ Implementar solução de monitor em tempo real
- 📊 Validar persistência de sessão única

---

## 📚 1. O Problema: Fragmentação de Sessões (30min)

### 1.1 Diagnóstico Inicial

```python
# PROBLEMA: Cada nova conexão cria um novo arquivo
# Exemplo do que acontecia:
/home/suthub/.claude/projects/.../
├── 17673e37-51d5-44ef-85a6-ec9bf79a0a2b.jsonl  # Sessão 1
├── 522ea3ba-713e-4602-b1d4-1bd69454e7d1.jsonl  # Sessão 2
├── 9be151bd-cd36-4087-ade7-36d4ba9ff195.jsonl  # Sessão 3
└── 50468c19-5559-477e-ae1c-7868c067846c.jsonl  # Sessão desejada
```

### 1.2 Impactos do Problema

```python
# Consequências da fragmentação:
impactos = {
    "perda_contexto": "Claude não lembra conversas anteriores",
    "fragmentacao_dados": "Histórico espalhado em múltiplos arquivos",
    "gestao_complexa": "Impossível rastrear conversas",
    "memoria_perdida": "Cada sessão começa do zero"
}
```

### 1.3 Análise Root Cause

```python
# Descoberta: CLI cria sessões independentemente
def analise_problema():
    """
    O SDK chama o CLI via subprocess
    O CLI tem sua própria lógica de sessão
    Resultado: Novo UUID a cada conexão
    """
    
    # Tentativa com SDK
    options = ClaudeCodeOptions(session_id="fixo")
    client = ClaudeSDKClient(options)  # CLI ignora!
    
    # CLI cria: abc-123-def-456.jsonl (novo!)
```

### 💡 Exercício 1: Reproduzindo o Problema
```bash
# Execute múltiplas vezes e observe os arquivos criados
python3 -c "
from src import ClaudeSDKClient
import asyncio

async def test():
    client = ClaudeSDKClient()
    await client.connect()
    await client.disconnect()

asyncio.run(test())
"

# Verifique: quantos arquivos foram criados?
ls ~/.claude/projects/*/*.jsonl | wc -l
```

---

## 🔬 2. Tentativas de Solução (40min)

### 2.1 Abordagem 1: Parâmetros do SDK ❌

```python
# TENTATIVA: Forçar session_id
class TentativaParametros:
    def __init__(self):
        self.FIXED_ID = "50468c19-5559-477e-ae1c-7868c067846c"
    
    async def tentar(self):
        # Tentativa 1: session_id
        options = ClaudeCodeOptions(session_id=self.FIXED_ID)
        
        # Tentativa 2: resume
        options = ClaudeCodeOptions(resume=self.FIXED_ID)
        
        # Tentativa 3: ambos
        options = ClaudeCodeOptions(
            session_id=self.FIXED_ID,
            resume=self.FIXED_ID,
            continue_conversation=True
        )
        
        # RESULTADO: CLI ainda cria novos arquivos!
```

### 2.2 Abordagem 2: Interceptação Python ❌

```python
# TENTATIVA: Interceptar função open()
import builtins

_original_open = builtins.open

def intercepted_open(file, mode='r', *args, **kwargs):
    """Redireciona abertura de arquivos"""
    if '.jsonl' in str(file) and 'w' in mode:
        # Força arquivo correto
        return _original_open(FIXED_FILE, mode, *args, **kwargs)
    return _original_open(file, mode, *args, **kwargs)

builtins.open = intercepted_open

# PROBLEMA: CLI é processo separado, não afetado!
```

### 2.3 Abordagem 3: Gerenciamento Local ❌

```python
# TENTATIVA: Gerenciar sessão localmente
class LocalSessionManager:
    def __init__(self):
        self.messages = []
    
    def save_message(self, role, content):
        # Salva localmente
        self.messages.append({
            "role": role,
            "content": content
        })
        
        # Grava no arquivo fixo
        with open(FIXED_FILE, 'a') as f:
            f.write(json.dumps(message) + '\n')

# PROBLEMA: SDK/CLI ainda criam arquivos próprios!
```

### 💡 Exercício 2: Testando Limitações
```python
# Crie um script para testar as abordagens falhas
# teste_abordagens.py

import asyncio
from pathlib import Path
from src import ClaudeSDKClient, ClaudeCodeOptions

SESSIONS_DIR = Path.home() / ".claude/projects/..."

async def test_approaches():
    # Conta arquivos antes
    before = len(list(SESSIONS_DIR.glob("*.jsonl")))
    
    # Teste com parâmetros
    options = ClaudeCodeOptions(
        session_id="teste-fixo",
        resume="teste-fixo"
    )
    
    client = ClaudeSDKClient(options)
    await client.connect()
    await client.query("teste")
    await client.disconnect()
    
    # Conta arquivos depois
    after = len(list(SESSIONS_DIR.glob("*.jsonl")))
    
    print(f"Arquivos antes: {before}")
    print(f"Arquivos depois: {after}")
    print(f"Novos arquivos criados: {after - before}")

asyncio.run(test_approaches())
```

---

## 🛡️ 3. Solução: Monitor de Diretório (50min)

### 3.1 Conceito da Solução

```python
"""
PARADIGMA: Em vez de PREVENIR, vamos DETECTAR e CORRIGIR

Fluxo:
1. CLI cria arquivo novo (não podemos impedir)
2. Monitor detecta em ~100ms
3. Move conteúdo para arquivo correto
4. Remove arquivo indevido
5. Resultado: apenas arquivo correto existe
"""
```

### 3.2 Implementação do Monitor

```python
# claude_monitor.py - Versão completa
import os
import sys
import time
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime

# Configuração
FIXED_SESSION_ID = "50468c19-5559-477e-ae1c-7868c067846c"
SESSIONS_DIR = Path.home() / ".claude/projects/..."
FIXED_FILE = SESSIONS_DIR / f"{FIXED_SESSION_ID}.jsonl"

class DirectoryMonitor:
    """Monitor que detecta e corrige arquivos em tempo real"""
    
    def __init__(self):
        self.running = True
        self.intercepted = []
        self.corrections = 0
        
    def monitor_loop(self):
        """Loop principal de monitoramento"""
        print("🔍 Monitor ativo - protegendo sessão única...")
        
        while self.running:
            try:
                # Varre diretório a cada 100ms
                for file in SESSIONS_DIR.glob("*.jsonl"):
                    # Detecta arquivo indevido
                    if file.name != f"{FIXED_SESSION_ID}.jsonl":
                        self.correct_file(file)
                        
            except Exception as e:
                print(f"❌ Erro no monitor: {e}")
            
            time.sleep(0.1)  # Intervalo de verificação
    
    def correct_file(self, wrong_file):
        """Corrige arquivo indevido"""
        print(f"\n⚠️ DETECTADO: {wrong_file.name}")
        
        try:
            # 1. Lê conteúdo do arquivo errado
            with open(wrong_file, 'r') as f:
                lines = f.readlines()
            
            # 2. Adiciona ao arquivo correto
            if lines:
                with open(FIXED_FILE, 'a') as f:
                    for line in lines:
                        # Atualiza sessionId
                        try:
                            data = json.loads(line)
                            data['sessionId'] = FIXED_SESSION_ID
                            f.write(json.dumps(data) + '\n')
                        except:
                            f.write(line)
                
                print(f"✅ Conteúdo movido: {len(lines)} linhas")
            
            # 3. Remove arquivo indevido
            wrong_file.unlink()
            print(f"🗑️ Arquivo removido: {wrong_file.name}")
            
            self.intercepted.append(wrong_file.name)
            self.corrections += 1
            
        except Exception as e:
            print(f"❌ Erro ao corrigir: {e}")
    
    def start(self):
        """Inicia monitor em thread separada"""
        self.thread = threading.Thread(
            target=self.monitor_loop, 
            daemon=True
        )
        self.thread.start()
        
    def stop(self):
        """Para o monitor"""
        self.running = False
        
    def get_stats(self):
        """Retorna estatísticas"""
        return {
            "corrections": self.corrections,
            "intercepted_files": len(self.intercepted),
            "unique_files": len(set(self.intercepted))
        }
```

### 3.3 Integração com Chat

```python
async def run_monitored_chat():
    """Chat com proteção de monitor"""
    
    # Inicia monitor protetor
    monitor = DirectoryMonitor()
    monitor.start()
    
    print("\n" + "="*70)
    print("🛡️ CHAT PROTEGIDO - SESSÃO ÚNICA GARANTIDA")
    print("="*70)
    print(f"📌 Arquivo único: {FIXED_SESSION_ID}")
    
    # Cliente normal do SDK
    client = ClaudeSDKClient()
    await client.connect()
    
    print("✅ Conectado (monitor protetor ativo)")
    print("\n💬 Chat iniciado...")
    
    try:
        while True:
            # Input do usuário
            user_input = input("\n👤 Você: ").strip()
            
            if user_input.lower() in ['sair', 's']:
                break
            
            # Envia mensagem (CLI pode criar arquivo novo)
            await client.query(user_input)
            
            # Recebe resposta
            print("🤖 Claude: ", end="", flush=True)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="")
            
            # Monitor já corrigiu em background!
            
    finally:
        await client.disconnect()
        monitor.stop()
        
        # Relatório final
        stats = monitor.get_stats()
        print(f"\n📊 Estatísticas do Monitor:")
        print(f"  - Correções realizadas: {stats['corrections']}")
        print(f"  - Arquivos interceptados: {stats['intercepted_files']}")
        print(f"  - Arquivos únicos detectados: {stats['unique_files']}")
```

### 💡 Exercício 3: Implementando o Monitor
```python
# Crie monitor_test.py e teste a solução

import asyncio
from pathlib import Path

# 1. Implemente a classe DirectoryMonitor
# 2. Teste com mensagem simples
# 3. Verifique que apenas 1 arquivo existe após execução

async def test_monitor():
    monitor = DirectoryMonitor()
    monitor.start()
    
    # Simula criação de arquivo errado
    wrong_file = SESSIONS_DIR / "teste-123.jsonl"
    with open(wrong_file, 'w') as f:
        f.write('{"test": "data"}\n')
    
    # Aguarda correção
    await asyncio.sleep(0.5)
    
    # Verifica correção
    assert not wrong_file.exists()
    print("✅ Monitor funcionando!")
    
    monitor.stop()

asyncio.run(test_monitor())
```

---

## 🧪 4. Validação e Testes (30min)

### 4.1 Suite de Testes

```python
# test_single_session.py
import unittest
import asyncio
from pathlib import Path
import time

class TestSingleSession(unittest.TestCase):
    """Testes para garantir sessão única"""
    
    def setUp(self):
        self.monitor = DirectoryMonitor()
        self.monitor.start()
        
    def tearDown(self):
        self.monitor.stop()
    
    def test_file_correction(self):
        """Testa correção de arquivo"""
        # Cria arquivo errado
        wrong = SESSIONS_DIR / "wrong.jsonl"
        wrong.write_text('{"test": "data"}\n')
        
        # Aguarda correção
        time.sleep(0.2)
        
        # Verifica
        self.assertFalse(wrong.exists())
        self.assertTrue(FIXED_FILE.exists())
    
    def test_content_preservation(self):
        """Testa preservação de conteúdo"""
        test_data = '{"message": "important data"}\n'
        
        # Cria arquivo errado com dados
        wrong = SESSIONS_DIR / "wrong2.jsonl"
        wrong.write_text(test_data)
        
        # Aguarda correção
        time.sleep(0.2)
        
        # Verifica conteúdo movido
        with open(FIXED_FILE, 'r') as f:
            content = f.read()
            self.assertIn("important data", content)
    
    def test_multiple_files(self):
        """Testa múltiplos arquivos simultâneos"""
        files = []
        for i in range(5):
            f = SESSIONS_DIR / f"test_{i}.jsonl"
            f.write_text(f'{{"id": {i}}}\n')
            files.append(f)
        
        # Aguarda correções
        time.sleep(1)
        
        # Verifica que todos foram removidos
        for f in files:
            self.assertFalse(f.exists())
        
        # Verifica estatísticas
        stats = self.monitor.get_stats()
        self.assertEqual(stats['corrections'], 5)
```

### 4.2 Testes de Performance

```python
def test_monitor_performance():
    """Testa performance do monitor"""
    
    monitor = DirectoryMonitor()
    monitor.start()
    
    # Métricas
    start_time = time.time()
    detections = []
    
    # Cria arquivo teste
    test_file = SESSIONS_DIR / "perf_test.jsonl"
    test_file.write_text('{"test": "performance"}\n')
    
    # Aguarda detecção
    while test_file.exists() and time.time() - start_time < 1:
        time.sleep(0.01)
    
    detection_time = time.time() - start_time
    
    print(f"⏱️ Tempo de detecção: {detection_time*1000:.2f}ms")
    assert detection_time < 0.2  # Deve detectar em menos de 200ms
    
    monitor.stop()
```

### 💡 Exercício 4: Criando Teste End-to-End
```python
# Crie e2e_test.py para teste completo

async def test_e2e():
    """Teste end-to-end completo"""
    
    # 1. Inicia monitor
    monitor = DirectoryMonitor()
    monitor.start()
    
    # 2. Conecta cliente
    client = ClaudeSDKClient()
    await client.connect()
    
    # 3. Envia mensagem
    await client.query("Teste E2E")
    
    # 4. Aguarda resposta
    async for msg in client.receive_response():
        if isinstance(msg, ResultMessage):
            break
    
    # 5. Desconecta
    await client.disconnect()
    
    # 6. Para monitor
    monitor.stop()
    
    # 7. Validações
    all_files = list(SESSIONS_DIR.glob("*.jsonl"))
    assert len(all_files) == 1
    assert all_files[0].name == f"{FIXED_SESSION_ID}.jsonl"
    
    print("✅ Teste E2E passou!")

asyncio.run(test_e2e())
```

---

## 🎯 Projeto Prático: Sistema Completo (60min)

### Implementação Final

```python
#!/usr/bin/env python3
"""
Sistema completo de chat com sessão única garantida
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
import threading
import time

# [Implemente aqui o sistema completo combinando:]
# 1. DirectoryMonitor
# 2. SessionManager para contexto
# 3. Interface de chat
# 4. Logging e métricas
# 5. Tratamento de erros

class SingleSessionChatSystem:
    """Sistema completo com sessão única"""
    
    def __init__(self):
        self.monitor = DirectoryMonitor()
        self.session_file = FIXED_FILE
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "corrections_made": 0,
            "session_start": datetime.now()
        }
    
    async def run(self):
        """Executa o sistema completo"""
        # Seu código aqui...
        pass

# Execute e teste o sistema completo
if __name__ == "__main__":
    system = SingleSessionChatSystem()
    asyncio.run(system.run())
```

---

## 📊 Métricas de Sucesso

### KPIs da Solução
```python
metricas = {
    "tempo_deteccao": "< 200ms",
    "taxa_correcao": "100%",
    "perda_dados": "0%",
    "arquivos_finais": "1 (único)",
    "persistencia": "Total entre sessões"
}
```

### Checklist de Validação
- [ ] Monitor detecta arquivos em < 200ms
- [ ] Todo conteúdo é preservado
- [ ] Apenas 1 arquivo JSONL existe
- [ ] SessionId é mantido consistente
- [ ] Chat funciona normalmente
- [ ] Contexto é mantido entre sessões

---

## 🏆 Desafios Avançados

### Desafio 1: Monitor Inteligente
Implemente detecção de padrões para prever quando CLI criará novo arquivo.

### Desafio 2: Backup Automático
Adicione sistema de backup incremental do arquivo único.

### Desafio 3: Métricas em Tempo Real
Crie dashboard que mostra correções em tempo real.

### Desafio 4: Multi-usuário
Adapte solução para múltiplos usuários com sessões separadas.

---

## 📚 Recursos Adicionais

### Documentação Relacionada
- [SOLUCAO_SESSAO_UNICA.md](../SOLUCAO_SESSAO_UNICA.md)
- [TESTE_COMPLETO_MONITOR.md](../TESTE_COMPLETO_MONITOR.md)

### Código Fonte
- `claude_monitor.py` - Implementação completa
- Scripts de teste na pasta `wrappers_cli/`

### Conceitos Avançados
- Threading vs Async em Python
- Monitoramento de filesystem
- Race conditions e sincronização
- Patterns de correção automática

---

## ✅ Conclusão da Aula

### O que aprendemos:
1. **Diagnóstico** - Como identificar problemas de persistência
2. **Tentativas** - Por que soluções óbvias falharam
3. **Solução** - Monitor em tempo real como paradigma
4. **Implementação** - Código production-ready
5. **Validação** - Testes completos da solução

### Próximos Passos:
- Implementar variações do monitor
- Explorar otimizações de performance
- Integrar com sistemas de produção
- Documentar casos de uso

### 🎯 Tarefa de Casa:
1. Implemente o sistema completo
2. Adicione logging detalhado
3. Crie testes automatizados
4. Documente 3 melhorias possíveis

---

**⏱️ Tempo Total da Aula:** 150 minutos  
**📝 Exercícios Práticos:** 4  
**🏆 Projeto Final:** Sistema de Chat com Sessão Única

> 💡 **Lição Principal:** Às vezes, a melhor solução não é prevenir o problema, mas detectá-lo e corrigi-lo em tempo real de forma transparente.

---

*Próxima Aula: Módulo 4 - Aula 1: Arquitetura em 4 Camadas*