FROM python:3.11-slim

# Install system dependencies (useful for python-docx, pymupdf, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
# Using uv sync to install dependencies into a virtual environment at /app/.venv
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY . .

# Expose the default Render port
EXPOSE 10000

# Run the FastAPI app using the uv virtual environment
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
