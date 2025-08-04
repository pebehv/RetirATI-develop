# Use Ubuntu 22.04 as base image
FROM ubuntu:22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Set environment variables for Django
ENV DJANGO_SETTINGS_MODULE=funATI.settings
ENV PYTHONPATH=/app/funATI

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    apache2 \
    apache2-dev \
    libapache2-mod-wsgi-py3 \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    redis-server \
    curl \
    netcat-openbsd \
    tzdata \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Set timezone
ENV TZ=America/Caracas
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Install mod_wsgi for Python 3
RUN pip3 install mod_wsgi

# Copy project files
COPY funATI/ /app/funATI/

# Create directories for static and media files
RUN mkdir -p /app/funATI/staticfiles
RUN mkdir -p /app/funATI/media

# Set permissions
RUN chown -R www-data:www-data /app/funATI/
RUN chmod -R 755 /app/funATI/

# Copy Apache configuration
COPY apache-funati.conf /etc/apache2/sites-available/funati.conf

# Enable Apache modules and site
RUN a2enmod wsgi
RUN a2enmod rewrite
RUN a2enmod headers
RUN a2enmod mime
RUN a2enmod expires
RUN a2enmod proxy
RUN a2enmod proxy_http
RUN a2enmod proxy_wstunnel
RUN a2dissite 000-default
RUN a2ensite funati

# Collect static files
WORKDIR /app/funATI
RUN python3 manage.py collectstatic --noinput

# Create startup and health check scripts
COPY start.sh /app/start.sh
COPY healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/start.sh /app/healthcheck.sh

# Expose port 80
EXPOSE 80

# Start services
CMD ["/app/start.sh"] 