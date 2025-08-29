# 🔍 Sistema de Debug Avançado - Streamlit App

Sistema completo de debug, monitoramento e diagnóstico integrado ao aplicativo Streamlit do Claude Code SDK Python.

## 🎯 Funcionalidades do Debug

### 1. **🔍 Modo Debug**
- **Ativação**: Checkbox "🔍 Modo Debug" na sidebar
- **Painel Expansível**: Expander "🔍 Debug Panel - Sistema Avançado"
- **4 Abas Especializadas**: Logs, Performance, Sistema, Métricas

### 2. **📝 Sistema de Logs**
- **Níveis**: ERROR, WARNING, INFO, DEBUG
- **Armazenamento**: Arquivo `streamlit_debug.log` + Session State
- **Filtragem**: Por nível e quantidade de logs
- **Formato**: Timestamp, ícone, nível, mensagem
- **Detalhes**: JSON expandível com informações técnicas

### 3. **🚀 Monitoramento de Performance**
- **Decorator**: `@measure_performance()` para funções assíncronas
- **Métricas**: Tempo de execução, status, erros
- **Estatísticas**: Tempo médio, máximo, taxa de sucesso
- **Histórico**: Últimas 20 execuções com detalhes

### 4. **🔄 Reconexão Automática**
- **Detecção**: Erros de conexão automaticamente identificados
- **Reconexão**: Client e conexão resetados automaticamente
- **Logs**: Todo processo documentado em logs debug
- **Interface**: Botão manual "🔄 Reconectar Agora"

### 5. **📊 Métricas Detalhadas**
- **Por Mensagem**: Tokens, custo, tempo de resposta
- **Totais da Sessão**: Acumuladores em tempo real
- **Gráficos**: Visualização de tokens ao longo do tempo
- **Exportação**: Download de dados em JSON

## 🛠️ Componentes Técnicos

### Logging System
```python
# Configuração automática
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console
        logging.FileHandler('streamlit_debug.log')  # Arquivo
    ]
)

# Função de log customizada
add_debug_log("info", "Mensagem", {"detalhes": "dados"})
```

### Performance Measurement
```python
@measure_performance("nome_funcao")
async def minha_funcao():
    # Automaticamente medida e logada
    pass
```

### Session State Extensions
```python
# Novos estados para debug
st.session_state.debug_mode = False
st.session_state.debug_logs = []
st.session_state.performance_metrics = []
```

## 📋 Interface de Debug

### Tab 1: 📝 Logs
- **Filtros**: Níveis ERROR/WARNING/INFO/DEBUG
- **Quantidade**: Configurável (5-100 logs)
- **Formatação**: Cores por nível de severidade
- **Ações**: Limpar logs, ver traceback completo
- **Detalhes**: JSON expansível por log

### Tab 2: 📈 Performance  
- **Métricas Resumo**: 4 cards com estatísticas
- **Tabela Detalhada**: 20 execuções mais recentes
- **Colunas**: Função, Tempo, Status, Hora, Erro
- **Indicadores Visuais**: ✅ Sucesso / ❌ Erro

### Tab 3: 🔧 Sistema
- **Info do Sistema**: Python, Streamlit, timestamps
- **Estado da Sessão**: Contadores de mensagens e logs
- **Exportação**: Download completo em JSON
- **Diagnóstico**: Informações técnicas detalhadas

### Tab 4: 📊 Métricas
- **Tabela por Mensagem**: Tokens e custos individuais
- **Gráfico Linear**: Evolução de tokens ao longo do tempo
- **Tempo de Resposta**: Performance por interação
- **Análise Histórica**: Tendências de uso

## 🚨 Sistema de Alertas

### Códigos de Cor
- **🔴 ERROR**: Fundo vermelho, problemas críticos
- **🟡 WARNING**: Fundo amarelo, avisos importantes  
- **🟢 INFO/DEBUG**: Fundo verde, informações normais

### Tipos de Log
1. **Connection Logs**: Conexão, desconexão, reconexão
2. **Message Logs**: Envio, recebimento, processamento
3. **Performance Logs**: Tempos de execução, erros
4. **System Logs**: Inicialização, limpeza, export

## 🔄 Fluxo de Reconexão

### Detecção Automática
```python
# Em send_message() - detecção de erro
if "connection" in str(e).lower() or "disconnect" in str(e).lower():
    add_debug_log("warning", "Tentando reconexão devido a erro de conexão")
    st.session_state.connected = False
    st.session_state.client = None
```

### Verificação Preventiva
```python
def check_and_reconnect():
    if not st.session_state.connected or not st.session_state.client:
        # Força reconexão na próxima interação
        return False
    return True
```

### Reconexão Manual
- **Botão**: "🔄 Reconectar Agora" na sidebar
- **Ação**: `asyncio.run(connect_client())`
- **Log**: Todo processo documentado

## 📁 Arquivos de Saída

### `streamlit_debug.log`
```
2025-08-29 09:30:15,123 - INFO - Aplicativo Streamlit iniciado
2025-08-29 09:30:20,456 - DEBUG - Criando nova instância do ClaudeSDKClient
2025-08-29 09:30:25,789 - INFO - Conexão estabelecida com sucesso
```

### Export JSON
```json
{
  "system_info": {
    "python_version": "3.11.0",
    "streamlit_version": "1.49.0",
    "current_time": "2025-08-29T09:30:00"
  },
  "debug_logs": [...],
  "performance_metrics": [...],
  "export_time": "2025-08-29T09:30:00"
}
```

## 🎛️ Configurações Avançadas

### Debug Mode
```python
# Ativado via checkbox na sidebar
st.session_state.debug_mode = st.checkbox("🔍 Modo Debug")

# Controla visibilidade do painel
if st.session_state.debug_mode:
    render_debug_panel()
```

### Log Levels
```python
log_levels = st.multiselect(
    "Filtrar por nível:",
    ["ERROR", "WARNING", "INFO", "DEBUG"],
    default=["ERROR", "WARNING", "INFO"]
)
```

### Performance Thresholds
- **Tempo Médio**: Calculado automaticamente
- **Tempo Máximo**: Destacado em vermelho se > 10s
- **Taxa de Sucesso**: Alerta se < 90%

## 🧪 Testes e Validação

### Script de Teste
```bash
# Teste de reconexão automática
python examples/test_reconnection.py
```

### Cenários Testados
1. **Conexão Normal**: Estabelece e mantém conexão
2. **Desconexão Forçada**: Simula perda de conexão
3. **Reconexão Automática**: Reestabelece conexão
4. **Múltiplas Queries**: Funciona após reconexão

### Resultados Esperados
- ✅ Conexão inicial: Sucesso
- ✅ Query inicial: Resposta recebida
- ✅ Desconexão: Confirmada
- ✅ Reconexão: Automática
- ✅ Query pós-reconexão: Funcional

## 🚀 Melhorias Implementadas

### Robustez
- **Tratamento de Erros**: Try/catch em todas funções críticas
- **Logging Detalhado**: Cada passo documentado
- **Fallback**: Reconexão automática em falhas
- **State Management**: Session state consistente

### Performance
- **Medição Automática**: Todas funções async monitoradas
- **Métricas Visuais**: Gráficos e tabelas em tempo real
- **Histórico**: Últimas execuções sempre disponíveis
- **Otimização**: Logs limitados para performance

### Experiência do Usuário
- **Interface Intuitiva**: Debug panel organizado em tabs
- **Feedback Visual**: Cores e ícones informativos
- **Controles Simples**: Botões claros e diretos
- **Informações Relevantes**: Dados úteis para troubleshooting

---

🎉 **Sistema de debug completo e funcional, garantindo conectividade automática e monitoramento detalhado!**