# Cortext Pipelines

## Prerequisites

- uv package manage
- docker
- python 3.12+

## Project Structure

## Configure Environment

1. Create a `.env` file** from the .env.example template file

2. **Set required variables** in your `.env` file:

## Start Services

You can run required services as docker containers. The `infra` folder defines these docker assets. To start the docker containers, run this from the terminal:

``` bash
make up 
```

After the postgres docker container is started and healthy, you can run the following command to get information about the Dagster instance and confirm that it is persisting metadata to postgres

   ```bash
   uv run dagster instance info
   ```

Look for the following in the ouput

- Storage: `PostgresRunStorage`
- Event Log: `PostgresEventLogStorage`
- Schedule Storage: `PostgresScheduleStorage`

## Run Pipeline

Run this from the terminal:

```bash
uv run dagster dev
```

The Dagster web app is available at http://localhost:3000 in your browser

## Learn more

To learn more about this template and Dagster in general:

- [Dagster Documentation](https://docs.dagster.io/)
- [Dagster University](https://courses.dagster.io/)
- [Dagster Slack Community](https://dagster.io/slack)
