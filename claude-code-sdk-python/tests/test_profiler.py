"""
Testes abrangentes para o módulo profiler.
"""

import pytest
import asyncio
import time
from unittest.mock import patch, Mock
from src.tools.profiler import AsyncProfiler, profile_query, get_profiler


class TestProfiler:
    """Testes para AsyncProfiler."""
    
    @pytest.fixture
    def profiler(self):
        """Fixture que cria uma nova instância do profiler para cada teste."""
        return AsyncProfiler()
    
    def test_profiler_initialization(self):
        """Teste 1: Testar criação do AsyncProfiler."""
        profiler = AsyncProfiler()
        
        assert isinstance(profiler.timings, dict)
        assert isinstance(profiler.active_timers, dict)
        assert len(profiler.timings) == 0
        assert len(profiler.active_timers) == 0
    
    def test_profiler_timer_start_stop(self, profiler):
        """Teste 2: Testar timer start/stop."""
        operation_name = "test_operation"
        
        # Iniciar timer
        profiler.start_timer(operation_name)
        assert operation_name in profiler.active_timers
        
        # Simular passagem de tempo
        time.sleep(0.001)  # 1ms
        
        # Finalizar timer
        duration = profiler.end_timer(operation_name)
        
        assert operation_name not in profiler.active_timers
        assert operation_name in profiler.timings
        assert len(profiler.timings[operation_name]) == 1
        assert duration > 0
        assert isinstance(duration, float)
    
    def test_profiler_get_summary(self, profiler):
        """Teste 3: Testar obtenção de resumo de métricas."""
        operation_name = "summary_test"
        
        # Adicionar algumas medições
        durations = [0.1, 0.2, 0.3, 0.4, 0.5]
        for duration in durations:
            with patch('time.time', side_effect=[0, duration]):
                profiler.start_timer(operation_name)
                profiler.end_timer(operation_name)
        
        stats = profiler.get_stats(operation_name)
        
        assert stats["count"] == 5
        assert stats["total"] == sum(durations)
        assert stats["average"] == sum(durations) / len(durations)
        assert stats["min"] == min(durations)
        assert stats["max"] == max(durations)
    
    def test_profiler_nested_timers(self, profiler):
        """Teste 4: Testar timers aninhados."""
        outer_op = "outer_operation"
        inner_op = "inner_operation"
        
        profiler.start_timer(outer_op)
        profiler.start_timer(inner_op)
        
        time.sleep(0.001)
        profiler.end_timer(inner_op)
        
        time.sleep(0.001)
        profiler.end_timer(outer_op)
        
        assert outer_op in profiler.timings
        assert inner_op in profiler.timings
        assert len(profiler.timings[outer_op]) == 1
        assert len(profiler.timings[inner_op]) == 1
        
        # Timer externo deve ter duração maior que o interno
        outer_duration = profiler.timings[outer_op][0]
        inner_duration = profiler.timings[inner_op][0]
        assert outer_duration > inner_duration
    
    def test_profiler_concurrent_operations(self, profiler):
        """Teste 5: Testar operações concorrentes."""
        op1 = "concurrent_op_1"
        op2 = "concurrent_op_2"
        
        # Iniciar ambas operações
        profiler.start_timer(op1)
        profiler.start_timer(op2)
        
        # Finalizar em ordem diferente
        time.sleep(0.001)
        profiler.end_timer(op2)
        
        time.sleep(0.001)
        profiler.end_timer(op1)
        
        assert op1 in profiler.timings
        assert op2 in profiler.timings
        assert len(profiler.timings[op1]) == 1
        assert len(profiler.timings[op2]) == 1
    
    @pytest.mark.asyncio
    async def test_profile_query_decorator(self):
        """Teste 6: Testar decorator profile_query."""
        
        @profile_query("decorated_operation")
        async def sample_async_function():
            await asyncio.sleep(0.001)
            return "test_result"
        
        # Limpar profiler global antes do teste
        global_profiler = get_profiler()
        global_profiler.timings.clear()
        global_profiler.active_timers.clear()
        
        result = await sample_async_function()
        
        assert result == "test_result"
        assert "decorated_operation" in global_profiler.timings
        assert len(global_profiler.timings["decorated_operation"]) == 1
        assert global_profiler.timings["decorated_operation"][0] > 0
    
    @pytest.mark.asyncio
    async def test_profile_query_with_custom_name(self):
        """Teste 7: Testar decorator com nome customizado."""
        
        @profile_query("custom_name_operation")
        async def another_async_function():
            await asyncio.sleep(0.001)
            return {"status": "success"}
        
        # Limpar profiler global
        global_profiler = get_profiler()
        global_profiler.timings.clear()
        global_profiler.active_timers.clear()
        
        result = await another_async_function()
        
        assert result == {"status": "success"}
        assert "custom_name_operation" in global_profiler.timings
        assert len(global_profiler.timings["custom_name_operation"]) == 1
    
    def test_get_profiler_singleton(self):
        """Teste 8: Testar que get_profiler retorna singleton."""
        profiler1 = get_profiler()
        profiler2 = get_profiler()
        
        assert profiler1 is profiler2
        assert id(profiler1) == id(profiler2)
        
        # Modificar em um deve refletir no outro
        profiler1.start_timer("singleton_test")
        assert "singleton_test" in profiler2.active_timers
    
    def test_profiler_error_handling(self, profiler):
        """Teste 9: Testar tratamento de erros."""
        # Tentar finalizar timer que não foi iniciado
        duration = profiler.end_timer("non_existent_operation")
        assert duration == 0
        
        # Tentar obter stats de operação inexistente
        stats = profiler.get_stats("non_existent_operation")
        assert stats == {}
        
        # Finalizar timer múltiplas vezes
        profiler.start_timer("test_op")
        duration1 = profiler.end_timer("test_op")
        duration2 = profiler.end_timer("test_op")
        
        assert duration1 > 0
        assert duration2 == 0
    
    def test_profiler_reset(self, profiler):
        """Teste 10: Testar reset de métricas."""
        # Adicionar algumas métricas
        profiler.start_timer("reset_test_1")
        profiler.end_timer("reset_test_1")
        profiler.start_timer("reset_test_2")
        profiler.end_timer("reset_test_2")
        
        assert len(profiler.timings) == 2
        
        # Reset manual (limpando os dicts)
        profiler.timings.clear()
        profiler.active_timers.clear()
        
        assert len(profiler.timings) == 0
        assert len(profiler.active_timers) == 0
    
    def test_profiler_report_generation(self, profiler):
        """Teste 11: Testar geração de relatório."""
        # Adicionar algumas operações
        with patch('time.time', side_effect=[0, 0.1]):
            profiler.start_timer("report_op_1")
            profiler.end_timer("report_op_1")
        
        with patch('time.time', side_effect=[0, 0.2]):
            profiler.start_timer("report_op_2")
            profiler.end_timer("report_op_2")
        
        report = profiler.report()
        
        assert "🔍 PERFORMANCE REPORT" in report
        assert "report_op_1" in report
        assert "report_op_2" in report
        assert "Calls: 1" in report
        assert "Avg:" in report
        assert "Min:" in report
        assert "Max:" in report
    
    def test_profiler_multiple_calls_same_operation(self, profiler):
        """Teste 12: Testar múltiplas chamadas da mesma operação."""
        operation_name = "repeated_operation"
        
        # Executar a operação 5 vezes com tempos reais
        for i in range(5):
            profiler.start_timer(operation_name)
            time.sleep(0.001)  # 1ms para cada operação
            profiler.end_timer(operation_name)
        
        assert len(profiler.timings[operation_name]) == 5
        
        stats = profiler.get_stats(operation_name)
        assert stats["count"] == 5
        assert stats["total"] > 0
        assert stats["average"] > 0
        assert stats["min"] > 0
        assert stats["max"] > 0
        
        # Todas as durações devem ser positivas
        assert all(d > 0 for d in profiler.timings[operation_name])
    
    @pytest.mark.asyncio
    async def test_profile_query_exception_handling(self):
        """Teste 13: Testar tratamento de exceções no decorator."""
        
        @profile_query("exception_operation")
        async def failing_function():
            await asyncio.sleep(0.001)
            raise ValueError("Test exception")
        
        # Limpar profiler global
        global_profiler = get_profiler()
        global_profiler.timings.clear()
        global_profiler.active_timers.clear()
        
        with pytest.raises(ValueError, match="Test exception"):
            await failing_function()
        
        # Mesmo com exceção, o timer deve ser finalizado
        assert "exception_operation" in global_profiler.timings
        assert len(global_profiler.timings["exception_operation"]) == 1
        assert len(global_profiler.active_timers) == 0  # Timer deve ser limpo
    
    def test_profiler_empty_report(self):
        """Teste 14: Testar relatório quando não há métricas."""
        profiler = AsyncProfiler()
        report = profiler.report()
        
        assert "🔍 PERFORMANCE REPORT" in report
        assert "=" * 25 in report
        # Deve ter apenas o cabeçalho se não há operações
    
    @pytest.mark.asyncio
    async def test_profile_query_default_name(self):
        """Teste 15: Testar decorator com nome padrão."""
        
        @profile_query()  # Sem especificar nome
        async def default_named_function():
            await asyncio.sleep(0.001)
            return "default_test"
        
        # Limpar profiler global
        global_profiler = get_profiler()
        global_profiler.timings.clear()
        global_profiler.active_timers.clear()
        
        result = await default_named_function()
        
        assert result == "default_test"
        assert "query" in global_profiler.timings  # Nome padrão é "query"
        assert len(global_profiler.timings["query"]) == 1