# DEATH METAL DISCO

A database (-> "disobase") with django web app to manage my record collection. WIP ...

## Setup

```bash
direnv allow        # activates the uv-managed venv for this folder
uv sync              # installs dependencies (app deps + dev tools)
```

Create `config_dev.yaml` in the project root (gitignored, not included in the repo) with:

```yaml
DJANGO:
  SECRET_KEY: <your-secret-key>
  DEBUG: True

DISCOGS:
  USER-AGENT: <app-name>/1.0
  CONSUMER_KEY: <discogs-consumer-key>
  CONSUMER_SECRET: <discogs-consumer-secret>
  OAUTH_TOKEN: <discogs-oauth-token>
  OAUTH_TOKEN_SECRET: <discogs-oauth-token-secret>
```

Then create the database and (optionally) an admin user:

```bash
uv run python app/manage.py migrate
uv run python app/manage.py createsuperuser
```

## Run web app

From the project root, type:

```bash
uv run python app/manage.py runserver
```

It will open in your browser at `http://127.0.0.1:8000/`

## Management Commands

Run standalone tools from the project root.

### Update Discogs metadata

```bash
# list records missing a valid discogs_id
uv run python app/manage.py update_discogs list

# update the first record without a valid discogs_id
uv run python app/manage.py update_discogs

# update a specific record by ID
uv run python app/manage.py update_discogs 123
```

## Resources

### Discogs API

See notebook in dev folder, based on:

- [Authentication with oauth2](https://github.com/jesseward/discogs-oauth-example/blob/master/discogs_example.py)
- [Fetching data with discogs-client](https://python3-discogs-client.readthedocs.io/en/latest/fetching_data_repl.html)


## Refactoring 2026

### Prio 1

- update_discogs
  - update README
  - use rich for markdown and can I use typer here? 
- create 
- pass formatting checks
- resolve TODOs

### Prio 2

- use harlequin as a frontend for sqlite
- Ask where it can be deployed cheaply, what has to be true for deployment ...

### Prio 3

- revert the Dump, reinsert the dumped records in the DB, but with a Deleted timestamp
- read WHERE Deleted is NULL for all usecases
