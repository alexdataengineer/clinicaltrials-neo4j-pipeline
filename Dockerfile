FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.6.1

# Copy dependency files
COPY pyproject.toml ./

# Configure Poetry to not create virtual env
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Fix NumPy compatibility issue with pyarrow (pyarrow 14.x needs numpy <2.0)
RUN pip install "numpy<2.0" --no-cache-dir --force-reinstall

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create data directories
RUN mkdir -p /app/data/raw /app/data/staged /app/logs

# Set Python path
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.pipeline.run"]

