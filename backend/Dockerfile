# Use official Python 3.12 slim image
FROM python:3.12-slim

# Install uv package manager
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy the rest of the backend source code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start the application
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]