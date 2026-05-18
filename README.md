# Overview 
This is a FastAPI template inspired by Django structure and features. 
- SQLAlchemy is used to replace Django's ORM
- Alembic is used to mimic Django's Migration
- [Makefile](https://makefiletutorial.com) is used to centralize commands
- UV to handle project environment

## Prerequisite
*click for installation guide/site*
1. [UV](https://docs.astral.sh/uv/getting-started/installation/)
2. [Docker](https://www.docker.com/products/docker-desktop/)

## Architecture
```
project/
    |- main.py
    |- core/    --> Project's core files
        |- config.py
        |- routes.py        --> Django-inspired project root urls.py
    |- app/
        |- models.py        --> Django-inspired models.py
        |- repository.py    --> models related functions
        |- schema.py        --> Django-inspired serializers.py
        |- services.py      --> Django-inspired views.py
        |- routes.py        --> Django-inspired app urls.py

tests/  --> project's test
```


## Setting up the project for development
Once you cloned this repo, you'll need to run the following command:
```bash
    make initproject
```

## Important Commands
### 1. Running the server
#### For development (hot-reload enabled)
```bash
    make runserver
```

### 2. Handling Database Migrations
#### Upgrading models/tables
```bash
    make migrate -m "migration_name"
```
note that if you created, you have to register the model at `app/db/migrations/env.py` first before running this command

#### Rolling back the last migration
```bash
    make rollback
```

### For more commands, type `make` on the terminal.

