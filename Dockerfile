FROM node:22-slim AS frontend
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app

# Install core + server
COPY core/ ./core/
RUN pip install --no-cache-dir ./core/

COPY server/ ./server/
RUN pip install --no-cache-dir ./server/

# Copy built frontend
COPY --from=frontend /app/web/dist ./web/dist

# Create data directory
RUN mkdir -p /data/documents

ENV MOWEN_DATABASE_URL=sqlite:////data/data.db
ENV MOWEN_UPLOAD_DIR=/data/documents
ENV MOWEN_HOST=0.0.0.0
ENV MOWEN_PORT=8000

EXPOSE 8000
CMD ["python", "-m", "mowen_server.main"]
