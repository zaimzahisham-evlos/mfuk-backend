FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the requirements files
COPY pyproject.toml uv.lock ./

# Install dependencies (Syncing without the app first)
RUN uv sync --frozen --no-install-project

# Copy the rest of the application code
COPY . .

# Final sync to install the project itself
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]