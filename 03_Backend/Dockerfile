FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY 03_Backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home vca
COPY 03_Backend/app /app/app
COPY 02_Configuration /configuration
COPY 06_Azure_Infrastructure/05_init_search.py /app/init_search.py
RUN mkdir -p /app/data && chown -R vca:vca /app /configuration
USER vca
ENV POLICY_FILE=/configuration/policy.pending.json
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--no-access-log"]
