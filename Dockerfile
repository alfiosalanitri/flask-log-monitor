# ---------------------------------------------------------
# Dockerfile for Flask Log Monitor
# ---------------------------------------------------------

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy source code and dependencies
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Cron configuration for daily log cleanup
# ---------------------------------------------------------
# Runs the flask cleanup command every day at 3:00 AM
RUN echo "0 3 * * * cd /app && flask --app app cleanup >> /app/cron.log 2>&1" > /etc/cron.d/log-cleanup \
    && chmod 0644 /etc/cron.d/log-cleanup \
    && crontab /etc/cron.d/log-cleanup

# ---------------------------------------------------------
# Expose the port defined in .env (default 5000)
# ---------------------------------------------------------
ARG APP_PORT=5000
ENV APP_PORT=${APP_PORT}
EXPOSE ${APP_PORT}

# ---------------------------------------------------------
# Startup command: run cron and Flask together
# ---------------------------------------------------------
CMD service cron start && python app.py