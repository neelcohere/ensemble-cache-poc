# Ensemble Cache POC

A proof of concept implementation for an ensemble caching system built with FastAPI and Redis.

## Overview

This project demonstrates a caching system that combines multiple caching strategies to optimize performance and reliability. It's built using modern Python technologies and follows best practices for scalable web applications.

## Features

- FastAPI-based REST API
- Redis caching integration
- Asynchronous request handling
- Environment-based configuration
- Modular architecture
- Azure Container Registry (ACR) deployment support

## Prerequisites

- Python 3.10 or higher
- Redis server
- uv (Python package installer and resolver)
- Azure CLI (for ACR deployment)
- Docker

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ensemble-cache-poc
```

2. Create and activate a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies from pyproject.toml:
```bash
uv pip install .
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_SSL=False

# Authentication
BEARER_TOKEN=your_bearer_token_here
```

You can copy the `.env.example` file (if available) and modify the values according to your environment:

```bash
cp .env.example .env
```

Then edit the `.env` file with your specific configuration values.

## Running the Application

### Local Development

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Azure Container Registry Deployment

This branch is specifically configured for hosting the application on Azure Container Registry (ACR) and Azure App Service.

1. Login to Azure:
```bash
az login
```

2. Login to Azure Container Registry:
```bash
az acr login --name acrcachepoc
```

3. Build and push the Docker image:
```bash
docker buildx build --platform linux/amd64 -t acrcachepoc.azurecr.io/cache-poc:latest --push .
```

4. The application will be available at:
```
https://app-cache-poc.azurewebsites.net/
```

Available endpoints:
- API Documentation: `/docs` or `/redoc`
- Health Check: `/api/v1/health`
- Cache API: `/api/v1/cache`

## Project Structure

```
ensemble-cache-poc/
├── app/
│   ├── api/        # API endpoints
│   ├── core/       # Core functionality
│   ├── models/     # Data models
│   └── main.py     # Application entry point
├── scripts/        # Utility scripts
├── client/         # Client-side code
└── pyproject.toml  # Project configuration
```

## Dependencies

- FastAPI >= 0.115.12
- Redis >= 5.0.1
- Pydantic >= 2.11.5
- Python-dotenv >= 1.1.0
- Uvicorn >= 0.34.2
- Aiohttp >= 3.11.18