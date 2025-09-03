#!/usr/bin/env python3
"""
Teste de persistência de sessões do chat interativo.
Verifica a criação e leitura de sessões no formato JSON usado pelo wrapper CLI.
"""

import json
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
import pytest
import sys
import os

# Adiciona o diretório pai ao path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src import AssistantMessage, TextBlock, ResultMessage

class TestSessionPersistence:
    """Testa persistência de sessões no formato do chat interativo."""
    
    def create_session_entry(self, message_type="user", content="Test message", session_id=None):
        """Cria uma entrada de sessão no formato correto."""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        entry = {
            "parentUuid": None,
            "isSidechain": False,
            "userType": "external",
            "cwd": "/home/suthub/.claude/api-claude-code-app/claude-code-sdk-python/wrappers_cli",
            "sessionId": session_id,
            "version": "1.0.102",
            "gitBranch": "main",
            "type": message_type,
            "uuid": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if message_type == "user":
            entry["message"] = {
                "role": "user",
                "content": content
            }
        elif message_type == "assistant":
            entry["message"] = {
                "id": f"msg_{uuid.uuid4().hex[:24]}",
                "type": "message",
                "role": "assistant",
                "model": "claude-opus-4-1-20250805",
                "content": [{"type": "text", "text": content}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "service_tier": "standard"
                }
            }
            entry["requestId"] = f"req_{uuid.uuid4().hex[:24]}"
            
        return entry
    
    def test_create_session_file(self):
        """Testa criação de arquivo de sessão."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_id = str(uuid.uuid4())
            session_path = Path(tmpdir) / f"{session_id}.jsonl"
            
            # Cria mensagens de teste
            messages = [
                self.create_session_entry("user", "Olá Claude", session_id),
                self.create_session_entry("assistant", "Olá! Como posso ajudar?", session_id),
                self.create_session_entry("user", "Me ajude com Python", session_id),
                self.create_session_entry("assistant", "Claro! O que você precisa em Python?", session_id)
            ]
            
            # Escreve as mensagens no arquivo
            with open(session_path, 'w') as f:
                for msg in messages:
                    f.write(json.dumps(msg, ensure_ascii=False) + '\n')
            
            # Verifica que o arquivo foi criado
            assert session_path.exists()
            
            # Lê e verifica o conteúdo
            with open(session_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 4
            
            # Verifica cada linha
            for i, line in enumerate(lines):
                data = json.loads(line)
                assert data["sessionId"] == session_id
                assert data["type"] in ["user", "assistant"]
                assert "message" in data
                assert "timestamp" in data
                assert "uuid" in data
    
    def test_read_existing_session(self):
        """Testa leitura de sessão existente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_id = str(uuid.uuid4())
            session_path = Path(tmpdir) / f"{session_id}.jsonl"
            
            # Cria uma sessão de teste
            test_messages = []
            with open(session_path, 'w') as f:
                for i in range(3):
                    user_msg = self.create_session_entry("user", f"Mensagem {i}", session_id)
                    asst_msg = self.create_session_entry("assistant", f"Resposta {i}", session_id)
                    
                    f.write(json.dumps(user_msg, ensure_ascii=False) + '\n')
                    f.write(json.dumps(asst_msg, ensure_ascii=False) + '\n')
                    
                    test_messages.extend([user_msg, asst_msg])
            
            # Lê a sessão
            loaded_messages = []
            with open(session_path, 'r') as f:
                for line in f:
                    loaded_messages.append(json.loads(line))
            
            # Verifica o conteúdo
            assert len(loaded_messages) == 6
            
            # Verifica ordem e conteúdo
            for i in range(0, 6, 2):
                user_msg = loaded_messages[i]
                asst_msg = loaded_messages[i + 1]
                
                assert user_msg["type"] == "user"
                assert asst_msg["type"] == "assistant"
                assert user_msg["sessionId"] == session_id
                assert asst_msg["sessionId"] == session_id
    
    def test_append_to_session(self):
        """Testa adicionar mensagens a uma sessão existente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_id = str(uuid.uuid4())
            session_path = Path(tmpdir) / f"{session_id}.jsonl"
            
            # Cria sessão inicial
            initial_msg = self.create_session_entry("user", "Primeira mensagem", session_id)
            with open(session_path, 'w') as f:
                f.write(json.dumps(initial_msg, ensure_ascii=False) + '\n')
            
            # Adiciona novas mensagens
            new_messages = [
                self.create_session_entry("assistant", "Resposta 1", session_id),
                self.create_session_entry("user", "Segunda mensagem", session_id),
                self.create_session_entry("assistant", "Resposta 2", session_id)
            ]
            
            with open(session_path, 'a') as f:
                for msg in new_messages:
                    f.write(json.dumps(msg, ensure_ascii=False) + '\n')
            
            # Verifica todas as mensagens
            with open(session_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 4
            
            # Verifica que a primeira mensagem ainda está lá
            first_msg = json.loads(lines[0])
            assert first_msg["message"]["content"] == "Primeira mensagem"
            
            # Verifica as novas mensagens
            last_msg = json.loads(lines[-1])
            assert last_msg["type"] == "assistant"
            assert last_msg["message"]["content"][0]["text"] == "Resposta 2"
    
    def test_session_with_parent_uuid(self):
        """Testa criação de mensagens com parentUuid (respostas encadeadas)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_id = str(uuid.uuid4())
            session_path = Path(tmpdir) / f"{session_id}.jsonl"
            
            # Cria primeira mensagem
            first_msg = self.create_session_entry("user", "Primeira", session_id)
            first_uuid = first_msg["uuid"]
            
            # Cria resposta com parent
            response = self.create_session_entry("assistant", "Resposta", session_id)
            response["parentUuid"] = first_uuid
            
            # Escreve as mensagens
            with open(session_path, 'w') as f:
                f.write(json.dumps(first_msg, ensure_ascii=False) + '\n')
                f.write(json.dumps(response, ensure_ascii=False) + '\n')
            
            # Verifica o encadeamento
            with open(session_path, 'r') as f:
                lines = f.readlines()
            
            msg1 = json.loads(lines[0])
            msg2 = json.loads(lines[1])
            
            assert msg1["parentUuid"] is None
            assert msg2["parentUuid"] == first_uuid
    
    def test_session_directory_structure(self):
        """Testa estrutura de diretórios compatível com o viewer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Cria estrutura de diretórios similar ao Claude
            claude_dir = Path(tmpdir) / ".claude"
            projects_dir = claude_dir / "projects"
            project_dir = projects_dir / "-home-suthub--claude-api-claude-code-app-claude-code-sdk-python-wrappers-cli"
            
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Cria múltiplas sessões
            session_ids = [str(uuid.uuid4()) for _ in range(3)]
            
            for session_id in session_ids:
                session_path = project_dir / f"{session_id}.jsonl"
                
                msg = self.create_session_entry("user", f"Teste {session_id[:8]}", session_id)
                with open(session_path, 'w') as f:
                    f.write(json.dumps(msg, ensure_ascii=False) + '\n')
            
            # Verifica que todos os arquivos foram criados
            session_files = list(project_dir.glob("*.jsonl"))
            assert len(session_files) == 3
            
            # Verifica que os IDs correspondem
            found_ids = {f.stem for f in session_files}
            expected_ids = set(session_ids)
            assert found_ids == expected_ids

if __name__ == "__main__":
    pytest.main([__file__, "-v"])