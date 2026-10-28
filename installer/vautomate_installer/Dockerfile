FROM python:3.14.0-alpine3.22
WORKDIR /app
COPY installer.py payload.json ./
COPY payload ./payload
CMD ["python", "-u", "/app/installer.py"]
