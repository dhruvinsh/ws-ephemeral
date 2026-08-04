# WS-EPHEMERAL

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

Images are published to GitHub Container Registry under the repository owner:

- `ghcr.io/<repository-owner>/ws-ephemeral`

### Tags

Available tags for docker image (based on semver):

| Tag    | Container Type                 |
| ------ | ------------------------------ |
| main   | straight from `main` branch    |
| latest | latest stable released version |
| x      | specific major version         |
| x.x    | specific minor version         |
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
-e WS_TOPT=totp_token \
-v /path/to/local/data:/cookie \
ghcr.io/<repository-owner>/ws-ephemeral:latest
```

#### Docker-compose

Docker compose file is provided for example. Set `WS_EPHEMERAL_IMAGE` to the
GHCR image for a fork if needed, make any other adjustments, and run:

```bash
docker compose up -d
```

### Environment Variables

| Variable             | Comment                                                                          |
| -------------------- | -------------------------------------------------------------------------------- |
| WS_USERNAME          | WS username                                                                      |
| WS_PASSWORD          | WS password                                                                      |
| WS_TOTP              | WS totp token for 2fa                                                            |
| WS_DEBUG             | Enable Debug logging                                                             |
| WS_COOKIE_PATH       | Persistent location for the cookie. (v3.x.x only)                                |
| QBIT_USERNAME        | QBIT username                                                                    |
| QBIT_PASSWORD        | QBIT password                                                                    |
| QBIT_API_KEY         | QBIT API key; alternative to username/password and requires qBittorrent v5.2.0+ |
| QBIT_HOST            | QBIT web address like, https://qbit.xyz.com or http://192.168.1.10               |
| QBIT_PORT            | QBIT web port number like, 443 or 8080                                           |
| QBIT_PRIVATE_TRACKER | get QBIT ready for private tracker by disabling dht, pex and lsd (true or false) |
| GLUETUN_URL           | Gluetun control server URL; setting it enables VPN firewall port synchronization  |
| GLUETUN_API_KEY       | API key for the Gluetun control server, if API-key authentication is configured   |
| GLUETUN_USERNAME      | Username for Gluetun control server basic authentication                          |
| GLUETUN_PASSWORD      | Password for Gluetun control server basic authentication                          |
| ONESHOT              | Run and setup the code only one time so that job can be schedule externally      |
| REQUEST_TIMEOUT      | configurable http api timeout for slow network/busy websites                     |

> [!tip]
> NOTE: for usage see [Docker Setup](#docker-setup) v2 setup guide.

### qBittorrent authentication

Use either a qBittorrent username and password:

```env
QBIT_USERNAME=admin
QBIT_PASSWORD=replace-with-password
```

Or, with qBittorrent v5.2.0 or newer, generate an API key in its WebUI settings
and configure:

```env
QBIT_API_KEY=qbt_replace_with_api_key
```

Do not configure `QBIT_API_KEY` together with `QBIT_USERNAME` or
`QBIT_PASSWORD`. API-key support requires `qbittorrent-api` v2026.5.3 or newer,
which is included in this project.

### Gluetun VPN firewall synchronization

ws-ephemeral can replace Gluetun's runtime VPN firewall port whenever
Windscribe assigns a new matching port. This removes the need to update
`FIREWALL_VPN_INPUT_PORTS` and restart Gluetun for each renewal.
`FIREWALL_INPUT_PORTS` controls Gluetun's default interface and does not need
the Windscribe-assigned port unless you separately want that port reachable
through the default interface.

This integration requires a Gluetun release containing
[`PUT /v1/portforward`](https://github.com/passteque/gluetun/pull/2392).
Gluetun v3.41.2 does not contain that endpoint. Leave Gluetun's
`VPN_PORT_FORWARDING` option off because ws-ephemeral obtains the port from
Windscribe.

Set `GLUETUN_URL` to enable the integration:

```env
GLUETUN_URL=http://gluetun:8000
GLUETUN_API_KEY=replace-with-api-key
```

Use `http://127.0.0.1:8000` instead when ws-ephemeral shares Gluetun's network
namespace. The control server does not need to be published outside the Docker
network.

Gluetun must authorize both the update and verification routes. For API-key
authentication, its `/gluetun/auth/config.toml` can include:

```toml
[[roles]]
name = "ws-ephemeral"
routes = ["PUT /v1/portforward", "GET /v1/portforward"]
auth = "apikey"
apikey = "replace-with-api-key"
```

Alternatively, set `GLUETUN_USERNAME` and `GLUETUN_PASSWORD` for a basic-auth
role. Do not set them together with `GLUETUN_API_KEY`. If the matching Gluetun
role uses `auth = "none"`, only `GLUETUN_URL` is needed.

The change is runtime state. Restarting Gluetun clears it, so restart
ws-ephemeral with Gluetun or otherwise run ws-ephemeral again after a Gluetun
restart.

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
- [x] Gluetun support [#2392](https://github.com/passteque/gluetun/pull/2392)

## License

[GPL3](LICENSE.md)
