# Base Image suitable for air-gapped deployment
FROM python:3.11-slim

WORKDIR /app

# Copy dependency requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source directory structure
COPY . .

# Expose UDP Syslog Ingestion Port and Streamlit Dashboard Port
EXPOSE 5140/udp
EXPOSE 8501

# Default command to run the application UI
CMD ["streamlit", "run", "UI/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
