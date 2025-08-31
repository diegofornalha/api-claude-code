"""Comprehensive tests for message parser module."""

import pytest
from src._errors import MessageParseError
from src._internal.message_parser import parse_message
from src.sdk_types import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


class TestMessageParserValidation:
    """Test input validation for message parser."""

    def test_parse_non_dict_raises_error(self):
        """Test that non-dict input raises appropriate error."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message("not a dict")
        assert "Invalid message data type" in str(exc_info.value)
        assert "expected dict, got str" in str(exc_info.value)

    def test_parse_message_without_type_raises_error(self):
        """Test that message without type field raises error."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message({"content": "test"})
        assert "Message missing 'type' field" in str(exc_info.value)

    def test_parse_unknown_message_type_raises_error(self):
        """Test that unknown message type raises error."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message({"type": "unknown_type"})
        assert "Unknown message type: unknown_type" in str(exc_info.value)


class TestUserMessageParsing:
    """Test parsing of user messages."""

    def test_parse_user_message_with_string_content(self):
        """Test parsing user message with simple string content."""
        data = {
            "type": "user",
            "message": {
                "role": "user",
                "content": "Hello, Claude!"
            }
        }
        result = parse_message(data)
        assert isinstance(result, UserMessage)
        assert result.content == "Hello, Claude!"

    def test_parse_user_message_with_text_blocks(self):
        """Test parsing user message with text block content."""
        data = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {"type": "text", "text": "First text"},
                    {"type": "text", "text": "Second text"}
                ]
            }
        }
        result = parse_message(data)
        assert isinstance(result, UserMessage)
        assert len(result.content) == 2
        assert all(isinstance(block, TextBlock) for block in result.content)
        assert result.content[0].text == "First text"
        assert result.content[1].text == "Second text"

    def test_parse_user_message_with_tool_use_blocks(self):
        """Test parsing user message with tool use blocks."""
        data = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_123",
                        "name": "calculator",
                        "input": {"operation": "add", "a": 1, "b": 2}
                    }
                ]
            }
        }
        result = parse_message(data)
        assert isinstance(result, UserMessage)
        assert len(result.content) == 1
        assert isinstance(result.content[0], ToolUseBlock)
        assert result.content[0].id == "tool_123"
        assert result.content[0].name == "calculator"
        assert result.content[0].input == {"operation": "add", "a": 1, "b": 2}

    def test_parse_user_message_with_tool_result_blocks(self):
        """Test parsing user message with tool result blocks."""
        data = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool_123",
                        "content": "Result: 3",
                        "is_error": False
                    }
                ]
            }
        }
        result = parse_message(data)
        assert isinstance(result, UserMessage)
        assert len(result.content) == 1
        assert isinstance(result.content[0], ToolResultBlock)
        assert result.content[0].tool_use_id == "tool_123"
        assert result.content[0].content == "Result: 3"
        assert result.content[0].is_error is False

    def test_parse_user_message_with_mixed_content(self):
        """Test parsing user message with mixed content types."""
        data = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Calculate this:"},
                    {
                        "type": "tool_use",
                        "id": "calc_1",
                        "name": "calculator",
                        "input": {"expr": "2+2"}
                    },
                    {
                        "type": "tool_result",
                        "tool_use_id": "calc_1",
                        "content": "4"
                    }
                ]
            }
        }
        result = parse_message(data)
        assert isinstance(result, UserMessage)
        assert len(result.content) == 3
        assert isinstance(result.content[0], TextBlock)
        assert isinstance(result.content[1], ToolUseBlock)
        assert isinstance(result.content[2], ToolResultBlock)

    def test_parse_user_message_missing_content_raises_error(self):
        """Test that user message without content raises error."""
        data = {
            "type": "user",
            "message": {"role": "user"}
        }
        with pytest.raises(MessageParseError) as exc_info:
            parse_message(data)
        assert "Missing required field in user message" in str(exc_info.value)

    def test_parse_user_message_missing_message_field_raises_error(self):
        """Test that user message without message field raises error."""
        data = {"type": "user"}
        with pytest.raises(MessageParseError) as exc_info:
            parse_message(data)
        assert "Missing required field in user message" in str(exc_info.value)


class TestAssistantMessageParsing:
    """Test parsing of assistant messages."""

    def test_parse_assistant_message_with_text(self):
        """Test parsing assistant message with text content."""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-3-sonnet",
                "content": [
                    {"type": "text", "text": "Hello! How can I help you?"}
                ]
            }
        }
        result = parse_message(data)
        assert isinstance(result, AssistantMessage)
        assert result.model == "claude-3-sonnet"
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextBlock)
        assert result.content[0].text == "Hello! How can I help you?"

    def test_parse_assistant_message_with_thinking(self):
        """Test parsing assistant message with thinking block."""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-3-opus",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "Let me think about this...",
                        "signature": "sig_123"
                    },
                    {"type": "text", "text": "Here's my answer"}
                ]
            }
        }
        result = parse_message(data)
        assert isinstance(result, AssistantMessage)
        assert result.model == "claude-3-opus"
        assert len(result.content) == 2
        assert isinstance(result.content[0], ThinkingBlock)
        assert result.content[0].thinking == "Let me think about this..."
        assert result.content[0].signature == "sig_123"
        assert isinstance(result.content[1], TextBlock)

    def test_parse_assistant_message_with_tool_use(self):
        """Test parsing assistant message with tool use."""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-3-haiku",
                "content": [
                    {"type": "text", "text": "I'll search for that"},
                    {
                        "type": "tool_use",
                        "id": "search_1",
                        "name": "web_search",
                        "input": {"query": "Python tutorials"}
                    }
                ]
            }
        }
        result = parse_message(data)
        assert isinstance(result, AssistantMessage)
        assert len(result.content) == 2
        assert isinstance(result.content[1], ToolUseBlock)
        assert result.content[1].name == "web_search"

    def test_parse_assistant_message_with_tool_result(self):
        """Test parsing assistant message with tool result."""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-3-sonnet",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "search_1",
                        "content": "Search results here",
                        "is_error": None
                    }
                ]
            }
        }
        result = parse_message(data)
        assert isinstance(result, AssistantMessage)
        assert len(result.content) == 1
        assert isinstance(result.content[0], ToolResultBlock)
        assert result.content[0].content == "Search results here"

    def test_parse_assistant_message_with_all_content_types(self):
        """Test parsing assistant message with all content types."""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-3-opus",
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "Processing request",
                        "signature": "sig_456"
                    },
                    {"type": "text", "text": "Let me help with that"},
                    {
                        "type": "tool_use",
                        "id": "tool_789",
                        "name": "file_reader",
                        "input": {"path": "/tmp/file.txt"}
                    },
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool_789",
                        "content": "File contents"
                    },
                    {"type": "text", "text": "Based on the file..."}
                ]
            }
        }
        result = parse_message(data)
        assert isinstance(result, AssistantMessage)
        assert len(result.content) == 5
        assert isinstance(result.content[0], ThinkingBlock)
        assert isinstance(result.content[1], TextBlock)
        assert isinstance(result.content[2], ToolUseBlock)
        assert isinstance(result.content[3], ToolResultBlock)
        assert isinstance(result.content[4], TextBlock)

    def test_parse_assistant_message_missing_model_raises_error(self):
        """Test that assistant message without model raises error."""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Hello"}]
            }
        }
        with pytest.raises(MessageParseError) as exc_info:
            parse_message(data)
        assert "Missing required field in assistant message" in str(exc_info.value)

    def test_parse_assistant_message_missing_content_raises_error(self):
        """Test that assistant message without content raises error."""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-3-sonnet"
            }
        }
        with pytest.raises(MessageParseError) as exc_info:
            parse_message(data)
        assert "Missing required field in assistant message" in str(exc_info.value)


class TestSystemMessageParsing:
    """Test parsing of system messages."""

    def test_parse_system_message_basic(self):
        """Test parsing basic system message."""
        data = {
            "type": "system",
            "subtype": "info",
            "message": "System is ready"
        }
        result = parse_message(data)
        assert isinstance(result, SystemMessage)
        assert result.subtype == "info"
        assert result.data["message"] == "System is ready"

    def test_parse_system_message_with_complex_data(self):
        """Test parsing system message with complex data."""
        data = {
            "type": "system",
            "subtype": "error",
            "error_code": 500,
            "error_message": "Internal error",
            "details": {
                "timestamp": "2024-01-01T00:00:00Z",
                "trace_id": "abc123"
            }
        }
        result = parse_message(data)
        assert isinstance(result, SystemMessage)
        assert result.subtype == "error"
        assert result.data["error_code"] == 500
        assert result.data["details"]["trace_id"] == "abc123"

    def test_parse_system_message_missing_subtype_raises_error(self):
        """Test that system message without subtype raises error."""
        data = {
            "type": "system",
            "message": "System message"
        }
        with pytest.raises(MessageParseError) as exc_info:
            parse_message(data)
        assert "Missing required field in system message" in str(exc_info.value)


class TestResultMessageParsing:
    """Test parsing of result messages."""

    def test_parse_result_message_complete(self):
        """Test parsing complete result message."""
        data = {
            "type": "result",
            "subtype": "success",
            "duration_ms": 1500,
            "duration_api_ms": 1200,
            "is_error": False,
            "num_turns": 3,
            "session_id": "session_123",
            "total_cost_usd": 0.0025,
            "usage": {
                "input_tokens": 100,
                "output_tokens": 200,
                "cache_creation_tokens": 0,
                "cache_read_tokens": 50
            },
            "result": "Task completed successfully"
        }
        result = parse_message(data)
        assert isinstance(result, ResultMessage)
        assert result.subtype == "success"
        assert result.duration_ms == 1500
        assert result.duration_api_ms == 1200
        assert result.is_error is False
        assert result.num_turns == 3
        assert result.session_id == "session_123"
        assert result.total_cost_usd == 0.0025
        assert result.usage["input_tokens"] == 100
        assert result.result == "Task completed successfully"

    def test_parse_result_message_minimal(self):
        """Test parsing minimal result message."""
        data = {
            "type": "result",
            "subtype": "error",
            "duration_ms": 100,
            "duration_api_ms": 80,
            "is_error": True,
            "num_turns": 1,
            "session_id": "error_session"
        }
        result = parse_message(data)
        assert isinstance(result, ResultMessage)
        assert result.subtype == "error"
        assert result.is_error is True
        assert result.total_cost_usd is None
        assert result.usage is None
        assert result.result is None

    def test_parse_result_message_with_null_optionals(self):
        """Test parsing result message with null optional fields."""
        data = {
            "type": "result",
            "subtype": "cancelled",
            "duration_ms": 500,
            "duration_api_ms": 400,
            "is_error": False,
            "num_turns": 2,
            "session_id": "cancelled_session",
            "total_cost_usd": None,
            "usage": None,
            "result": None
        }
        result = parse_message(data)
        assert isinstance(result, ResultMessage)
        assert result.total_cost_usd is None
        assert result.usage is None
        assert result.result is None

    def test_parse_result_message_missing_required_field_raises_error(self):
        """Test that result message without required fields raises error."""
        data = {
            "type": "result",
            "subtype": "success",
            "duration_ms": 1000
            # Missing other required fields
        }
        with pytest.raises(MessageParseError) as exc_info:
            parse_message(data)
        assert "Missing required field in result message" in str(exc_info.value)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_parse_empty_dict_with_type(self):
        """Test parsing dict with only type field."""
        data = {"type": "invalid"}
        with pytest.raises(MessageParseError) as exc_info:
            parse_message(data)
        assert "Unknown message type: invalid" in str(exc_info.value)

    def test_parse_message_with_extra_fields(self):
        """Test that extra fields are preserved in system messages."""
        data = {
            "type": "system",
            "subtype": "custom",
            "extra_field_1": "value1",
            "extra_field_2": {"nested": "value2"}
        }
        result = parse_message(data)
        assert isinstance(result, SystemMessage)
        assert result.data["extra_field_1"] == "value1"
        assert result.data["extra_field_2"]["nested"] == "value2"

    def test_parse_user_message_empty_content_list(self):
        """Test parsing user message with empty content list."""
        data = {
            "type": "user",
            "message": {
                "role": "user",
                "content": []
            }
        }
        result = parse_message(data)
        assert isinstance(result, UserMessage)
        assert result.content == []

    def test_parse_assistant_message_empty_content_list(self):
        """Test parsing assistant message with empty content list."""
        data = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "model": "claude-3-sonnet",
                "content": []
            }
        }
        result = parse_message(data)
        assert isinstance(result, AssistantMessage)
        assert result.content == []
        assert result.model == "claude-3-sonnet"