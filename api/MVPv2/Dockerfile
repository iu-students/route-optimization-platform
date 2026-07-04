FROM python:3.12-slim

WORKDIR /ROP

COPY api/MVPv2/requirements.txt MVPv2/
RUN pip install --no-cache-dir -r MVPv2/requirements.txt

COPY data/ data/
COPY api/MVPv2/ MVPv2/

EXPOSE 5002

CMD ["python", "MVPv2/Web/app.py"]
