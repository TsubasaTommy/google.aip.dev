# syntax=docker/dockerfile:1.7
#
# Build context is the repository root:
#   docker build -f mcp/Dockerfile -t aip-mcp .
#
# The image bundles both the Python MCP server and the AIP markdown corpus,
# so `docker run --rm -i aip-mcp` is enough to launch the stdio server.

FROM python:3.13-slim

WORKDIR /app

# Install the MCP package first so the dependency layer is reused
# when only the AIP corpus changes.
COPY mcp/pyproject.toml mcp/README.md /app/mcp/
COPY mcp/src /app/mcp/src
RUN pip install --no-cache-dir /app/mcp

# Bake the AIP corpus into the image.
COPY aip /app/aip

ENV AIP_REPO=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["aip-mcp"]
