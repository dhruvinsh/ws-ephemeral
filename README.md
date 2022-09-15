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

Work in progress.

## Privacy

I assure you that nothing is being collected or logged. Your credentials are safe and set via environment variable only. Still If you have further questions or concerns, please open an issue here.

## License

[GPL3](LICENSE.md)
