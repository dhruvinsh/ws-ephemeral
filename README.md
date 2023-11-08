# WS-EPHEMERAL

This project aims to automate setting up ephemeral port on Windscribe VPN
service for the purpose of port forwarding. Once the setup is done it wait
patiently for next seven days. It delete the ephemeral port setting if any and
set the new one. Useful for some torrent application which are running behind
Windscribe VPN and need to open the ports.

## Docker Setup

**NOTE: V1 is deprecated now and note supported.**

### Registries

There are two registries available:

- dhruvinsh/ws-ephemeral
- ghcr.io/dhruvinsh/ws-ephemera

### Tags

Available tags for docker image (based on semver):

| Tag    | Container Type                                |
| ------ | --------------------------------------------- |
| main   | straight from `main` branch                   |
| latest | most recent changes straight from main branch |
| x      | specific major versoin with all patches       |
| 3.x.x  | Specific version                              |

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
-v /home/user/appdata/:/cookie \
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
| WS_DEBUG             | Enable Debug logging                                                             |
| WS_COOKIE_PATH       | Persistent location for the cookie. (v3.x.x only)                                |
| QBIT_USERNAME        | QBIT username                                                                    |
| QBIT_PASSWORD        | QBIT password                                                                    |
| QBIT_HOST            | QBIT web address like, https://qbit.xyz.com or http://192.168.1.10               |
| QBIT_PORT            | QBIT web port number like, 443 or 8080                                           |
| QBIT_PRIVATE_TRACKER | get QBIT ready for private tracker by disabling dht, pex and lsd (true or false) |
| ONESHOT              | Run and setup the code only one time so that job can be schedule externally      |
| REQUEST_TIMEOUT      | configurable http api timeout for slow network/busy websites                     |

> NOTE: for usage see [Docker Setup](#docker-setup) v2 setup guide.

## Unraid Setup

Unraid template is now available under community application.

## Changelog

Located [here](./CHANGELOG.md)

## Privacy

I assure you that nothing is being collected or logged. Your credentials are
safe and set via environment variable only. Still If you have further questions
or concerns, please open an issue here.

## License

[GPL3](LICENSE.md)
