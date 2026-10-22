FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.115.12 uvicorn==0.34.2 && useradd --uid 10001 --create-home vca && mkdir /data && chown vca /data
COPY 05_LOS_Integration/simulator.py /app/simulator.py
USER vca
EXPOSE 8090
CMD ["uvicorn","simulator:app","--host","0.0.0.0","--port","8090","--no-access-log"]
