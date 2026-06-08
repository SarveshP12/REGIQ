# ── Stage 1: Build Dependencies ──────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt .

RUN pip install --no-cache-dir -r requirements-docker.txt \
    && pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements-docker.txt


# ── Stage 2: Runtime Runner ─────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/wheels /app/wheels
COPY requirements-docker.txt .

RUN pip install --no-cache-dir --no-index --find-links=/app/wheels -r requirements-docker.txt \
    && rm -rf /app/wheels /app/requirements-docker.txt

# Copy application source code
COPY . .

# Security best practice: Create a non-root user and assign ownership
RUN addgroup --system --gid 1001 regiq && \
    adduser --system --uid 1001 --ingroup regiq regiq && \
    chown -R regiq:regiq /app

# Switch to the non-root user
USER regiq

# Expose port 8000
EXPOSE 8000

ENV PORT 8000
ENV HOSTNAME "0.0.0.0"
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
