# pdr-backend

## Run bots (agents)

- **[Run trader bot](READMEs/trader.md)** - consume predictions, trade, make $

(If you're a predictoor or trader, you can safely ignore the rest of this README.)

## Settings: PPSS

A "ppss" yaml file, like [`ppss.yaml`](ppss.yaml), holds parameters for all bots and simulation flows.

- We follow the idiom "pp" = problem setup (what to solve), "ss" = solution strategy (how to solve).
- `PRIVATE_KEY` is an exception; it's set as an envvar.

When you run a bot from the CLI, you specify your PPSS YAML file.

pdr has basic stdout logging, but supports customisations.
To customise logging, copy and edit the existing `logging.yaml`:

```console
cp logging.yaml my_logging.yaml
```

## CLI

(First, [install pdr-backend](READMEs/predictoor.md#install-pdr-backend-repo) first.)

To see CLI options, in console:

```console
pdr
```

This will output something like:

```text
Usage: pdr sim|trader|..

Main tools:
  pdr sim YAML_FILE
  pdr trader APPROACH YAML_FILE livemock|livereal (FIXME)
...
```

## Flows for core team

- Backend-dev - for `pdr-backend` itself
  - [Local dev flow](READMEs/dev.md)
  - [VPS dev flow](READMEs/vps.md)
  - [Dependency management](READMEs/dependencies.md)

## Repo structure

This repo implements all bots in Predictoor ecosystem. Here are each of the sub-directories in the repo.

Main bots & user tools:

- `trader` - buy aggregated predictions, then trade
- `sim` - experiments / simulation flow

Mid-level building blocks:

- `cli` - implementation of CLI
- `ppss` - implements settings

Data-level building blocks:

- `ohlcv` - financial data pipeline
- `aimodel` - AI/ML modeling engine
- `lake` - data lake and analytics tools

Lower-level utilities:

- `util` - function-based tools
