"""Complete tests for error classes to achieve 100% coverage."""

import pytest
from src._errors import (
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    ClaudeSDKError,
    MessageParseError,
    ProcessError,
)


class TestClaudeSDKErrorComplete:
    """Complete tests for ClaudeSDKError base class."""

    def test_sdk_error_with_message(self):
        """Test ClaudeSDKError with message."""
        error = ClaudeSDKError("Test error message")
        assert str(error) == "Test error message"
        assert error.args == ("Test error message",)

    def test_sdk_error_inheritance(self):
        """Test that ClaudeSDKError inherits from Exception."""
        error = ClaudeSDKError("Test")
        assert isinstance(error, Exception)

    def test_sdk_error_empty_message(self):
        """Test ClaudeSDKError with empty message."""
        error = ClaudeSDKError("")
        assert str(error) == ""

    def test_sdk_error_with_special_characters(self):
        """Test ClaudeSDKError with special characters."""
        msg = "Error: ñ, ü, 中文, 🚀, \n\t"
        error = ClaudeSDKError(msg)
        assert str(error) == msg


class TestCLINotFoundErrorComplete:
    """Complete tests for CLINotFoundError."""

    def test_cli_not_found_default(self):
        """Test CLINotFoundError with default message."""
        error = CLINotFoundError()
        assert "Claude Code not found" in str(error)

    def test_cli_not_found_custom_message(self):
        """Test CLINotFoundError with custom message."""
        msg = "Custom CLI not found at /usr/bin/claude"
        error = CLINotFoundError(msg)
        assert str(error) == msg

    def test_cli_not_found_inheritance(self):
        """Test CLINotFoundError inheritance chain."""
        error = CLINotFoundError()
        assert isinstance(error, ClaudeSDKError)
        assert isinstance(error, Exception)


class TestCLIConnectionErrorComplete:
    """Complete tests for CLIConnectionError."""

    def test_cli_connection_default(self):
        """Test CLIConnectionError with default message."""
        error = CLIConnectionError()
        # CLIConnectionError doesn't have a default message, just test instantiation
        assert isinstance(error, CLIConnectionError)

    def test_cli_connection_custom_message(self):
        """Test CLIConnectionError with custom message."""
        msg = "Connection timeout after 30 seconds"
        error = CLIConnectionError(msg)
        assert str(error) == msg

    def test_cli_connection_inheritance(self):
        """Test CLIConnectionError inheritance."""
        error = CLIConnectionError()
        assert isinstance(error, ClaudeSDKError)


class TestProcessErrorComplete:
    """Complete tests for ProcessError."""

    def test_process_error_basic(self):
        """Test ProcessError with basic parameters."""
        error = ProcessError("Process failed", exit_code=1)
        assert "Process failed" in str(error)
        assert "exit code: 1" in str(error)
        assert error.exit_code == 1
        assert error.stderr is None

    def test_process_error_with_stderr(self):
        """Test ProcessError with stderr output."""
        stderr_output = "Error: Invalid argument\nUsage: command [options]"
        error = ProcessError("Command failed", exit_code=2, stderr=stderr_output)
        assert "Command failed" in str(error)
        assert "exit code: 2" in str(error)
        assert "Error output:" in str(error)
        assert error.exit_code == 2
        assert error.stderr == stderr_output

    def test_process_error_zero_exit_code(self):
        """Test ProcessError with zero exit code."""
        error = ProcessError("Unexpected termination", exit_code=0)
        assert error.exit_code == 0

    def test_process_error_negative_exit_code(self):
        """Test ProcessError with negative exit code (signal)."""
        error = ProcessError("Killed by signal", exit_code=-9)
        assert error.exit_code == -9

    def test_process_error_inheritance(self):
        """Test ProcessError inheritance."""
        error = ProcessError("Test", exit_code=1)
        assert isinstance(error, ClaudeSDKError)

    def test_process_error_attributes_access(self):
        """Test accessing ProcessError attributes."""
        error = ProcessError("Failed", exit_code=127, stderr="Command not found")
        assert hasattr(error, "exit_code")
        assert hasattr(error, "stderr")
        assert error.exit_code == 127
        assert error.stderr == "Command not found"


class TestCLIJSONDecodeErrorComplete:
    """Complete tests for CLIJSONDecodeError."""

    def test_json_decode_error_basic(self):
        """Test CLIJSONDecodeError with basic parameters."""
        original = ValueError("Invalid JSON")
        error = CLIJSONDecodeError('{"invalid": json}', original)
        assert "Failed to decode JSON" in str(error)
        assert error.original_error is original
        assert error.line == '{"invalid": json}'

    def test_json_decode_error_with_json_decode_error(self):
        """Test CLIJSONDecodeError with actual JSONDecodeError."""
        import json
        
        try:
            json.loads("{invalid json}")
        except json.JSONDecodeError as e:
            error = CLIJSONDecodeError("{invalid json}", e)
            assert error.original_error is e
            assert isinstance(error.original_error, json.JSONDecodeError)

    def test_json_decode_error_inheritance(self):
        """Test CLIJSONDecodeError inheritance."""
        error = CLIJSONDecodeError("Test line", ValueError())
        assert isinstance(error, ClaudeSDKError)

    def test_json_decode_error_attribute_access(self):
        """Test accessing original_error attribute."""
        original = RuntimeError("Original error")
        error = CLIJSONDecodeError("Line content here", original)
        assert hasattr(error, "original_error")
        assert hasattr(error, "line")
        assert error.original_error is original
        assert error.line == "Line content here"


class TestMessageParseErrorComplete:
    """Complete tests for MessageParseError."""

    def test_message_parse_error_with_dict_data(self):
        """Test MessageParseError with dictionary data."""
        data = {"type": "unknown", "content": "test"}
        error = MessageParseError("Unknown message type", data)
        assert str(error) == "Unknown message type"
        assert error.data == data

    def test_message_parse_error_with_string_data(self):
        """Test MessageParseError with string data."""
        data = "invalid message format"
        error = MessageParseError("Invalid format", data)
        assert error.data == data

    def test_message_parse_error_with_none_data(self):
        """Test MessageParseError with None data."""
        error = MessageParseError("No data provided", None)
        assert error.data is None

    def test_message_parse_error_with_complex_data(self):
        """Test MessageParseError with complex nested data."""
        data = {
            "type": "complex",
            "nested": {
                "level1": {
                    "level2": ["item1", "item2"],
                    "value": 42
                }
            },
            "list": [1, 2, 3]
        }
        error = MessageParseError("Complex parse error", data)
        assert error.data == data
        assert error.data["nested"]["level1"]["value"] == 42

    def test_message_parse_error_inheritance(self):
        """Test MessageParseError inheritance."""
        error = MessageParseError("Test", {})
        assert isinstance(error, ClaudeSDKError)

    def test_message_parse_error_attribute_access(self):
        """Test accessing data attribute."""
        data = {"key": "value"}
        error = MessageParseError("Error", data)
        assert hasattr(error, "data")
        assert error.data is data


class TestErrorRaisingAndCatching:
    """Test raising and catching errors."""

    def test_raise_and_catch_sdk_error(self):
        """Test raising and catching ClaudeSDKError."""
        with pytest.raises(ClaudeSDKError) as exc_info:
            raise ClaudeSDKError("Test error")
        assert "Test error" in str(exc_info.value)

    def test_catch_specific_error_type(self):
        """Test catching specific error types."""
        try:
            raise ProcessError("Process failed", exit_code=1, stderr="Error output")
        except ProcessError as e:
            assert e.exit_code == 1
            assert e.stderr == "Error output"
        except ClaudeSDKError:
            pytest.fail("Should catch ProcessError specifically")

    def test_catch_base_error(self):
        """Test catching base ClaudeSDKError for all subtypes."""
        errors = [
            CLINotFoundError("Not found"),
            CLIConnectionError("Connection failed"),
            ProcessError("Process error", exit_code=1),
            CLIJSONDecodeError("JSON line", ValueError()),
            MessageParseError("Parse error", {})
        ]
        
        for error in errors:
            try:
                raise error
            except ClaudeSDKError as e:
                assert isinstance(e, ClaudeSDKError)
            except Exception:
                pytest.fail(f"Should catch {type(error).__name__} as ClaudeSDKError")

    def test_error_chain_with_cause(self):
        """Test error chaining with __cause__."""
        original = ValueError("Original error")
        try:
            try:
                raise original
            except ValueError as e:
                raise CLIJSONDecodeError("JSON line content", e) from e
        except CLIJSONDecodeError as e:
            assert e.__cause__ is original
            assert e.original_error is original


class TestErrorStringRepresentations:
    """Test string representations of errors."""

    def test_error_repr(self):
        """Test __repr__ of error classes."""
        error = ClaudeSDKError("Test message")
        repr_str = repr(error)
        assert "ClaudeSDKError" in repr_str
        assert "Test message" in repr_str

    def test_process_error_detailed_string(self):
        """Test detailed string representation of ProcessError."""
        error = ProcessError(
            "Command failed",
            exit_code=127,
            stderr="bash: command: not found"
        )
        # Test that all information is accessible
        error_str = str(error)
        assert "Command failed" in error_str
        assert "exit code: 127" in error_str
        assert "Error output:" in error_str
        assert "not found" in error_str
        assert error.exit_code == 127
        assert "not found" in error.stderr

    def test_json_decode_error_detailed_string(self):
        """Test detailed string representation of CLIJSONDecodeError."""
        original = ValueError("Expecting ',' delimiter")
        error = CLIJSONDecodeError(
            '{"test": "invalid json line that is very long and will be truncated after 100 characters for display purposes in the error message"}',
            original
        )
        assert "Failed to decode JSON" in str(error)
        assert str(error.original_error) == "Expecting ',' delimiter"


class TestErrorComparison:
    """Test error comparison and equality."""

    def test_error_equality(self):
        """Test that errors with same message are not equal."""
        error1 = ClaudeSDKError("Same message")
        error2 = ClaudeSDKError("Same message")
        # Different instances should not be equal
        assert error1 is not error2
        # But messages should be the same
        assert str(error1) == str(error2)

    def test_error_type_checking(self):
        """Test type checking with isinstance."""
        error = ProcessError("Test", exit_code=1)
        assert isinstance(error, ProcessError)
        assert isinstance(error, ClaudeSDKError)
        assert isinstance(error, Exception)
        assert not isinstance(error, CLINotFoundError)