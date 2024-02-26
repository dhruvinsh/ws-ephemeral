from fastapi import FastAPI

from run import main

app = FastAPI()
v1 = FastAPI()


@v1.get("/status")
def status() -> dict[str, str]:
    return {"message": "Hello World"}


@v1.post("/renew")
def renew() -> dict[str, str | None | int]:
    ret = main()
    return ret


app.mount("/api/v1", v1)
