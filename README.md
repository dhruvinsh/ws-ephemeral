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

v2.2.0 - 19th Sept 2023

- af47114 heatbeat check added
- 708cba5 config: extracting some variable
- 5c315dd logging: space before the messages
- 822d316 env: all the dependency updated to latest version
- 3999224 pre-commit-config updated to latest version

v2.1.0 - 3rd Jun 2023

- a54aa1f code: logging sequence changed
- 2461df3 code: fire job at the beginning and then wait for schedule
- 6e64769 fix: time format for schedule was incorrect
- f1d8d89 fix: incorrect method for schedule
- 579fbf8 lib: migrating to schedule library
- 071fde8 env: schedule package added
- ff84105 code: converting WS to context manager
- e16bcc6 env: updating packages to latest version
- ab5086b updating pyproject metadata
- 4548209 packages: bump to latest version

v2.0.0 - 9th April 2023

- 8493fe1 (HEAD -> main) README updated
- 64f68a7 docker: update to setup
- a3f6c51 docker-compose example added
- bc5ea90 main: tqdm message
- a1cd806 chore: minor doc improvement
- 4ce2ef0 config: for now not using logging here
- 25a43d2 logging: disable existing logger
- 9a9a627 lib: proper protection for qbit
- 4945f8f qbit: do not break existing system
- 187cd5c Qbit: big update, qbit support added
- 33bafaa package(s): semver added
- 43e478e README: fixing another mess
- fe81416 README: fixing changelog

v1.2.0 - 7th April 2023

Better progress bar added with better way of logging message on the console. Also preparing system for the next v2.0.0 release with qbit support

- 2a1a382 (tag: v1.2.0) README: changelog added
- a985fa6 package(s): update to latest version
- 3a661b6 package(s): adding pyyaml types
- d148a67 lint(ruff): ignore line-too-long
- e64f818 minor spelling correction
- ef107ef logger: better way of logging added
- b299d21 package(s): adding pyyaml
- d3095e3 package(s): adding tqdm with stub
- 38be3f5 docker: copose file added for easy usage
- 5eea287 docker: bump python version to 3.11
- ce4fad8 pre-commit: adding pre-commit hook
- 3ba34d8 env: updating requirement files
- d0e7ede env: updating poetry lock
- 84641c5 packages: adding qbit api
- 5733d1b packages: bump to latest version

## Privacy

I assure you that nothing is being collected or logged. Your credentials are safe and set via environment variable only. Still If you have further questions or concerns, please open an issue here.

## License

[GPL3](LICENSE.md)
