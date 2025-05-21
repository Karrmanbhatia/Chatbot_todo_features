#!/bin/bash

# Create directory structure
mkdir -p ansys-discovery-chatbot/rasa/actions
mkdir -p ansys-discovery-chatbot/rasa/data
mkdir -p ansys-discovery-chatbot/web

echo "Directory structure created"

# Create docker-compose.yml file
cat > ansys-discovery-chatbot/docker-compose.yml << 'EOL'
version: "3.0"
services:
  rasa:
    build: ./rasa
    ports:
      - "5005:5005"
    volumes:
      - ./rasa:/app
    command: run --enable-api --cors "*"

  web:
    build: ./web
    ports:
      - "8080:80"
    depends_on:
      - rasa
EOL

echo "docker-compose.yml created"

# Create Dockerfile for Rasa
cat > ansys-discovery-chatbot/rasa/Dockerfile << 'EOL'
FROM python:3.8.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgomp1 \
    graphviz-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install specific Rasa version and its dependencies
RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir rasa==3.2.10 rasa-sdk==3.2.3

# Install SQLAlchemy for your declarative base requirement
RUN pip install --no-cache-dir SQLAlchemy

# Default command to run when the container starts
ENTRYPOINT ["rasa"]
CMD ["run", "--enable-api", "--cors", "*"]
EOL

echo "Rasa Dockerfile created"

# Create Dockerfile for Web
cat > ansys-discovery-chatbot/web/Dockerfile << 'EOL'
FROM nginx:alpine

# Copy the HTML file to the nginx HTML directory
COPY . /usr/share/nginx/html/

# Expose port 80
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
EOL

echo "Web Dockerfile created"

# Create a README
cat > ansys-discovery-chatbot/README.md << 'EOL'
# Ansys Discovery Chatbot

## Running the Chatbot with Docker

1. Install Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Copy your Rasa files into the 'rasa' directory
3. Copy your HTML interface to the 'web' directory
4. Open a terminal/command prompt in this folder
5. Run the command: `docker-compose up`
6. Open your web browser and go to: http://localhost:8080
7. To stop the chatbot, press Ctrl+C in the terminal

## Folder Structure

```
ansys-discovery-chatbot/
├── docker-compose.yml
├── rasa/
│   ├── Dockerfile
│   ├── actions/
│   │   └── (your action files)
│   ├── data/
│   │   └── (your training data)
│   ├── config.yml
│   ├── domain.yml
│   ├── endpoints.yml
│   └── models/
│       └── (your trained model)
└── web/
    ├── Dockerfile
    └── index.html (your HTML file)
```
EOL

echo "README created"

echo "==============================================="
echo "Setup complete! Now you need to:"
echo "1. Copy your Rasa files into ansys-discovery-chatbot/rasa/"
echo "2. Copy your HTML interface to ansys-discovery-chatbot/web/"
echo "3. Run docker-compose from ansys-discovery-chatbot directory"
echo "==============================================="