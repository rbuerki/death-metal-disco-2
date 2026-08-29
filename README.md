# DEATH METAL DISCO V2

A web app to manage my record collection. WIP ...

## Resources

### Discogs API

See notebook in dev folder, based on:

- [Authentication with oauth2](https://github.com/jesseward/discogs-oauth-example/blob/master/discogs_example.py)
- [Fetching data with discogs-client](https://python3-discogs-client.readthedocs.io/en/latest/fetching_data_repl.html)

### Trouble Shooting

- __Server not running__: Open WT as Admin and type `net start postgresql-x64-17` (you can double-check the service name by running `services.msc` in the windows console). You probably will then also have to start the pgAdmin tool and re-enter the password for the master user.

### Refactoring 2026

- Migrate to sqlite or other lightweight DB
- revert the Dump, reinsert the dumped records in the DB, but with a Deleted timestamp
- read WHERE Deleted is NULL for all usecases
- Ask where it can be deployed cheaply, what has to be true for deployment ...
