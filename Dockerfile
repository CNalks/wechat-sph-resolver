FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8020
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8020"]
