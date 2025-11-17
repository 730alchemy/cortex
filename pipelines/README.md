# Cortext Pipelines

## Project Structure

## Run Pipeline

### Configuration

Before running the pipeline, you need to configure environment variables:

1. **Create a `.env` file** from the example template:
   ```bash
   cp .env.example .env
   ```

2. **Set required variables** in your `.env` file:
   - `INPUT_DIR` - The directory path that the file monitoring sensor will watch for new files

3. **Note**: The `.env` file is gitignored and should never be committed to version control. Use `.env.example` as a template for documenting required variables.

### Execution

```bash
uv run dagster dev
```

The Dagster web app is available at http://localhost:3000 in your browser

## Learn more

To learn more about this template and Dagster in general:

- [Dagster Documentation](https://docs.dagster.io/)
- [Dagster University](https://courses.dagster.io/)
- [Dagster Slack Community](https://dagster.io/slack)
