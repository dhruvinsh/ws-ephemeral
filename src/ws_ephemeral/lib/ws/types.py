"""Windscribe type collection."""

from pydantic import BaseModel


class Csrf(BaseModel):
    """CSRF base model."""

    time: int
    token: str
