FROM python:3.11-alpine

ENV WS_USERNAME=${WS_USERNAME}
ENV WS_PASSWORD=${WS_PASSWORD}
ENV WS_EPHEMERAL_PORT=${WS_EPHEMERAL_PORT}

WORKDIR /app

COPY requirements.txt .
COPY src ./

RUN python3 -m pip install -U pip
RUN python -m pip install -r requirements.txt

CMD ["python3", "run.py"]
