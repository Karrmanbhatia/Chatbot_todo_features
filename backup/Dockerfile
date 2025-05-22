# rasa/Dockerfile
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

# Copy project files
COPY . .

# Default command to run when the container starts
ENTRYPOINT ["rasa"]
CMD ["run", "--enable-api", "--cors", "*"]