### Barge flow of calls

From getting barge going, here's how it calls specific pdr-backend components and passes arguments.

- user calls `/barge/start_ocean.sh` to get barge going
  - then, `start_ocean.sh` fills `COMPOSE_FILES` incrementally. Eg `COMPOSE_FILES+=" -f ${COMPOSE_DIR}/pdr-publisher.yml"`
     - `barge/compose-files/pdr-publisher.yml` sets:
       - `pdr-publisher: image: oceanprotocol/pdr-backend:${PDR_BACKEND_VERSION:-latest}`
       - `pdr-publisher: command: publisher`
       - `pdr-publisher: networks: backend: ipv4_address: 172.15.0.43`
       - `pdr-publisher: environment:`
         - `RPC_URL: ${NETWORK_RPC_URL}` (= `http://localhost:8545` via `start_ocean.sh`)
         - `ADDRESS_FILE: /root/.ocean/ocean-contracts/artifacts/address.json`
	 - (many `PRIVATE_KEY_*`)
	    
  - then, `start_ocean.sh` pulls the `$COMPOSE_FILES` as needed:
    - `[ ${FORCEPULL} = "true" ] && eval docker-compose "$DOCKER_COMPOSE_EXTRA_OPTS" --project-name=$PROJECT_NAME "$COMPOSE_FILES" pull`
     
  - then, `start_ocean.sh` runs docker-compose including all `$COMPOSE_FILES`:
    - `eval docker-compose "$DOCKER_COMPOSE_EXTRA_OPTS" --project-name=$PROJECT_NAME "$COMPOSE_FILES" up --remove-orphans`
    - it executes each of the `"command"` entries in compose files.
       - (Eg for pdr-publisher.yml, `"command" = "publisher ppss.yaml development"`)
       - Which then goes to `pdr-backend/entrypoint.sh` via `"python /app/pdr_backend/pdr $@"`
         - (where `@` is unpacked as eg `publisher ppss.yaml development`) [Ref](https://superuser.com/questions/1586997/what-does-symbol-mean-in-the-context-of#:).
	 - Then it goes through the usual CLI at `pdr-backend/pdr_backend/util/cli_module.py`


### How to make changes to calls

If you made a change to pdr-backend CLI interface, then barge must call using the updated CLI command.

How:
- change the relevant compose file's `"command"`. Eg change `barge/compose-files/pdr-publisher.yml`'s "command" value to `publisher ppss.yaml development`
- also, change envvar setup as needed. Eg in compose file, remove `RPC_URL` and `ADDRESS_FILE` entry.
- ultimately, ask: "does Docker have everything it needs to succesfully run the component?"

