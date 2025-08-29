# 🚀 GUIA DE INÍCIO RÁPIDO - CLAUDE SDK PYTHON

## 📦 Instalação em 1 Minuto

```bash
# 1️⃣ Clone o projeto
git clone <repo-url> claude-sdk
cd claude-code-sdk-python

# 2️⃣ Execute o setup automático
chmod +x scripts/setup_iniciante.sh
./scripts/setup_iniciante.sh

# 3️⃣ Pronto! Teste com:
./wrappers_cli/claude
```

## 🎯 Primeiro Código - O Mais Simples

```python
# arquivo: meu_primeiro.py
import asyncio
from src import query

async def main():
    async for msg in query("Oi! Me diga algo legal"):
        print(msg)  # Simples assim!

asyncio.run(main())
```

## 💡 5 Exemplos Práticos

### 1. **Pergunta e Resposta**
```python
from src import query
import asyncio

# Pergunta simples
async for msg in query("Capital do Brasil?"):
    print(msg)
```

### 2. **Assistente**
```python
# Ajuda com código
prompt = "Escreva uma função Python que valide CPF"
async for msg in query(prompt):
    print(msg)
```

## 🛠️ Comandos Úteis

| O que fazer | Comando |
|------------|---------|
| Pergunta rápida | `./wrappers_cli/claude` |



## 🎉 Parabéns!

Você já sabe usar o Claude SDK! 🚀
