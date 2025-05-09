# Use the official Python base image
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install the application dependencies
RUN uv sync --frozen --no-cache

# Expose the port on which the application will run
EXPOSE 80

# Run the FastAPI application using uv
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "--port", "80"]