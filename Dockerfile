FROM python:3.14-slim-bookworm

RUN useradd --create-home --user-group appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py routes.py ./
COPY shared/ shared/

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]