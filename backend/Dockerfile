FROM python:3.12.2-slim

# Install git and build dependencies (required for crewai[tools])
RUN apt-get update && \
    apt-get install -y git gcc g++ make curl docker.io docker-compose && \
    apt-get clean

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn sqlmodel python-dotenv openai instructor pydantic
# Install custom puntorigen crewai with latest instructor 1.3.2 (supporting ollama output_pydantic)
#RUN pip install --no-cache-dir https://github.com/puntorigen/crewai/archive/main.zip
#RUN pip install --no-cache-dir crewai "crewai[tools]" 
RUN pip install git+https://github.com/joaomdmoura/crewAI.git@d3b6640b4ad804ca4537d25af0278b0743f511e3
#RUN pip install --no-cache-dir https://github.com/joaomdmoura/crewAI/archive/main.zip
RUN pip install --no-cache-dir "crewai[tools]" 
RUN pip install --no-cache-dir embedchain

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Copy helper scripts
COPY docker /app/docker
COPY tools /app/tools
RUN chmod +x /app/docker/install_ollama.sh
#COPY docker-compose.yml /docker-compose.yml
#COPY docker-compose.yml /docker-compose.yml
RUN chmod +x /app/entrypoint.sh

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Set the entrypoint to the script
ENTRYPOINT ["/app/entrypoint.sh"]