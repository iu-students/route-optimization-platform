FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY script.py loaders.py models.py .
COPY data/ data/
COPY api/MVPv1/ api/MVPv1/
RUN pip install --no-cache-dir -r api/MVPv1/requirements.txt

EXPOSE 5001

CMD ["python", "api/MVPv1/app.py"]
