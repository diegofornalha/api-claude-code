"""Comprehensive tests for subprocess CLI transport."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import anyio
import pytest
from anyio.streams.text import TextReceiveStream

from src._errors import CLIConnectionError, CLIJSONDecodeError, CLINotFoundError, ProcessError
from src._internal.transport.subprocess_cli import SubprocessCLITransport
from src.sdk_types import ClaudeCodeOptions


class TestCLIFinding:
    """Test CLI binary finding logic."""

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_find_cli_priority_locations(self, mock_is_file, mock_exists, mock_which):
        """Test that priority locations are checked first."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_which.return_value = None
        
        transport = SubprocessCLITransport("test", ClaudeCodeOptions())
        assert transport._cli_path == "/usr/local/bin/claude"

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.exists")
    @patch("shutil.which")
    def test_find_cli_with_shutil_which(self, mock_which, mock_exists, mock_is_file):
        """Test finding CLI using shutil.which."""
        # Make priority paths not exist
        mock_exists.return_value = False
        mock_is_file.return_value = False
        
        # Make shutil.which return custom path
        mock_which.return_value = "/custom/path/claude"
        
        transport = SubprocessCLITransport("test", ClaudeCodeOptions())
        assert transport._cli_path == "/custom/path/claude"

    @patch("shutil.which")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_find_cli_fallback_locations(self, mock_is_file, mock_exists, mock_which):
        """Test fallback locations when priority ones don't exist."""
        mock_which.return_value = None
        
        # Make priority locations not exist
        def exists_side_effect(self):
            path_str = str(self)
            if "/usr/local/bin/claude" in path_str or "/usr/bin/claude" in path_str:
                return False
            if "/.npm-global/bin/claude" in path_str:
                return True
            return False
        
        def is_file_side_effect(self):
            return "/.npm-global/bin/claude" in str(self)
        
        mock_exists.side_effect = exists_side_effect
        mock_is_file.side_effect = is_file_side_effect
        
        transport = SubprocessCLITransport("test", ClaudeCodeOptions())
        assert "/.npm-global/bin/claude" in transport._cli_path

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.exists")
    @patch("shutil.which")
    def test_find_cli_not_found_no_node(self, mock_which, mock_exists, mock_is_file):
        """Test error when CLI not found and Node.js not installed."""
        mock_which.return_value = None
        mock_exists.return_value = False
        mock_is_file.return_value = False
        
        with pytest.raises(CLINotFoundError) as exc_info:
            SubprocessCLITransport("test", ClaudeCodeOptions())
        
        assert "Claude Code requires Node.js" in str(exc_info.value)
        assert "https://nodejs.org/" in str(exc_info.value)

    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.exists")
    @patch("shutil.which")
    def test_find_cli_not_found_with_node(self, mock_which, mock_exists, mock_is_file):
        """Test error when CLI not found but Node.js is installed."""
        # Make all paths not exist
        mock_exists.return_value = False
        mock_is_file.return_value = False
        
        def which_side_effect(cmd):
            if cmd == "node":
                return "/usr/bin/node"
            return None
        
        mock_which.side_effect = which_side_effect
        
        with pytest.raises(CLINotFoundError) as exc_info:
            SubprocessCLITransport("test", ClaudeCodeOptions())
        
        assert "npm install -g @anthropic-ai/claude-code" in str(exc_info.value)

    def test_custom_cli_path(self):
        """Test using custom CLI path."""
        custom_path = "/custom/bin/claude"
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(), 
            cli_path=custom_path
        )
        assert transport._cli_path == custom_path

    def test_custom_cli_path_as_pathlib(self):
        """Test using custom CLI path as Path object."""
        custom_path = Path("/custom/bin/claude")
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(), 
            cli_path=custom_path
        )
        assert transport._cli_path == str(custom_path)


class TestCommandBuilding:
    """Test CLI command building with options."""

    def test_build_command_basic_string_prompt(self):
        """Test basic command building with string prompt."""
        transport = SubprocessCLITransport(
            "Hello Claude", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        cmd = transport._build_command()
        
        assert cmd[0] == "/usr/bin/claude"
        assert "--output-format" in cmd
        assert "stream-json" in cmd
        assert "--verbose" in cmd
        assert "--print" in cmd
        assert "Hello Claude" in cmd

    def test_build_command_with_system_prompt(self):
        """Test command with system prompt."""
        options = ClaudeCodeOptions(system_prompt="You are a helpful assistant")
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--system-prompt" in cmd
        assert "You are a helpful assistant" in cmd

    def test_build_command_with_append_system_prompt(self):
        """Test command with append system prompt."""
        options = ClaudeCodeOptions(append_system_prompt="Additional context")
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--append-system-prompt" in cmd
        assert "Additional context" in cmd

    def test_build_command_with_allowed_tools(self):
        """Test command with allowed tools."""
        options = ClaudeCodeOptions(allowed_tools=["tool1", "tool2"])
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--allowedTools" in cmd
        assert "tool1,tool2" in cmd

    def test_build_command_with_disallowed_tools(self):
        """Test command with disallowed tools."""
        options = ClaudeCodeOptions(disallowed_tools=["badtool1", "badtool2"])
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--disallowedTools" in cmd
        assert "badtool1,badtool2" in cmd

    def test_build_command_with_max_turns(self):
        """Test command with max turns."""
        options = ClaudeCodeOptions(max_turns=5)
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--max-turns" in cmd
        assert "5" in cmd

    def test_build_command_with_model(self):
        """Test command with model specification."""
        options = ClaudeCodeOptions(model="claude-3-opus")
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--model" in cmd
        assert "claude-3-opus" in cmd

    def test_build_command_with_permission_mode(self):
        """Test command with permission mode."""
        options = ClaudeCodeOptions(
            permission_mode="auto",
            permission_prompt_tool_name="file_editor"
        )
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--permission-mode" in cmd
        assert "auto" in cmd
        assert "--permission-prompt-tool" in cmd
        assert "file_editor" in cmd

    def test_build_command_with_continue_conversation(self):
        """Test command with continue conversation flag."""
        options = ClaudeCodeOptions(continue_conversation=True)
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--continue" in cmd

    def test_build_command_with_resume(self):
        """Test command with resume session."""
        options = ClaudeCodeOptions(resume="session_123")
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--resume" in cmd
        assert "session_123" in cmd

    def test_build_command_with_settings(self):
        """Test command with settings file."""
        options = ClaudeCodeOptions(settings="/path/to/settings.json")
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--settings" in cmd
        assert "/path/to/settings.json" in cmd

    def test_build_command_with_add_dirs(self):
        """Test command with additional directories."""
        options = ClaudeCodeOptions(add_dirs=["/dir1", Path("/dir2")])
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert cmd.count("--add-dir") == 2
        assert "/dir1" in cmd
        assert "/dir2" in cmd

    def test_build_command_with_mcp_servers_dict(self):
        """Test command with MCP servers as dict."""
        servers = {
            "server1": {"command": "cmd1"},
            "server2": {"command": "cmd2"}
        }
        options = ClaudeCodeOptions(mcp_servers=servers)
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--mcp-config" in cmd
        mcp_idx = cmd.index("--mcp-config")
        config_json = json.loads(cmd[mcp_idx + 1])
        assert "mcpServers" in config_json
        assert config_json["mcpServers"] == servers

    def test_build_command_with_mcp_servers_string(self):
        """Test command with MCP servers as string path."""
        options = ClaudeCodeOptions(mcp_servers="/path/to/mcp.json")
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--mcp-config" in cmd
        assert "/path/to/mcp.json" in cmd

    def test_build_command_with_extra_args(self):
        """Test command with extra arguments."""
        options = ClaudeCodeOptions(extra_args={
            "custom-flag": None,  # Boolean flag
            "custom-value": "test123"  # Flag with value
        })
        transport = SubprocessCLITransport("test", options, cli_path="/usr/bin/claude")
        cmd = transport._build_command()
        
        assert "--custom-flag" in cmd
        assert "--custom-value" in cmd
        assert "test123" in cmd

    async def test_build_command_streaming_mode(self):
        """Test command building for streaming mode."""
        async def stream():
            yield {"message": "test"}
        
        transport = SubprocessCLITransport(
            stream(), 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        cmd = transport._build_command()
        
        assert "--input-format" in cmd
        assert "stream-json" in cmd
        assert "--print" not in cmd


class TestConnection:
    """Test connection and disconnection."""

    @pytest.mark.asyncio
    @patch("anyio.open_process")
    async def test_connect_success(self, mock_open_process):
        """Test successful connection."""
        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.returncode = None
        mock_open_process.return_value = mock_process
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        await transport.connect()
        
        assert transport._process is not None
        assert mock_open_process.called

    @pytest.mark.asyncio
    @patch("anyio.open_process")
    async def test_connect_already_connected(self, mock_open_process):
        """Test connecting when already connected."""
        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        mock_process.stdin = MagicMock()
        mock_open_process.return_value = mock_process
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        await transport.connect()
        first_process = transport._process
        
        # Try to connect again
        await transport.connect()
        
        # Should not create new process
        assert transport._process is first_process
        assert mock_open_process.call_count == 1

    @pytest.mark.asyncio
    @patch("anyio.open_process")
    async def test_connect_cli_not_found(self, mock_open_process):
        """Test connection error when CLI not found."""
        mock_open_process.side_effect = FileNotFoundError()
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/nonexistent/claude"
        )
        
        with pytest.raises(CLINotFoundError):
            await transport.connect()

    @pytest.mark.asyncio
    @patch("anyio.open_process")
    @patch("pathlib.Path.exists")
    async def test_connect_working_dir_not_found(self, mock_exists, mock_open_process):
        """Test connection error when working directory doesn't exist."""
        mock_exists.return_value = False
        mock_open_process.side_effect = FileNotFoundError()
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(cwd="/nonexistent/dir"),
            cli_path="/usr/bin/claude"
        )
        
        with pytest.raises(CLIConnectionError) as exc_info:
            await transport.connect()
        
        assert "Working directory does not exist" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("anyio.open_process")
    async def test_connect_generic_error(self, mock_open_process):
        """Test connection with generic error."""
        mock_open_process.side_effect = Exception("Test error")
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        with pytest.raises(CLIConnectionError) as exc_info:
            await transport.connect()
        
        assert "Failed to start Claude Code" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("anyio.open_process")
    async def test_disconnect_running_process(self, mock_open_process):
        """Test disconnecting a running process."""
        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.returncode = None
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()
        mock_open_process.return_value = mock_process
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        await transport.connect()
        await transport.disconnect()
        
        assert transport._process is None
        assert mock_process.terminate.called

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self):
        """Test disconnecting when not connected."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        # Should not raise error
        await transport.disconnect()
        assert transport._process is None

    @pytest.mark.asyncio
    @patch("anyio.open_process")
    async def test_disconnect_with_timeout(self, mock_open_process):
        """Test disconnecting with timeout and kill."""
        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.returncode = None
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        
        # Simulate timeout on wait
        async def wait_timeout():
            raise TimeoutError()
        mock_process.wait = wait_timeout
        
        mock_open_process.return_value = mock_process
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        await transport.connect()
        await transport.disconnect()
        
        assert mock_process.terminate.called
        assert mock_process.kill.called


class TestMessageReceiving:
    """Test receiving messages from CLI."""

    @pytest.mark.asyncio
    async def test_receive_single_message(self):
        """Test receiving a single JSON message."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        # Mock the process and stdout stream
        transport._process = AsyncMock()
        transport._process.returncode = None
        transport._process.wait = AsyncMock(return_value=0)
        
        # Create mock stdout stream
        async def mock_stdout():
            yield '{"type": "test", "data": "hello"}\n'
        
        transport._stdout_stream = mock_stdout()
        
        messages = []
        async for msg in transport.receive_messages():
            messages.append(msg)
        
        assert len(messages) == 1
        assert messages[0]["type"] == "test"
        assert messages[0]["data"] == "hello"

    @pytest.mark.asyncio
    async def test_receive_multiple_messages(self):
        """Test receiving multiple JSON messages."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        transport._process = AsyncMock()
        transport._process.returncode = None
        transport._process.wait = AsyncMock(return_value=0)
        
        async def mock_stdout():
            yield '{"type": "message1", "id": 1}\n'
            yield '{"type": "message2", "id": 2}\n'
            yield '{"type": "message3", "id": 3}\n'
        
        transport._stdout_stream = mock_stdout()
        
        messages = []
        async for msg in transport.receive_messages():
            messages.append(msg)
        
        assert len(messages) == 3
        assert messages[0]["id"] == 1
        assert messages[2]["id"] == 3

    @pytest.mark.asyncio
    async def test_receive_partial_json(self):
        """Test handling partial JSON that needs accumulation."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        transport._process = AsyncMock()
        transport._process.returncode = None
        transport._process.wait = AsyncMock(return_value=0)
        
        async def mock_stdout():
            # Send JSON in parts
            yield '{"type": "test",'
            yield ' "data": '
            yield '"complete"}\n'
        
        transport._stdout_stream = mock_stdout()
        
        messages = []
        async for msg in transport.receive_messages():
            messages.append(msg)
        
        assert len(messages) == 1
        assert messages[0]["type"] == "test"
        assert messages[0]["data"] == "complete"

    @pytest.mark.asyncio
    async def test_receive_control_response(self):
        """Test filtering control response messages."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        transport._process = AsyncMock()
        transport._process.returncode = None
        transport._process.wait = AsyncMock(return_value=0)
        
        async def mock_stdout():
            yield '{"type": "message1"}\n'
            yield '{"type": "control_response", "response": {"request_id": "req_123"}}\n'
            yield '{"type": "message2"}\n'
        
        transport._stdout_stream = mock_stdout()
        
        messages = []
        async for msg in transport.receive_messages():
            messages.append(msg)
        
        # Control response should be filtered out
        assert len(messages) == 2
        assert messages[0]["type"] == "message1"
        assert messages[1]["type"] == "message2"
        
        # Control response should be stored
        assert "req_123" in transport._pending_control_responses

    @pytest.mark.asyncio
    async def test_receive_empty_lines(self):
        """Test handling empty lines in output."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        transport._process = AsyncMock()
        transport._process.returncode = None
        transport._process.wait = AsyncMock(return_value=0)
        
        async def mock_stdout():
            yield '\n'
            yield '{"type": "message"}\n'
            yield '  \n'
            yield '\n'
        
        transport._stdout_stream = mock_stdout()
        
        messages = []
        async for msg in transport.receive_messages():
            messages.append(msg)
        
        assert len(messages) == 1
        assert messages[0]["type"] == "message"

    @pytest.mark.asyncio
    async def test_receive_buffer_overflow(self):
        """Test error on buffer overflow."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        transport._process = AsyncMock()
        transport._process.returncode = None
        
        # Create very large incomplete JSON
        large_json = '{"data": "' + ('x' * (1024 * 1024 + 1))
        
        async def mock_stdout():
            yield large_json
        
        transport._stdout_stream = mock_stdout()
        
        with pytest.raises(CLIJSONDecodeError) as exc_info:
            async for _ in transport.receive_messages():
                pass
        
        assert "exceeded maximum buffer size" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_receive_process_error_nonzero_exit(self):
        """Test process error with non-zero exit code."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        transport._process = AsyncMock()
        transport._process.returncode = None
        transport._process.wait = AsyncMock(return_value=1)
        
        # Mock stderr file
        transport._stderr_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        transport._stderr_file.write("Error: Something went wrong\n")
        transport._stderr_file.flush()
        
        async def mock_stdout():
            return
            yield  # Empty generator
        
        transport._stdout_stream = mock_stdout()
        
        with pytest.raises(ProcessError) as exc_info:
            async for _ in transport.receive_messages():
                pass
        
        assert exc_info.value.exit_code == 1
        assert "Something went wrong" in exc_info.value.stderr
        
        # Cleanup
        Path(transport._stderr_file.name).unlink()

    @pytest.mark.asyncio
    async def test_receive_not_connected(self):
        """Test receiving when not connected."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        with pytest.raises(CLIConnectionError) as exc_info:
            async for _ in transport.receive_messages():
                pass
        
        assert "Not connected" in str(exc_info.value)


class TestStreamingMode:
    """Test streaming mode specific functionality."""

    @pytest.mark.asyncio
    @patch("anyio.open_process")
    @patch("anyio.create_task_group")
    async def test_streaming_mode_connect(self, mock_task_group, mock_open_process):
        """Test connecting in streaming mode."""
        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.returncode = None
        mock_open_process.return_value = mock_process
        
        mock_tg = AsyncMock()
        mock_task_group.return_value = mock_tg
        
        async def stream():
            yield {"message": "test"}
        
        transport = SubprocessCLITransport(
            stream(), 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        await transport.connect()
        
        assert transport._stdin_stream is not None
        assert transport._task_group is not None
        assert mock_tg.__aenter__.called

    @pytest.mark.asyncio
    async def test_send_request_streaming_mode(self):
        """Test sending additional requests in streaming mode."""
        async def stream():
            yield {"initial": "message"}
        
        transport = SubprocessCLITransport(
            stream(), 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        # Mock stdin stream
        mock_stdin = AsyncMock()
        transport._stdin_stream = mock_stdin
        
        messages = [
            {"type": "user", "message": {"role": "user", "content": "Hello"}},
            {"type": "user", "message": {"role": "user", "content": "World"}}
        ]
        
        await transport.send_request(messages, {"session_id": "test_session"})
        
        assert mock_stdin.send.call_count == 2

    @pytest.mark.asyncio
    async def test_send_request_not_streaming_mode(self):
        """Test error when trying to send request in non-streaming mode."""
        transport = SubprocessCLITransport(
            "string prompt", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        with pytest.raises(CLIConnectionError) as exc_info:
            await transport.send_request([], {})
        
        assert "only works in streaming mode" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_request_no_stdin(self):
        """Test error when stdin not available."""
        async def stream():
            yield {"message": "test"}
        
        transport = SubprocessCLITransport(
            stream(), 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        with pytest.raises(CLIConnectionError) as exc_info:
            await transport.send_request([], {})
        
        assert "stdin not available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_interrupt_streaming_mode(self):
        """Test sending interrupt in streaming mode."""
        async def stream():
            yield {"message": "test"}
        
        transport = SubprocessCLITransport(
            stream(), 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        mock_stdin = AsyncMock()
        transport._stdin_stream = mock_stdin
        transport._request_counter = 0
        
        await transport.interrupt()
        
        # Check that control request was sent
        call_args = mock_stdin.send.call_args[0][0]
        request = json.loads(call_args.strip())
        assert request["type"] == "control_request"
        assert request["request"]["subtype"] == "interrupt"

    @pytest.mark.asyncio
    async def test_interrupt_not_streaming_mode(self):
        """Test error when trying to interrupt in non-streaming mode."""
        transport = SubprocessCLITransport(
            "string prompt", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        with pytest.raises(CLIConnectionError) as exc_info:
            await transport.interrupt()
        
        assert "requires streaming mode" in str(exc_info.value)


class TestUtilityMethods:
    """Test utility methods."""

    def test_is_connected_with_running_process(self):
        """Test is_connected with running process."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        mock_process = Mock()
        mock_process.returncode = None
        transport._process = mock_process
        
        assert transport.is_connected() is True

    def test_is_connected_with_terminated_process(self):
        """Test is_connected with terminated process."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        mock_process = Mock()
        mock_process.returncode = 0
        transport._process = mock_process
        
        assert transport.is_connected() is False

    def test_is_connected_no_process(self):
        """Test is_connected with no process."""
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        assert transport.is_connected() is False

    @pytest.mark.asyncio
    async def test_stream_to_stdin(self):
        """Test streaming messages to stdin."""
        async def message_stream():
            yield {"message": "1"}
            yield {"message": "2"}
            yield {"message": "3"}
        
        transport = SubprocessCLITransport(
            message_stream(), 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        mock_stdin = AsyncMock()
        transport._stdin_stream = mock_stdin
        
        await transport._stream_to_stdin()
        
        assert mock_stdin.send.call_count == 3

    @pytest.mark.asyncio
    async def test_stream_to_stdin_with_close_after(self):
        """Test streaming with close_stdin_after_prompt."""
        async def message_stream():
            yield {"message": "test"}
        
        transport = SubprocessCLITransport(
            message_stream(), 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude",
            close_stdin_after_prompt=True
        )
        
        mock_stdin = AsyncMock()
        transport._stdin_stream = mock_stdin
        
        await transport._stream_to_stdin()
        
        assert mock_stdin.send.called
        assert mock_stdin.aclose.called
        assert transport._stdin_stream is None