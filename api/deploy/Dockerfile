FROM python:3.12-slim

WORKDIR /app

COPY deploy/requirements.txt deploy/
RUN pip install --no-cache-dir -r deploy/requirements.txt

COPY deploy/ deploy/
COPY openapi.yaml .

EXPOSE 5000

CMD ["python", "deploy/app.py"]
