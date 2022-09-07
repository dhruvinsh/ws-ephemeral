# WS-EPHEMERAL

This project aims to automate setting up ephemeral port on windscribe VPN service for the purpose of port forwarding. Once the setup is done it wait patiently for next seven days. It delete the ephemeral port setting if any and set the new one. Useful for some torrent application which are running behind windscribe VPN and need to open the ports.

## Docker Setup

```bash
docker run -e WS_USERNAME=username -e WS_PASSWORD=password -e WS_EPHEMERAL_PORT=40000 dhruvinsh/ws-ephemeral
```

## Unraid Setup

Work in progress.

## Privacy

I assure you that nothing being collected or logged. If you have further question option the issue here or check the source code.
