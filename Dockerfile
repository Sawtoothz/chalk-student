# Chalk in a container: the same app on Windows (Docker Desktop), macOS and Linux.
#   docker compose up            -> http://localhost:8765
#   ./chalk test thrun-pr 4      (Windows: chalk test thrun-pr 4) runs any `just` recipe inside
# The project folder is bind-mounted at /app (compose.yaml), so packages, exercise.py and learner.yaml stay on the
# host. Python lives in /opt/venv inside the image, never in the project folder.
FROM python:3.12-slim-trixie

# AI agents that can run the /teach stages, as npm packages; empty = none (studying the shipped packages needs none).
# Set CHALK_AI in .env, e.g. CHALK_AI=@anthropic-ai/claude-code, then: docker compose build
ARG AI_CLIS=""
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    VIRTUAL_ENV=/opt/venv \
    UV_LINK_MODE=copy \
    PATH=/opt/venv/bin:$PATH \
    CHALK_HOST=0.0.0.0

# just (commands), git (paper code refs), LibreOffice (slide PDFs), fonts for slides; Node only when AI tools are wanted
RUN apt-get update && apt-get install -y --no-install-recommends \
        just git curl ca-certificates bash \
        libreoffice-impress fonts-liberation fonts-dejavu-core \
    && if [ -n "$AI_CLIS" ]; then apt-get install -y --no-install-recommends nodejs npm \
         && npm install -g $AI_CLIS && npm cache clean --force; fi \
    && rm -rf /var/lib/apt/lists/* /usr/share/doc/* \
    && git config --system --add safe.directory '*' \
    && echo 'export PATH=/opt/venv/bin:$PATH' > /etc/profile.d/chalk-venv.sh   # login shells keep the venv first

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Non-root user: Claude Code refuses to skip permission prompts as root, and files written to the bind mount
# should belong to a normal user (uid 1000 matches the first user on most Linux hosts).
RUN useradd --create-home --uid 1000 --shell /bin/bash chalk && mkdir -p /opt/venv /app && chown chalk:chalk /opt/venv /app
USER chalk

# Python dependencies, cached as a layer: only pyproject.toml / uv.lock changes rebuild it
COPY --chown=chalk:chalk pyproject.toml uv.lock /tmp/deps/
RUN cd /tmp/deps && uv sync --frozen --no-install-project && rm -rf /tmp/deps ~/.cache/uv

WORKDIR /app
COPY --chown=chalk:chalk . /app

EXPOSE 8765 2718
CMD ["just", "serve"]
