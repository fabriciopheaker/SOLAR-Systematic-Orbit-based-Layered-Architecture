FROM python:3.14-slim

WORKDIR /solar

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# A aplicação sobe pelo ponto de entrada: o Kernel monta,
# o Server sobe.
CMD ["python", "server.py"]