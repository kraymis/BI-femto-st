FROM node:22-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_DEMO_MODE=true
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
COPY requirements-deploy.txt ./
RUN python -m pip install --no-cache-dir -r requirements-deploy.txt
COPY backend ./backend
COPY src ./src
COPY data/raw/stages_cleaned2.xlsx ./data/raw/stages_cleaned2.xlsx
COPY data/interim/geographic_reference.csv ./data/interim/geographic_reference.csv
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV BI_DATA_MODE=real
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
