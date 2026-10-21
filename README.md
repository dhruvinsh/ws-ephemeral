# WS-EPHEMERAL

> [!ATTENTION]
> **Disclosures:** AI and AI tooling has been used for this project revival purpose. But I (human) was in the loop to make sure it is achieving the intended goal (at least for me).

> [!WARNING]
> Please use this tool responsibly. Excessive or inappropriate
> usage may result in temporary suspension of your account. Due to lack of
> time I will try to revisit sometime in future but I strongly advice to let
> it run at default pace, that is once every week. For new user cookie generation
> might fail at the beginning, please try again after some time once you delete
> partially created cookie.

> [!NOTE]
> **Current State of the Project:** There are upstream web changes affecting this project. I am also suffering from issue and I would like implement fixes but lack of time its not possible at the moment. I plan to get back to it as soon as possible.

This project aims to automate setting up ephemeral port on Windscribe VPN
service for the purpose of port forwarding. Once the setup is done it wait
patiently for next seven days. It delete the ephemeral port setting if any and
set the new one. Useful for some torrent application which are running behind
Windscribe VPN and need to open the ports.

## Docker Setup

> [!important]
> NOTE: V1 is deprecated and should not be used.

### Registries

There are two registries available:

- dhruvinsh/ws-ephemeral
- ghcr.io/dhruvinsh/ws-ephemeral

### Tags

Available tags for docker image (based on semver):

| Tag    | Container Type                 |
| ------ | ------------------------------ |
| main   | straight from `main` branch    |
| latest | latest stable released version |
| x      | specific major version         |
| x.x.x  | specific version               |

### Deploy

#### Cli

```bash
docker run \
-e ONESHOT=false \
-e QBIT_HOST=http://192.168.1.10 \
-e QBIT_PASSWORD=password \
-e QBIT_PORT=8080 \
-e QBIT_PRIVATE_TRACKER=true \
-e QBIT_USERNAME=username \
-e REQUEST_TIMEOUT=10 \
-e WS_COOKIE_PATH=/cookie \
-e WS_DEBUG=False \
-e WS_PASSWORD=password \
-e WS_USERNAME=username \
-e WS_TOTP=totp_token \
-v /path/to/local/data:/cookie \
dhruvinsh/ws-ephemeral:latest
```

#### Docker-compose

Docker compose file is provided for example, make some adjustment and run as,

```bash
docker compose up -d
```

### Environment Variables

| Variable             | Comment                                                                          |
| -------------------- | -------------------------------------------------------------------------------- |
| WS_USERNAME          | WS username                                                                      |
| WS_PASSWORD          | WS password                                                                      |
| WS_TOTP              | WS totp token for 2fa                                                            |
| WS_DEBUG             | Enable Debug logging (true or false)                                             |
| WS_COOKIE_PATH       | Persistent directory that keeps the session between runs, mount it as a volume   |
| QBIT_USERNAME        | QBIT username                                                                    |
| QBIT_PASSWORD        | QBIT password                                                                    |
| QBIT_HOST            | QBIT web address like, https://qbit.xyz.com or http://192.168.1.10               |
| QBIT_PORT            | QBIT web port number like, 443 or 8080                                           |
| QBIT_PRIVATE_TRACKER | get QBIT ready for private tracker by disabling dht, pex and lsd (true or false) |
| DAYS                 | Days between two runs of the `daemon` command, default 6                         |
| TIME                 | Time of the day to run at, HH:MM in the timezone set by `TZ`, default 02:00      |
| CRON                 | A 5 field cron expression like `0 2 * * 1`, replaces `DAYS` and `TIME`           |
| RUN_ON_START         | Also run once when the `daemon` starts, default true                             |
| TZ                   | Timezone of the schedule, like `America/Toronto`, default UTC in Docker          |
| ONESHOT              | Run and setup the code only one time so that job can be schedule externally      |
| REQUEST_TIMEOUT      | configurable http api timeout for slow network/busy websites                     |

> [!tip]
> NOTE: for usage see [Docker Setup](#docker-setup) v2 setup guide.

## Usage

The docker image runs `ws-ephemeral daemon`. There are two commands, every option
is also available as the environment variable listed above, see `--help`.

```bash
ws-ephemeral run      # rotate the port once and exit, non-zero exit code on failure
ws-ephemeral daemon   # keep rotating it on a schedule (every DAYS days at TIME, or CRON)
```

Use `run` when something else owns the schedule, like cron or a systemd timer. For
example, in a Docker container with the volume from above:

```bash
docker run --rm --env-file .env -v /path/to/local/data:/cookie \
dhruvinsh/ws-ephemeral:latest ws-ephemeral run
```

Every start of the `daemon` also rotates the port, because the schedule is counted
from the start. Pass `--no-run-on-start` (or `RUN_ON_START=false`) to wait for the
first scheduled run instead.

## Development

The project uses [uv](https://docs.astral.sh/uv/) and Python 3.14.

```bash
uv sync                          # create .venv and install dependencies (including dev)
uv run ws-ephemeral --help       # run the cli locally, needs the environment variables from above
uv add <package>                 # add a dependency, updates pyproject.toml and uv.lock
uv run pytest                    # tests, they never touch the network
uv run ruff check                # lint
uv run ruff format               # format
uv run pyrefly check             # type check
uv run prek install              # run the checks before each commit, and the tests before each push
uv run prek run --all-files      # run all pre-commit hooks on every file
```

The code lives in `src/ws_ephemeral`: `cli.py` (typer commands), `job.py` (one
port rotation), `scheduler.py` (APScheduler), `windscribe.py` (the API client) and
`qbit.py`. CI runs the same checks as the hooks.

## Unraid Setup

Unraid template is now available under community application.

## Changelog

Located [here](./CHANGELOG.md)

## Privacy

I assure you that nothing is being collected or logged. Your credentials are
safe and set via environment variable only. Still If you have further questions
or concerns, please open an issue here.

## Roadmap

- [x] Support 2FA, #19
- [ ] Daemon mode and job mode
  - [ ] Rest API (useful for cron/script job)
  - [ ] Separate port renewal, qbittorrent update and private tracker logic
  - [ ] Random job time for cron job #15
- [ ] Allow to run custom script (for now Bash script only) #12
- [ ] Support for deluge
- [ ] Gluetun support [#2392](https://github.com/qdm12/gluetun/pull/2392)

## License

[GPL3](LICENSE.md)
