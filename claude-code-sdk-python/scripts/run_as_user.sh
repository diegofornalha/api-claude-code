#!/bin/bash

# Script para executar SDK como usuário codable
su - codable -c "cd /home/codable/terminal/claude-code-sdk-python && source venv/bin/activate && PYTHONPATH=. python3 examples/streaming_mode_trio.py basic"