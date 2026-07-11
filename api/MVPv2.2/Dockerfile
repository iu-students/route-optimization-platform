FROM python:3.12-slim

WORKDIR /ROP

COPY api/MVPv2.2/requirements.txt MVPv2.2/
RUN pip install --no-cache-dir -r MVPv2.2/requirements.txt

COPY data/ data/
COPY api/MVPv2.2/ MVPv2.2/

EXPOSE 5022

CMD ["python", "MVPv2.2/Web/app.py"]
