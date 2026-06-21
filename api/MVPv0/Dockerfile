FROM python:3.12-slim

WORKDIR /ROP

COPY api/MVPv0/requirements.txt MVPv0/
RUN pip install --no-cache-dir -r MVPv0/requirements.txt

COPY api/MVPv0/ MVPv0/
COPY api/openapi.yaml .

EXPOSE 5000

CMD ["python", "MVPv0/app.py"]
