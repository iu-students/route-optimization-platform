FROM python:3.12-slim

WORKDIR /ROP

COPY api/MVPv1.2/requirements.txt MVPv1.2/
RUN pip install --no-cache-dir -r MVPv1.2/requirements.txt

COPY data/ data/
COPY api/MVPv1.2/ MVPv1.2/

EXPOSE 5011

CMD ["python", "MVPv1.2/app.py"]
