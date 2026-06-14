FROM python:3.12-slim

WORKDIR /app

COPY MVPv0/requirements.txt MVPv0/
RUN pip install --no-cache-dir -r MVPv0/requirements.txt

COPY MVPv0/ MVPv0/
COPY openapi.yaml .

EXPOSE 5000

CMD ["python", "MVPv0/app.py"]
