FROM python:3.10-slim-bullseye

# Install only the necessary build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    wget \
    git \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database
RUN mkdir -p /app/instance && \
    chmod 777 /app/instance

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV SECRET_KEY=your-secret-key-here
ENV SQLALCHEMY_DATABASE_URI=sqlite:////app/instance/moundir.db
ENV SQLALCHEMY_TRACK_MODIFICATIONS=False
ENV WTF_CSRF_ENABLED=False
ENV PORT=8000

# Expose ports for Flask app and signaling server
EXPOSE 5000
EXPOSE 5001

# Command to run both Flask app and signaling server
CMD ["sh", "-c", "python app.py & python signaling_server.py"]
