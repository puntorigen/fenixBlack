#!/bin/sh
echo "OpenAI API key not provided. Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh
sleep 10
echo "Starting Ollama server in background thread..."
ollama serve > /dev/null 2>&1 &
sleep 10
echo "Downloading Phi3:instruct 8B model... 4.1 GB"
ollama pull "phi3:3.8b-mini-128k-instruct-q8_0" > /dev/null 2>&1
sleep 10