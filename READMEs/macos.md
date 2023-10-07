<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# MacOS Gotchas

Here are potential issues related to MacOS, and workarounds.

### Issue: MacOS * Docker

Summary:
- On MacOS, Docker may freeze
- Fix by reverting to Docker 4.22.1

Details:
- Symptoms: it stops logging; Docker cpu usage is 0%; it hangs when you type `docker ps` in console
- Docker 4.24.1 (Sep 28, 2023) freezes, and 4.22.1 (Aug 24, 2023) works. For us, anyway. [Docker release notes](https://docs.docker.com/desktop/release-notes).
- To fix, revert to Docker 4.22.1 by:
  - In console: `./cleanup.sh; docker system prune -a --volumes`
  - Download [Docker 4.22.1](https://docs.docker.com/desktop/release-notes/#4221)
  - Open the download, drag "Docker" to "Applications". Choose "Replace existing" when prompted.
  - Run Docker Desktop. Confirm the version via "About".
  - If you have the wrong version, then [fully uninstall Docker](https://www.makeuseof.com/how-to-uninstall-docker-desktop-mac/) and try again.

### Issue: MacOS * Subgraph Ports

Summary:
- The subgraph container reports a subgraph url like: `http://172.15.0.15:8000/subgraphs/name/oceanprotocol/ocean-subgraph`
- But agents or the browser can't see that directly, because MacOS doesn't support per-container IP addressing
- Workaround for envvars: `export SUBGRAPH_URL=http://localhost:9000/subgraphs/name/oceanprotocol/ocean-subgraph`
- Workaround for browser: open http://localhost:9000/subgraphs/name/oceanprotocol/ocean-subgraph/graphql

Details why:
- https://github.com/oceanprotocol/barge/blob/main/compose-files/thegraph.yml#L6 exposes the port 8000 in the container to the host network, thus it's accessible.
- "172.15.0.15" is the internal ip of the container; other containers in the network can access it. The docker network is isolated from host network unless you expose a port, therefore you cannot access it.
- and whereas Linux can make it more convenient via "bridge", MacOS doesn't support that [ref](https://docker-docs.uclv.cu/docker-for-mac/networking/#there-is-no-docker0-bridge-on-macos)
- In other words, per-container IP addressing is not possible on MacOS [Ref](https://docker-docs.uclv.cu/docker-for-mac/networking/#per-container-ip-addressing-is-not-possible).
