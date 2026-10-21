"""A fake of the parts of api.windscribe.com that we use, no network involved."""

from dataclasses import dataclass, field

import httpx

GOOD_TOKEN = "9:1:1:" + "a" * 20 + ":" + "b" * 30


@dataclass
class FakeApi:
    # the current ephemeral port, None if there is none
    port: str | None = None
    # the only session token that the API accepts
    valid_token: str = GOOD_TOKEN
    # if set, the login is rejected with this error body
    session_error: dict[str, object] | None = None
    # the external and internal port handed out for a new port
    new_port: tuple[int, int] = (7, 7)
    requests: list[httpx.Request] = field(default_factory=list)

    def client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self._handle))

    def calls(self) -> list[tuple[str, str]]:
        return [(r.method, r.url.path) for r in self.requests]

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path

        if path == "/AuthToken/login":
            return httpx.Response(200, json={"data": {"token": "t", "token_sig": "s"}})

        if path == "/Session":
            if self.session_error is not None:
                return httpx.Response(403, json=self.session_error)
            body = {"data": {"session_auth_hash": self.valid_token}}
            return httpx.Response(201, json=body)

        if request.headers["authorization"] != f"Bearer {self.valid_token}":
            return httpx.Response(
                403,
                json={
                    "errorCode": 701,
                    "errorMessage": "Session is invalid",
                    "errorDescription": "Submitted session is invalid. Please re-log in",
                },
            )

        if request.method == "GET":
            epf = (
                {"ext": self.port, "int": self.port, "start_ts": "1"}
                if self.port
                else False
            )
            return httpx.Response(200, json={"data": {"epf": epf, "success": 1}})

        if request.method == "DELETE":
            self.port = None
            return httpx.Response(200, json={"data": {"epf": True, "success": 1}})

        external, internal = self.new_port
        self.port = str(external)
        epf = {"ext": external, "int": internal, "start_ts": 1}
        return httpx.Response(200, json={"data": {"epf": epf, "success": 1}})
