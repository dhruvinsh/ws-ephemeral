FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .

RUN python3 -m pip install -U pip
RUN python -m pip install -r requirements.txt

COPY src ./

CMD ["python3", "run.py"]
