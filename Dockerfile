FROM python:3.11-slim AS python-base
# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend and frontend code
COPY ./backend ./backend
COPY ./frontend ./frontend

# Expose the port for Google Cloud Run
EXPOSE 8080

# Default to PORT 8000 for loca
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}