# ─── Build Stage ────────────────────────────────────────────────────────────
FROM python:3.10-slim AS build

# Install system deps for Ollama installer
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install Ollama CLI as root
RUN curl -fsSL https://ollama.com/install.sh | sh

# Prepare Python deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY app.py bot.py ./

# ─── Runtime Stage ──────────────────────────────────────────────────────────
FROM python:3.10-slim

# Copy Ollama CLI from build stage
COPY --from=build /usr/local/bin/ollama /usr/local/bin/ollama

WORKDIR /app
# Copy installed site-packages
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy your code
COPY app.py bot.py ./

# Expose the Gradio port
EXPOSE 7860

# Launch both bot and Gradio app together
ENTRYPOINT ["bash", "-lc", "python bot.py & python app.py"]