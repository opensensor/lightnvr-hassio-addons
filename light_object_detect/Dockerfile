ARG BUILD_FROM=python:3.11-slim-trixie
FROM ${BUILD_FROM}

# Build the CPU/Coral runtime from a pinned upstream revision. The general
# upstream image also installs Torch/Transformers and is several GB larger.
ARG UPSTREAM_REF=b7060b933e06b7a5b6c6f5d3fad88ba7ecdb8013
ARG TARGETARCH
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libusb-1.0-0 \
    && arch="${TARGETARCH:-$(dpkg --print-architecture)}" \
    && curl -fsSL --retry 3 "https://github.com/feranick/libedgetpu/releases/download/16.0TF2.19.1-1/libedgetpu1-std_16.0tf2.19.1-1.trixie_${arch}.deb" -o /tmp/edgetpu.deb \
    && dpkg -i /tmp/edgetpu.deb \
    && curl -fsSL --retry 3 "https://github.com/opensensor/light-object-detect/archive/${UPSTREAM_REF}.tar.gz" -o /tmp/source.tar.gz \
    && tar -xzf /tmp/source.tar.gz --strip-components=1 -C /app \
    && rm /tmp/edgetpu.deb /tmp/source.tar.gz \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && python scripts/download_model.py
COPY run.py ha_app.py healthcheck.py /app/
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD ["python", "/app/healthcheck.py"]
ENTRYPOINT ["python", "/app/run.py"]
