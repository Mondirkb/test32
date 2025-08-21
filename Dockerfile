FROM python:3.10-slim-bullseye

# Install system dependencies for face-recognition (dlib, OpenCV, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    wget \
    git \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip==24.2 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir supervisor

# Copy application code
COPY . .

# Create instance folder for DB
RUN mkdir -p /app/instance && \
    chmod 777 /app/instance

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV SECRET_KEY=your-secret-key-here
ENV SQLALCHEMY_DATABASE_URI=sqlite:////app/instance/moundir.db
ENV SQLALCHEMY_TRACK_MODIFICATIONS=False
ENV WTF_CSRF_ENABLED=False
ENV PORT=5000

# Expose Flask + signaling server ports
EXPOSE 5000
EXPOSE 5001

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start both services under supervisor
CMD ["/usr/bin/supervisord"]
