FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Default command is to run the main backend app; overridden in docker-compose for microservices
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
