# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12.11
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /

# Non-root user (match host UID to avoid volume perms issues)
ARG UID=10001
RUN adduser --disabled-password --gecos "" --home "/home/appuser" \
    --shell "/sbin/nologin" --uid "${UID}" appuser
RUN mkdir -p /home/appuser && chown appuser:appuser /home/appuser

# ----- Pick ONE dep install style -----
# Simple:
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Faster (BuildKit):
# RUN --mount=type=cache,target=/root/.cache/pip \
#     --mount=type=bind,source=requirements.txt,target=requirements.txt \
#     python -m pip install -r requirements.txt
# -------------------------------------

COPY . .
ENV HOME=/home/appuser
RUN chmod -R a+w /home/appuser /tmp /reports /out || true
USER appuser

# For a CLI script, no EXPOSE
CMD ["python", "main.py"]
# (no CMD so args come from the runner)