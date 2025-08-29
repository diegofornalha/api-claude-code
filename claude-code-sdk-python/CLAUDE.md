# 📚 DIRETRIZES DO PROJETO - Claude Code SDK Python

## 🚫 REGRAS ABSOLUTAS - O QUE É PROIBIDO

### 1. ❌ **PROIBIDO CRIAR ARQUIVOS SOLTOS NA RAIZ**
   - **NUNCA** crie arquivos de teste, scripts ou exemplos na raiz do projeto
   - A raiz deve conter APENAS:
     - `README.md` (documentação principal)
     - `CLAUDE.md` (este arquivo de diretrizes)
     - `pyproject.toml` (configuração do projeto)
     - `run_claude.sh` (script wrapper principal)
     - Pastas organizacionais

### 2. 📁 **ORGANIZAÇÃO OBRIGATÓRIA DE ARQUIVOS**

| **Tipo de Arquivo** | **Pasta Correta** | **Exemplo** |
|-------------------|------------------|------------|
| Testes Python | `/tests/` | `test_novo_feature.py` |
| Scripts Bash | `/scripts/` | `deploy.sh`, `setup.sh` |
| Exemplos | `/examples/` | `exemplo_api.py` |
| Código fonte | `/src/` | Módulos Python do SDK |
| Documentação | `/docs/` | Guias e tutoriais |
| Configurações | Raiz | `pyproject.toml` apenas |

### 3. 🔴 **VIOLAÇÕES GRAVES**
   - Criar `test.py`, `teste.py`, `exemplo.py` na raiz → **PROIBIDO**
   - Criar scripts `.sh` temporários na raiz → **PROIBIDO**
   - Deixar arquivos de debug/log na raiz → **PROIBIDO**
   - Criar notebooks Jupyter na raiz → **PROIBIDO**

## ✅ REGRAS DE DESENVOLVIMENTO

### 1. **Estrutura do Módulo**
   - O módulo principal é `/src/` (NÃO `claude_code_sdk`)
   - Imports devem ser `from src import ...`
   - Executar com `python -m src`

### 2. **Antes de Criar Qualquer Arquivo**
   ```
   PERGUNTA: Este arquivo é um...
   - Teste? → /tests/
   - Script shell? → /scripts/
   - Exemplo? → /examples/
   - Código fonte? → /src/
   - Documentação? → /docs/
   - NENHUM DOS ACIMA? → Provavelmente não deveria existir
   ```

### 3. **Scripts Shell**
   - TODOS os scripts `.sh` vão em `/scripts/`
   - Exceção: `run_claude.sh` (wrapper principal)
   - Scripts devem ter permissão executável: `chmod +x`

### 4. **Testes**
   - TODOS os testes vão em `/tests/`
   - Nomenclatura: `test_*.py`
   - Executar com: `pytest tests/`

### 5. **Exemplos**
   - TODOS os exemplos vão em `/examples/`
   - Devem ser funcionais e documentados
   - Incluir docstring explicando o propósito

### 6. **Arquivos Temporários**
   - Use `/tmp/` ou `tempfile` do Python
   - NUNCA deixe arquivos temporários no projeto
   - Limpe após uso

## 🛠️ CONFIGURAÇÕES ESSENCIAIS

### SDK Configuration
```python
# Sempre usar flag para evitar prompts interativos
--dangerously-skip-permissions

# Módulo correto
python -m src "pergunta"

# NÃO usar
python -m claude_code_sdk  # ERRADO!
```

### Estrutura Correta
```
/home/codable/terminal/claude-code-sdk-python/
├── CLAUDE.md           # Este arquivo
├── README.md           # Documentação principal
├── pyproject.toml      # Configuração
├── run_claude.sh       # Wrapper principal
├── src/               # Código fonte
│   ├── __init__.py
│   ├── __main__.py
│   ├── client.py
│   ├── query.py
│   └── _internal/
├── tests/             # Todos os testes
├── scripts/           # Scripts auxiliares
├── examples/          # Exemplos de uso
├── docs/              # Documentação extra
└── venv/              # Ambiente virtual
```

## 📝 CHECKLIST ANTES DE COMMIT

- [ ] Nenhum arquivo solto na raiz?
- [ ] Testes em `/tests/`?
- [ ] Scripts em `/scripts/`?
- [ ] Exemplos em `/examples/`?
- [ ] Imports usando `src` não `claude_code_sdk`?
- [ ] Arquivos temporários removidos?

## 🔍 COMANDO DE VERIFICAÇÃO

```bash
# Verificar arquivos indevidos na raiz
ls -la /home/codable/terminal/claude-code-sdk-python/ | grep -v "^d" | grep -v "README\|CLAUDE\|pyproject\|run_claude"
```

## ⚡ RESPOSTA EM PT-BR
Sempre responder em português brasileiro.

---
**LEMBRE-SE**: A organização é fundamental. Cada arquivo tem seu lugar correto!