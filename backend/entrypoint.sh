#!/bin/sh

#OPENAI_API_KEY=$1
export PYTHONUNBUFFERED=1 # this is to make sure that the output is not buffered and is printed in real-time

if [ -z "$OPENAI_API_KEY" ]; then
  # export args as ENV variables
  echo "OpenAI API key not provided. Starting Ollama using Shell..."
  /bin/sh -c /app/docker/install_ollama.sh
else
  echo "OpenAI API key provided. Skipping Ollama installation."
fi

echo "Running the script... $@"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload