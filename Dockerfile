FROM python:3.12-alpine

# setup work directory
WORKDIR /app

# setup package
COPY requirements.lock .
RUN sed '/-e/d' requirements.lock > requirements.txt
RUN python3 -m pip install -U pip
RUN python -m pip install -r requirements.txt

# copy rest of the project
COPY src/ws_ephemeral ./ws_ephemeral

ENV PYTHONPATH "${PYTHONPATH}:/app/ws_ephemeral"

CMD ["python3", "ws_ephemeral", "renew", "--qbit", "--forever"]
