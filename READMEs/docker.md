# Running with Docker

## Building the Docker Image

To build the Docker image, follow these steps:

- Navigate to the root directory of the project.
- Run the following command:

```bash
docker build -t pdrbackend .
```

This command builds the Docker image and tags it with the name `pdrbackend`. Feel free to replace `pdrbackend` with whatever you want to name your Docker image.

## Running a Module with Docker

To run a specific module (for example `trader`), run the following command:

```bash
docker run --name pdr_trader_container -it pdrbackend trader

$ Running main.py for trader...
```

This will run the `trader` module. You can replace `trader` with the name of any other module in the `pdr_backend` directory except `utils` since it's not a module.