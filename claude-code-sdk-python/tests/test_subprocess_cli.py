"""Comprehensive tests for subprocess CLI transport."""

import asyncio
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
    @patch.object(Path, 'is_file', autospec=True)
    @patch.object(Path, 'exists', autospec=True)
    def test_find_cli_fallback_locations(self, mock_exists, mock_is_file, mock_which):
        """Test fallback locations when priority ones don't exist."""
        mock_which.return_value = None
        
        def exists_side_effect(path_instance):
            path_str = str(path_instance)
            # Priority locations don't exist
            if "/usr/local/bin/claude" in path_str:
                return False
            if "/usr/bin/claude" in path_str:
                return False
            # Fallback location exists
            if "/.npm-global/bin/claude" in path_str:
                return True
            return False
        
        def is_file_side_effect(path_instance):
            path_str = str(path_instance)
            # Only the fallback location is a file
            if "/.npm-global/bin/claude" in path_str:
                return True
            return False
        
        # With autospec=True, the first parameter is the instance
        mock_exists.side_effect = exists_side_effect
        mock_is_file.side_effect = is_file_side_effect
        
        transport = SubprocessCLITransport("test", ClaudeCodeOptions())
        
        # Verify that the fallback location was found
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
    
    def test_build_command_streaming_mode(self):
        """Test command building for streaming mode (should be synchronous)."""
        async def stream():
            yield {"message": "test"}
        
        transport = SubprocessCLITransport(
            stream(), 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        # _build_command é síncrono, não assíncrono
        cmd = transport._build_command()
        
        # Verifica flags específicos do streaming mode
        assert "--input-format" in cmd
        assert "stream-json" in cmd
        # Em streaming mode, não deve ter --print flag
        assert "--print" not in cmd
        # Mas deve ter --output-format
        assert "--output-format" in cmd
        assert "stream-json" in cmd



class TestConnection:
    """Test connection and disconnection."""


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
    @patch("tempfile.NamedTemporaryFile")
    async def test_connect_success(self, mock_tempfile, mock_open_process):
        """Test successful connection."""
        # Configure mock process
        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        
        # Configure stdin with async close method
        mock_stdin = MagicMock()
        mock_stdin.aclose = AsyncMock()
        mock_process.stdin = mock_stdin
        
        mock_process.stderr = MagicMock()
        mock_process.returncode = None
        mock_open_process.return_value = mock_process
        
        # Configure mock temp file for stderr
        mock_stderr_file = MagicMock()
        mock_stderr_file.name = "/tmp/stderr.txt"
        mock_tempfile.return_value = mock_stderr_file
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        await transport.connect()
        
        # Verify connection was established
        assert transport._process is not None
        assert transport._process == mock_process
        assert mock_open_process.called
        
        # Verify stderr file was created
        assert transport._stderr_file is not None
        
        # Verify stdin was closed (not streaming mode)
        assert mock_stdin.aclose.called
    
    @pytest.mark.asyncio
    @patch("anyio.open_process")
    @patch("tempfile.NamedTemporaryFile")
    async def test_connect_already_connected(self, mock_tempfile, mock_open_process):
        """Test connecting when already connected."""
        # Configure first mock process
        first_process = AsyncMock()
        first_process.stdout = MagicMock()
        
        # Configure stdin with async close for first process
        first_stdin = MagicMock()
        first_stdin.aclose = AsyncMock()
        first_process.stdin = first_stdin
        
        first_process.stderr = MagicMock()
        first_process.returncode = None
        first_process.terminate = MagicMock()
        first_process.wait = AsyncMock()
        
        # Configure second mock process
        second_process = AsyncMock()
        second_process.stdout = MagicMock()
        
        # Configure stdin with async close for second process
        second_stdin = MagicMock()
        second_stdin.aclose = AsyncMock()
        second_process.stdin = second_stdin
        
        second_process.stderr = MagicMock()
        second_process.returncode = None
        
        mock_open_process.side_effect = [first_process, second_process]
        
        # Configure mock temp file
        mock_stderr_file = MagicMock()
        mock_stderr_file.name = "/tmp/stderr.txt"
        mock_tempfile.return_value = mock_stderr_file
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        # First connection
        await transport.connect()
        assert transport._process == first_process
        
        # Second connection should do nothing (already connected)
        await transport.connect()
        
        # Verify process was NOT terminated (still same process)
        assert not first_process.terminate.called
        # Verify still using first process
        assert transport._process == first_process
        # Open process should only be called once
        assert mock_open_process.call_count == 1

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
    @patch("tempfile.NamedTemporaryFile")
    async def test_disconnect_running_process(self, mock_tempfile, mock_open_process):
        """Test disconnecting a running process."""
        # Configure mock process
        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        
        # Configure stdin with async close
        mock_stdin = MagicMock()
        mock_stdin.aclose = AsyncMock()
        mock_process.stdin = mock_stdin
        
        mock_process.stderr = MagicMock()
        mock_process.returncode = None
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()
        mock_open_process.return_value = mock_process
        
        # Configure mock temp file
        mock_stderr_file = MagicMock()
        mock_stderr_file.name = "/tmp/stderr.txt"
        mock_stderr_file.close = MagicMock()
        mock_tempfile.return_value = mock_stderr_file
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        # Connect first
        await transport.connect()
        assert transport._process is not None
        
        # Then disconnect
        await transport.disconnect()
        
        # Verify process was terminated gracefully
        assert mock_process.terminate.called
        assert mock_process.wait.called
        # Process should be cleared
        assert transport._process is None
        # Stderr file should be closed
        assert mock_stderr_file.close.called
    
    @pytest.mark.asyncio
    @patch("anyio.open_process")
    @patch("tempfile.NamedTemporaryFile")
    @patch("anyio.sleep")
    async def test_disconnect_with_timeout(self, mock_sleep, mock_tempfile, mock_open_process):
        """Test disconnecting with timeout and kill."""
        # Configure mock process
        mock_process = AsyncMock()
        mock_process.stdout = MagicMock()
        
        # Configure stdin with async close
        mock_stdin = MagicMock()
        mock_stdin.aclose = AsyncMock()
        mock_process.stdin = mock_stdin
        
        mock_process.stderr = MagicMock()
        mock_process.returncode = None
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        
        # Simulate timeout on wait by raising TimeoutError
        wait_call_count = 0
        async def wait_with_timeout():
            nonlocal wait_call_count
            wait_call_count += 1
            if wait_call_count == 1:
                # First call times out
                raise asyncio.TimeoutError()
            # Second call succeeds (after kill)
            return 0
        
        mock_process.wait = wait_with_timeout
        mock_open_process.return_value = mock_process
        
        # Configure mock temp file
        mock_stderr_file = MagicMock()
        mock_stderr_file.name = "/tmp/stderr.txt"
        mock_stderr_file.close = MagicMock()
        mock_tempfile.return_value = mock_stderr_file
        
        # Mock sleep to avoid actual waiting
        mock_sleep.return_value = None
        
        transport = SubprocessCLITransport(
            "test", 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        # Connect first
        await transport.connect()
        
        # Then disconnect (should timeout and kill)
        await transport.disconnect()
        
        # Verify terminate was tried first
        assert mock_process.terminate.called
        # Verify kill was called after timeout
        assert mock_process.kill.called
        # Process should be cleared
        assert transport._process is None



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
    @pytest.mark.skip(reason="Mock configuration needs refactoring")
    async def test_interrupt_streaming_mode(self):
        """Test sending interrupt in streaming mode."""
        async def stream():
            yield {"message": "test"}
        
        transport = SubprocessCLITransport(
            stream(), 
            ClaudeCodeOptions(),
            cli_path="/usr/bin/claude"
        )
        
        # Configure mock stdin stream properly
        mock_stdin = AsyncMock()
        mock_stdin.send = AsyncMock()
        transport._stdin_stream = mock_stdin
        
        # Initialize request counter
        transport._request_counter = 0
        
        # Send interrupt
        request_id = await transport.interrupt()
        
        # Verify control request was sent
        assert mock_stdin.send.called
        call_args = mock_stdin.send.call_args[0][0]
        
        # Parse the sent JSON
        request_data = json.loads(call_args.strip())
        assert request_data["type"] == "control_request"
        assert request_data["request"]["subtype"] == "interrupt"
        assert "request_id" in request_data["request"]
        
        # Verify request ID was returned
        assert request_id is not None
        assert request_id.startswith("req_")
    
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