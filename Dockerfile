FROM python:3.12-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates git tesseract-ocr ffmpeg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g prettier@3.4.2 && \
    rm -rf /var/lib/apt/lists/*


ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

RUN useradd -ms /bin/bash appuser

RUN mkdir -p /data
WORKDIR /app

COPY .env /app/.env  
COPY --chown=appuser:appuser . /app

USER appuser

RUN pip install --upgrade pip && \
    pip install charset-normalizer && \
    pip install pytesseract && \
    pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
