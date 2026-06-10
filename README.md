# Overview 
This is a MFUK FastAPI Backend inspired by Django structure and features. 
- SQLAlchemy is used as Database ORM
- Alembic is used for Database Migration
- [Makefile](https://makefiletutorial.com) is used to centralize commands
- UV to handle project environment
- SeaweedFS as Object Storage System to handle images and files

## Prerequisites
*click for installation guide/site*
1. [UV](https://docs.astral.sh/uv/getting-started/installation/)
2. [Docker](https://www.docker.com/products/docker-desktop/)

## Architecture
```
Makefile                    <-- CLI tool for administrative commands
project/
    |- main.py
    |- core/                <-- Project's core files
        |- config.py        <-- Project configurations and environment settings
        |- routes.py        <-- Global URL routing/declarations
    |- app/                 <-- Application Component/Module (created via make createmodule)
        |- models.py        <-- Database blueprints / Data Layer
        |- repository.py    <-- Data Access Layer
        |- schema.py        <-- Data Validation/Serialization Layer
        |- services.py      <-- Logic Layer
        |- routes.py        <-- App-level URL routing/declarations

tests/                      <-- project's test
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
    make migrate migration_name
```

#### Rolling back the last migration
```bash
    make rollback
```

### For more commands, type `make` on the terminal.

