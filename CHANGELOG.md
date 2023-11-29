## Changelog

v3.1.0 - 28th Nov 2023

- 1c37128 env: bumping the qbittorrentapi to latest version
- 6104d0a README: fixing registry url
- b88799b README updated
- 80bba0d README updated
- 90146ff ci: build image for main branch
- a463e67 ci: image release to ghcr.io
- dad5340 README update
- 9439bc2 env: updating to latest version
- 4f7dd6c updating pre-commit-config

v3.0.0 - 5th Nov 2023

- 528fa4a lib: correcting warning message
- 3ecd568 Merge pull request #10 from dhruvinsh/dev
- 33c08c1 docs(ws): updating README and other relevant docs
- 88c7f60 env: removing beautifulsoup4
- 5e83da6 chore(code): proper type hint
- 2288f54 windscribe: more cleaner api to work with cookie
- 90d224e gitignore updated
- 94a2a44 env: updating dependency along with poetry
- c343585 WIP: lib(ws): adding cookie storage support
- baec121 fix(monitor): fix heartbeat logic
- af8e1ce doc: splitting CHANGELOG and README
- 6f64474 env: env updated
- 1d5606b env updated
- 2733588 ci: even branch added so that dispatch can work
- 4045126 ci: minor tweak to build context
- 2a2ebb3 ci: adding docker building
- 0a6409c README change log updated

v2.3.0 - 26th Sep 2023

- 4f6e089 (HEAD -> main) README updated
- cfd382a gitignore update
- 217789f code: black formatting
- f66b6e9 util: adding Exception rather plain `except`
- a19adc5 (origin/main, origin/HEAD) ONESHOT, REQUEST_TIMEOUT and Efficient docker build (#7)

v2.2.0 - 19th Sep 2023

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

v2.0.0 - 9th Apr 2023

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

v1.2.0 - 7th Apr 2023

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
