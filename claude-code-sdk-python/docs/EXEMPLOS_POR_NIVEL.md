# 📚 EXEMPLOS POR NÍVEL - CLAUDE CODE SDK PYTHON

## 🎯 **VISÃO GERAL**

Este documento explica **detalhadamente** cada exemplo do SDK, organizado por nível de dificuldade. Cada exemplo inclui:
- **O que faz** - Funcionalidade específica
- **Nível** - Iniciante, Intermediário ou Avançado
- **O que a pessoa aprende** - Conhecimentos adquiridos
- **Como executar** - Comando específico
- **Caso de uso** - Quando usar

---

## 🌟 **NÍVEL INICIANTE**

### **1. `exemplo_hello_world.py` - PRIMEIRO CONTATO**

**📋 O QUE FAZ:**
- Faz uma pergunta simples ao Claude: "Olá! Pode me dizer 'Olá, mundo!' em português?"
- Mostra a resposta do Claude em tempo real
- Exibe informações de uso (tokens, custo)
- Oferece modo interativo para perguntas personalizadas
- Demonstra o fluxo básico do SDK

**🎯 NÍVEL:** 🟢 **INICIANTE** (Primeira vez usando o SDK)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Importar o SDK** - Como importar `query`, `AssistantMessage`, `TextBlock`
- ✅ **Fazer consulta básica** - Como enviar uma pergunta simples
- ✅ **Processar resposta** - Como receber e exibir respostas do Claude
- ✅ **Modo interativo** - Como fazer múltiplas perguntas
- ✅ **Tratamento de erros** - Como lidar com problemas comuns
- ✅ **Estrutura básica** - Como organizar código assíncrono

**💻 COMO EXECUTAR:**
```bash
python examples/exemplo_hello_world.py
```

**🎯 CASO DE USO:**
- **Primeira vez** usando o SDK
- **Teste de instalação** e configuração
- **Aprendizado dos conceitos básicos**
- **Demonstração para iniciantes**

**⏱️ TEMPO ESTIMADO:** 5-10 minutos

---

### **2. `quick_start.py` - INÍCIO RÁPIDO**

**📋 O QUE FAZ:**
- Demonstra funcionalidades fundamentais do SDK
- Faz queries básicas com diferentes configurações
- Mostra como usar system prompts personalizados
- Demonstra uso de ferramentas básicas (Read, Write)
- Exibe métricas de uso (custo, tokens)

**🎯 NÍVEL:** 🟢 **INICIANTE** (Conceitos básicos)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Estrutura básica** - Como organizar uma query completa
- ✅ **System prompts** - Como configurar comportamento do assistente
- ✅ **Ferramentas básicas** - Como usar Read e Write
- ✅ **Métricas de uso** - Como acessar informações de custo
- ✅ **Configurações** - Como personalizar opções básicas

**💻 COMO EXECUTAR:**
```bash
python examples/quick_start.py
```

**🎯 CASO DE USO:**
- **Entender o fluxo básico** do SDK
- **Aprender sobre system prompts**
- **Introdução às ferramentas**
- **Configurações básicas**

**⏱️ TEMPO ESTIMADO:** 10-15 minutos

---

### **3. `exemplo_basico_en.py` - EXEMPLO BÁSICO EM INGLÊS**

**📋 O QUE FAZ:**
- Demonstra funcionalidades básicas em inglês
- Faz queries simples com system prompt personalizado
- Limita conversas a um turno específico
- Mostra uso básico de ferramentas
- Estrutura clara e organizada

**🎯 NÍVEL:** 🟢 **INICIANTE** (Configurações básicas)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Limitação de turnos** - Como controlar extensão da conversa
- ✅ **System prompts em inglês** - Como configurar comportamentos
- ✅ **Estrutura básica de opções** - Como configurar parâmetros
- ✅ **Uso de ferramentas** - Como restringir capacidades
- ✅ **Organização de código** - Como estruturar exemplos

**💻 COMO EXECUTAR:**
```bash
python examples/exemplo_basico_en.py
```

**🎯 CASO DE USO:**
- **Desenvolvedores que preferem inglês**
- **Aprendizado de configurações básicas**
- **Controle de conversas**
- **Estruturação de código**

**⏱️ TEMPO ESTIMADO:** 8-12 minutos

---

### **4. `exemplo_completo_pt_br.py` - EXEMPLO COMPLETO EM PORTUGUÊS**

**📋 O QUE FAZ:**
- Demonstra funcionalidades avançadas em português
- Faz queries complexas com diferentes configurações
- Mostra uso de ferramentas específicas (Read)
- Exibe métricas detalhadas (tokens, custo)
- Configura system prompts personalizados em português

**🎯 NÍVEL:** 🟡 **INTERMEDIÁRIO** (Visão completa das funcionalidades)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Configuração completa** - Como usar todas as opções disponíveis
- ✅ **Ferramentas específicas** - Como usar Read para arquivos
- ✅ **Métricas detalhadas** - Como acessar informações completas de uso
- ✅ **System prompts avançados** - Como configurar comportamentos complexos
- ✅ **Integração de funcionalidades** - Como combinar diferentes recursos

**💻 COMO EXECUTAR:**
```bash
python examples/exemplo_completo_pt_br.py
```

**🎯 CASO DE USO:**
- **Visão completa** das funcionalidades
- **Aprendizado em português**
- **Entendimento de métricas**
- **Configurações avançadas**

**⏱️ TEMPO ESTIMADO:** 15-20 minutos

---

## 🚀 **NÍVEL INTERMEDIÁRIO**

### **5. `streaming_mode.py` - MODO STREAMING COMPLETO**

**📋 O QUE FAZ:**
- Demonstra **todas** as capacidades de streaming do SDK
- Implementa streaming básico com respostas em tempo real
- Gerencia múltiplas interações e conversas multi-turno
- Mantém cliente persistente para eficiência
- Configura opções personalizadas avançadas
- Coleta e processa mensagens estruturadas
- Trata erros de forma robusta

**🎯 NÍVEL:** 🟡 **INTERMEDIÁRIO** (Streaming e interações)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Streaming básico** - Como receber respostas em tempo real
- ✅ **Múltiplas interações** - Como manter conversas complexas
- ✅ **Cliente persistente** - Como otimizar conexões
- ✅ **Opções personalizadas** - Como configurar comportamentos avançados
- ✅ **Coleta de mensagens** - Como processar diferentes tipos de resposta
- ✅ **Tratamento de erros** - Como gerenciar falhas

**💻 COMO EXECUTAR:**
```bash
python examples/streaming_mode.py          # Lista exemplos disponíveis
python examples/streaming_mode.py all      # Executa todos os exemplos
python examples/streaming_mode.py basic_streaming  # Exemplo específico
```

**🎯 CASO DE USO:**
- **Aplicações que precisam de respostas em tempo real**
- **Conversas multi-turno complexas**
- **Clientes que fazem múltiplas queries**
- **Configurações avançadas do SDK**

**⏱️ TEMPO ESTIMADO:** 20-30 minutos

---

### **6. `streaming_mode_ipython.py` - STREAMING NO IPYTHON**

**📋 O QUE FAZ:**
- Fornece snippets executáveis para IPython/Jupyter
- Implementa streaming em tempo real para notebooks
- Mantém cliente persistente para múltiplas perguntas
- Oferece capacidade de interrupção de queries longas
- Integra perfeitamente com ambiente IPython

**🎯 NÍVEL:** 🟡 **INTERMEDIÁRIO** (Integração com IPython)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Snippets executáveis** - Como copiar/colar código funcional
- ✅ **Streaming em notebooks** - Como usar em Jupyter
- ✅ **Cliente persistente** - Como otimizar para múltiplas queries
- ✅ **Capacidade de interrupção** - Como controlar execução
- ✅ **Integração com IPython** - Como usar em ambiente de desenvolvimento

**💻 COMO EXECUTAR:**
```bash
python examples/streaming_mode_ipython.py
```

**🎯 CASO DE USO:**
- **Desenvolvimento em Jupyter notebooks**
- **Experimentação rápida com o SDK**
- **Prototipagem de aplicações**
- **Aprendizado interativo**

**⏱️ TEMPO ESTIMADO:** 15-20 minutos

---

## ⚡ **NÍVEL AVANÇADO**

### **7. `streaming_mode_trio.py` - STREAMING COM TRIO**

**📋 O QUE FAZ:**
- Integra o SDK com biblioteca assíncrona Trio
- Implementa conversas multi-turno complexas
- Configura modelo específico do Claude
- Mantém estado e contexto entre perguntas
- Demonstra cálculos sequenciais matemáticos

**🎯 NÍVEL:** 🔴 **AVANÇADO** (Programação assíncrona avançada)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Integração com Trio** - Como usar biblioteca assíncrona alternativa
- ✅ **Conversas multi-turno** - Como manter contexto complexo
- ✅ **Configuração de modelo** - Como escolher versão específica do Claude
- ✅ **Gerenciamento de estado** - Como manter informações entre interações
- ✅ **Programação assíncrona** - Como usar async/await avançado

**💻 COMO EXECUTAR:**
```bash
python examples/streaming_mode_trio.py
```

**🎯 CASO DE USO:**
- **Aplicações que usam Trio**
- **Conversas matemáticas sequenciais**
- **Configurações de modelo específicas**
- **Programação assíncrona avançada**

**⏱️ TEMPO ESTIMADO:** 20-25 minutos

---

## 🆕 **EXEMPLOS ADICIONAIS CRIADOS**

### **8. `exemplo_ferramentas_basicas.py` - FERRAMENTAS BÁSICAS**

**📋 O QUE FAZ:**
- Demonstra uso das ferramentas Read, Write e Bash
- Mostra como configurar permissões de ferramentas
- Implementa operações básicas de arquivo
- Exibe resultados de comandos bash
- Trata erros de permissão e execução

**🎯 NÍVEL:** 🟡 **INTERMEDIÁRIO** (Uso de ferramentas)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Configuração de ferramentas** - Como permitir/restringir capacidades
- ✅ **Operações de arquivo** - Como ler e escrever arquivos
- ✅ **Execução de comandos** - Como usar Bash através do SDK
- ✅ **Tratamento de permissões** - Como lidar com restrições
- ✅ **Integração de ferramentas** - Como combinar diferentes capacidades

**💻 COMO EXECUTAR:**
```bash
python examples/exemplo_ferramentas_basicas.py
```

**🎯 CASO DE USO:**
- **Automação de arquivos**
- **Execução de comandos**
- **Integração com sistema**
- **Aprendizado de ferramentas**

**⏱️ TEMPO ESTIMADO:** 15-20 minutos

---

### **9. `exemplo_tratamento_erros.py` - TRATAMENTO DE ERROS**

**📋 O QUE FAZ:**
- Demonstra diferentes tipos de erro do SDK
- Implementa tratamento robusto de exceções
- Mostra como lidar com falhas de conexão
- Exibe mensagens de erro amigáveis
- Implementa retry automático para falhas temporárias

**🎯 NÍVEL:** 🟡 **INTERMEDIÁRIO** (Robustez e confiabilidade)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Tipos de erro** - Como identificar diferentes falhas
- ✅ **Tratamento de exceções** - Como capturar e processar erros
- ✅ **Mensagens amigáveis** - Como comunicar problemas ao usuário
- ✅ **Retry automático** - Como implementar recuperação automática
- ✅ **Logging de erros** - Como registrar problemas para debug

**💻 COMO EXECUTAR:**
```bash
python examples/exemplo_tratamento_erros.py
```

**🎯 CASO DE USO:**
- **Aplicações em produção**
- **Sistemas robustos**
- **Debugging avançado**
- **Monitoramento de erros**

**⏱️ TEMPO ESTIMADO:** 15-20 minutos

---

### **10. `exemplo_integracao_web.py` - INTEGRAÇÃO COM WEB**

**📋 O QUE FAZ:**
- Demonstra integração com frameworks web (Flask, FastAPI)
- Implementa endpoints que usam o SDK
- Mostra como processar requests HTTP
- Implementa cache de respostas
- Exibe métricas de performance

**🎯 NÍVEL:** 🔴 **AVANÇADO** (Integração com web)

**📖 O QUE A PESSOA APRENDE:**
- ✅ **Integração com web** - Como usar em aplicações web
- ✅ **Processamento de requests** - Como lidar com HTTP
- ✅ **Cache de respostas** - Como otimizar performance
- ✅ **Métricas de performance** - Como medir eficiência
- ✅ **Arquitetura de aplicações** - Como estruturar sistemas

**💻 COMO EXECUTAR:**
```bash
python examples/exemplo_integracao_web.py
```

**🎯 CASO DE USO:**
- **APIs web**
- **Aplicações em produção**
- **Integração com frontend**
- **Sistemas distribuídos**

**⏱️ TEMPO ESTIMADO:** 25-35 minutos

---

## 📊 **RESUMO POR NÍVEL**

### **🟢 INICIANTE (0-15 min cada):**
1. **`exemplo_hello_world.py`** - Primeiro contato
2. **`quick_start.py`** - Conceitos básicos  
3. **`exemplo_basico_en.py`** - Configurações básicas

### **🟡 INTERMEDIÁRIO (15-30 min cada):**
4. **`exemplo_completo_pt_br.py`** - Visão completa
5. **`streaming_mode.py`** - Streaming completo
6. **`streaming_mode_ipython.py`** - Para IPython
7. **`exemplo_ferramentas_basicas.py`** - Uso de ferramentas
8. **`exemplo_tratamento_erros.py`** - Tratamento de erros

### **🔴 AVANÇADO (20-35 min cada):**
9. **`streaming_mode_trio.py`** - Com Trio
10. **`exemplo_integracao_web.py`** - Integração com web

---

## 🎯 **ORDEM RECOMENDADA DE APRENDIZADO**

### **📚 SEMANA 1: FUNDAMENTOS**
- **Dia 1-2:** Exemplos iniciantes (1-3)
- **Dia 3-4:** Exemplos intermediários básicos (4-5)
- **Dia 5-7:** Exemplos intermediários avançados (6-8)

### **🚀 SEMANA 2: APROFUNDAMENTO**
- **Dia 8-9:** Exemplos avançados (9-10)
- **Dia 10-14:** Experimentação e personalização

---

## 🎉 **RESULTADO FINAL**

**✅ 10 exemplos organizados** por nível de dificuldade  
**✅ Documentação detalhada** de cada funcionalidade  
**✅ Tempo estimado** para cada exemplo  
**✅ Casos de uso específicos** para cada nível  
**✅ Aprendizado progressivo** do básico ao avançado  

**Agora você tem um guia completo para aprender o SDK do básico ao avançado! 🚀**
