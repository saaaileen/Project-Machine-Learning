FROM node:22-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/project-ml/package.json frontend/project-ml/package-lock.json ./
RUN npm ci

COPY frontend/project-ml/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir \
    -r requirements.txt \
    fastapi[standard] \
    uvicorn[standard] \
    python-multipart \
    python-dotenv \
    bcrypt \
    PyJWT

# Copy backend source
COPY --chown=user backend/ ./backend/

# Copy model weights & label encoder
COPY --chown=user model/ ./model/

# Copy default dataset(s)
COPY --chown=user dataset/ ./dataset/

COPY --from=frontend-build --chown=user /app/frontend/dist ./backend/static

ENV HOST=0.0.0.0
ENV PORT=7860

ENV PYTHONPATH="/app/backend:$PYTHONPATH"
EXPOSE 7860

WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
