# 🚀 Claude Chat Streamlit - Guia de Uso

Interface web interativa para o Claude Code SDK Python usando Streamlit.

## 📦 Instalação e Configuração

### 1. Instalar Dependências
```bash
# Instalar Streamlit
pip install streamlit

# Ou usar o requirements específico
pip install -r examples/requirements_streamlit.txt
```

### 2. Executar o Aplicativo

#### Opção 1: Script Automático
```bash
# Usar o script de execução
./scripts/run_streamlit.sh
```

#### Opção 2: Comando Direto
```bash
# Executar diretamente
streamlit run examples/streamlit_chat_app.py --server.port=8504
```

#### Opção 3: Servidor Remoto
```bash
# Para acesso externo (servidor)
streamlit run examples/streamlit_chat_app.py \
  --server.port=8504 \
  --server.address=0.0.0.0
```

## 🎯 Funcionalidades

### Interface Principal
- **💬 Chat Interativo**: Conversa em tempo real com Claude
- **📊 Métricas**: Tokens consumidos e custo por mensagem
- **🔄 Controle de Sessão**: Limpar contexto, nova conversa
- **⏱️ Timestamps**: Horário de cada mensagem

### Sidebar - Controles
- **🟢/🔴 Status**: Indicador de conexão
- **🔄 Nova Conversa**: Limpa contexto atual
- **🚪 Desconectar**: Encerra sessão
- **📊 Estatísticas Totais**: Tokens e custos acumulados

### Comandos Especiais
- **📨 Enviar**: Envia mensagem atual
- **💡 Exemplo**: Envia pergunta de exemplo
- **Enter**: Atalho para enviar (dentro do form)

## 🔧 Personalização

### Portas Disponíveis
```bash
# Padrão
--server.port=8504

# Alternativas
--server.port=8501  # Streamlit padrão
--server.port=8502  # Alternativa 1
--server.port=8503  # Alternativa 2
```

### Configurações do Servidor
```bash
# Servidor local apenas
--server.address=127.0.0.1

# Acesso externo
--server.address=0.0.0.0

# Modo headless (sem browser automático)
--server.headless=true

# Desabilitar coleta de estatísticas
--browser.gatherUsageStats=false
```

## 💡 Exemplos de Uso

### 1. Chat Básico
1. Abra o aplicativo
2. Digite: "Olá Claude! Como você está?"
3. Clique em "📨 Enviar"
4. Aguarde a resposta

### 2. Programação
```
Pergunta: "Você pode me ajudar a criar uma função Python para calcular fibonacci?"
Resposta: Claude criará a função e explicará o código
```

### 3. Análise de Código
```
Pergunta: "Analise este código e sugira melhorias: [colar código]"
Resposta: Claude analisará e dará sugestões
```

### 4. Nova Conversa
1. Clique em "🔄 Nova Conversa" na sidebar
2. O contexto será limpo
3. Nova sessão começará

## 🎨 Interface Visual

### Cores e Temas
- **Usuário**: Fundo azul claro com borda azul
- **Claude**: Fundo verde claro com borda verde  
- **Métricas**: Caixa cinza com informações de uso
- **Header**: Gradiente azul/roxo

### Layout Responsivo
- **Desktop**: Sidebar expandida, chat centralizado
- **Mobile**: Sidebar colapsível, layout otimizado
- **Tablet**: Layout híbrido adaptatível

## 📊 Monitoramento

### Métricas por Mensagem
- **Tokens de Entrada**: Quantos tokens enviados
- **Tokens de Saída**: Quantos tokens recebidos
- **Custo**: Valor em USD da consulta

### Estatísticas Totais
- **Total Input**: Soma de todos tokens enviados
- **Total Output**: Soma de todos tokens recebidos
- **Custo Total**: Valor acumulado da sessão

## 🛠️ Solução de Problemas

### Erro: Porta em Uso
```bash
# Tente outra porta
streamlit run examples/streamlit_chat_app.py --server.port=8505
```

### Erro: Módulo não Encontrado
```bash
# Verifique se está no diretório correto
cd /path/to/claude-code-sdk-python

# Instale dependências
pip install -r examples/requirements_streamlit.txt
```

### Erro: Claude não Responde
1. Verifique conexão com internet
2. Confirme se Claude CLI está configurado
3. Tente "🔄 Nova Conversa"

### Performance Lenta
1. Feche outras abas do navegador
2. Limite o histórico de mensagens
3. Use "🔄 Nova Conversa" periodicamente

## 🚀 Dicas de Uso

### Produtividade
1. **Use Exemplos**: Botão "💡 Exemplo" para começar
2. **Contexto Claro**: Seja específico nas perguntas
3. **Limpe Contexto**: Use "Nova Conversa" quando mudar de tópico

### Desenvolvimento
1. **Cole Código**: Claude pode analisar código colado
2. **Peça Explicações**: Solicite explicações detalhadas
3. **Iteração**: Faça perguntas de follow-up

### Economia
1. **Monitore Tokens**: Acompanhe uso na sidebar
2. **Perguntas Diretas**: Evite perguntas muito longas
3. **Nova Conversa**: Limpe contexto desnecessário

## 📱 Acesso Remoto

### Servidor Local
```bash
# URL local
http://localhost:8504
```

### Servidor Externo
```bash
# Configure o servidor
streamlit run examples/streamlit_chat_app.py \
  --server.port=8504 \
  --server.address=0.0.0.0

# Acesse via IP
http://SEU_IP:8504
```

### Nginx/Apache (Opcional)
```nginx
# Proxy reverso para domínio
location /claude-chat {
    proxy_pass http://localhost:8504;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 📚 Recursos Adicionais

- **CLI Original**: `wrappers_cli/claude` para modo terminal
- **Exemplos Python**: Pasta `examples/` com mais exemplos
- **Documentação**: Pasta `docs/` com guias completos
- **Scripts**: Pasta `scripts/` com utilitários

---

🎉 **Pronto!** Agora você tem uma interface web completa para usar o Claude Code SDK Python!