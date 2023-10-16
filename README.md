# WS-EPHEMERAL

This project aims to automate setting up ephemeral port on windscribe VPN service for the purpose of port forwarding. Once the setup is done it wait patiently for next seven days. It delete the ephemeral port setting if any and set the new one. Useful for some torrent application which are running behind windscribe VPN and need to open the ports.

## Docker Setup

**NOTE**: updating to latest version will not break existing system but it is not advice to use it any longer. Proper environment values (see below) need to be set for qbit.

**V1 setup (NOT ADVISED TO USE ANYMORE)**

```bash
docker run -e WS_USERNAME=username -e WS_PASSWORD=password -e dhruvinsh/ws-ephemeral:latest
```

**V2 setup**

```bash
docker run \
-e WS_USERNAME=username \
-e WS_PASSWORD=password \
-e QBIT_USERNAME=username \
-e QBIT_PASSWORD=password \
-e QBIT_HOST=http://192.168.1.10 \
-e QBIT_PORT=8080 \
-e QBIT_PRIVATE_TRACKER=true \
-e ONESHOT=false \
-e REQUEST_TIMEOUT=10 \
dhruvinsh/ws-ephemeral:latest
```

Docker compose file is provided for example, make some adjustment and run as,

```bash
docker compose up -d
```

### Tags

Available tags for docker image:

| Tag    | Container Type                                                                     |
| ------ | ---------------------------------------------------------------------------------- |
| latest | most recent changes straight from main branch                                      |
| 2.x.x  | Specific build from v2 with qbit and matching port support                         |
| 1.x.x  | Specific build from v1 with no qbit or matching port support (in maintenance mode) |
| x      | specific major versoin with all patches                                            |

### Environment Variables

| Variable             | Comment                                                                          | Applicable Version |
| -------------------- | -------------------------------------------------------------------------------- | ------------------ |
| WS_USERNAME          | WS username                                                                      | v1.x.x and v2.x.x  |
| WS_PASSWORD          | WS password                                                                      | v1.x.x and v2.x.x  |
| QBIT_USERNAME        | QBIT username                                                                    | v2.x.x             |
| QBIT_PASSWORD        | QBIT password                                                                    | v2.x.x             |
| QBIT_HOST            | QBIT web address like, https://qbit.xyz.com or http://192.168.1.10               | v2.x.x             |
| QBIT_PORT            | QBIT web port number like, 443 or 8080                                           | v2.x.x             |
| QBIT_PRIVATE_TRACKER | get QBIT ready for private tracker by disabling dht, pex and lsd (true or false) | v2.x.x             |
| ONESHOT              | Run and setup the code only one time so that job can be schedule externally      | v2.x.x             |
| REQUEST_TIMEOUT      | configurable http api timeout for slow network/busy websites                     | v2.x.x             |

> NOTE: for usage see [Docker Setup](#docker-setup) v2 setup guide.

## Unraid Setup

Unraid template is now available under community application.

## Changelog

Located [here](./CHANGELOG.md)

## Privacy

I assure you that nothing is being collected or logged. Your credentials are safe and set via environment variable only. Still If you have further questions or concerns, please open an issue here.

## License

[GPL3](LICENSE.md)
