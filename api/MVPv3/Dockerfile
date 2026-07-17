FROM python:3.12-slim

WORKDIR /ROP

COPY api/MVPv3/requirements.txt MVPv3/
RUN pip install --no-cache-dir -r MVPv3/requirements.txt

COPY data/ data/
COPY api/MVPv3/ MVPv3/

EXPOSE 5003

CMD ["python", "MVPv3/Web/app.py"]
