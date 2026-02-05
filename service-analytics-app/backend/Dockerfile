FROM python:3.11-slim

WORKDIR /app

# No system dependencies needed - all packages are available as binary wheels
# psycopg2-binary, pandas, and all other packages install without compilation

# Upgrade pip first for better package resolution
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# All packages are available as pre-built wheels, no compilation needed
RUN pip install --no-cache-dir --timeout=100 -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

