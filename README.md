# WS-EPHEMERAL

This project aims to automate setting up ephemeral port on windscribe VPN service for the purpose of port forwarding. Once the setup is done it wait patiently for next seven days. It delete the ephemeral port setting if any and set the new one. Useful for some torrent application which are running behind windscribe VPN and need to open the ports.

## Docker Setup

```bash
docker run -e WS_USERNAME=username -e WS_PASSWORD=password -e WS_EPHEMERAL_PORT=40000 dhruvinsh/ws-ephemeral:latest
```

Available tags for docker image:

| Tag    | Container type                                |
| ------ | --------------------------------------------- |
| latest | most recent changes straight from main branch |
| 1.x.x  | specific build from v1                        |
| x      | major version with all the patches            |

## Unraid Setup

Unraid template is now available under communinty application.

## Changelog

v1.2.0 - 7th April 2023

Better progress bar added with better way of logging message on the console. Also preparing system for the next v2.0.0 release with qbit support

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
