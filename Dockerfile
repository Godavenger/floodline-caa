# Optional PostgreSQL/PostGIS demo path; not executed on the local QA machine.
FROM node:22-bookworm-slim AS interface
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements-postgres.txt ./backend/
RUN python -m pip install --no-cache-dir -r backend/requirements-postgres.txt
COPY backend/ ./backend/
COPY data/ ./data/
COPY --from=interface /app/frontend/dist ./frontend/dist
ENV APP_MODE=synthetic FLOODLINE_RUNTIME=/app/.runtime
EXPOSE 8000
CMD ["python", "-m", "backend.floodline", "serve", "--host", "0.0.0.0"]
