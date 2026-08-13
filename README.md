# WS-EPHEMERAL

> [!WARNING]
> Please use this tool responsibly. Excessive or inappropriate
> usage may result in temporary suspension of your account. Due to lack of
> time I will try to revisit sometime in future but I strongly advice to let
> it run at default pace, that is once every week.

> [!NOTE]
> **Current State of the Project:** Windscribe put its website behind a bot
> protection, so the login now goes through the desktop client api
> (`api.windscribe.com`) and the resulting session is exchanged for a website
> session. The slider captcha that comes with that login is solved locally, no
> browser or captcha service is needed.

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
-e WS_TOPT=totp_token \
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
| WS_AUTH_HASH         | Optional existing api session hash, skips the username/password login            |
| WS_DEBUG             | Enable Debug logging                                                             |
| WS_COOKIE_PATH       | Persistent location for the session cache. (v3.x.x only)                         |
| QBIT_USERNAME        | QBIT username                                                                    |
| QBIT_PASSWORD        | QBIT password                                                                    |
| QBIT_HOST            | QBIT web address like, https://qbit.xyz.com or http://192.168.1.10               |
| QBIT_PORT            | QBIT web port number like, 443 or 8080                                           |
| QBIT_PRIVATE_TRACKER | get QBIT ready for private tracker by disabling dht, pex and lsd (true or false) |
| ONESHOT              | Run and setup the code only one time so that job can be schedule externally      |
| REQUEST_TIMEOUT      | configurable http api timeout for slow network/busy websites                     |

> [!tip]
> NOTE: for usage see [Docker Setup](#docker-setup) v2 setup guide.

> [!tip]
> `WS_COOKIE_PATH` should point to a persistent volume. The session is cached
> there (`session.json`) so that the login, and its captcha, only happen when
> the cached session is no longer accepted.

> [!tip]
> `WS_AUTH_HASH` is only needed as an escape hatch, for example when Windscribe
> serves a captcha that cannot be solved headlessly. It is the
> `session_auth_hash` value returned by `POST https://api.windscribe.com/Session`,
> and it is what the desktop client stores after a successful login.

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
