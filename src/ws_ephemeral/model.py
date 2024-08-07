"""Type collection."""

from pydantic import BaseModel

from .status import Status


class Renewal(BaseModel):
    """Windscribe port renewal."""

    status: Status
    port: int | None
