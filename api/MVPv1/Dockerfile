FROM python:3.12-slim

WORKDIR /ROP

COPY api/MVPv1/requirements.txt MVPv1/
RUN pip install --no-cache-dir -r MVPv1/requirements.txt

COPY script.py loaders.py models.py verifier.py .
COPY data/ data/
COPY api/MVPv1/ MVPv1/

EXPOSE 5001

CMD ["python", "MVPv1/app.py"]
