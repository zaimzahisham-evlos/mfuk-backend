.DEFAULT_GOAL := help

.PHONY: runserver stopserver restartserver clean tests migrate rollback createmodule help

help: # Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

initproject: ## Initialize the project. Run this when you first clone the repository to set up necessary files and configurations.
	@echo "Initializing the project..."
	uv sync
	cp .env.example .env
	cp docker-compose.override.example.yml docker-compose.override.yml

runserver: ## Build and start the containers. Include .dev for development (with file watching and auto-reload).
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
	docker exec fastapi_backend uv sync
	docker exec fastapi_backend alembic upgrade head
	docker exec fastapi_backend python app/db/seed/superadmin.py
	docker exec fastapi_backend python app/db/seed/permissions.py

stopserver: ## Stop server.
	docker compose -f docker-compose.yml -f docker-compose.override.yml down

restartserver: ## Restart the server by stopping and then starting it again.
	make stopserver 
	make runserver

resetserver: ## Reset the server by stopping, removing containers, networks, volumes, and images, and then starting it again.
	docker compose -f docker-compose.yml -f docker-compose.override.yml down -v
	make runserver

clean: ## Clean the project by stopping, removing containers, networks, volumes, and images.
	docker compose -f docker-compose.yml -f docker-compose.override.yml down -v

tests: ## Run the tests.
	@$(eval path=$(filter-out $@,$(MAKECMDGOALS)))
	docker exec fastapi_backend pytest $(path)

logs: ## View the logs of the backend service.
	docker compose -f docker-compose.yml -f docker-compose.override.yml logs -f backend

migrate: ## Create and apply a migration. Usage: make migrate your message here
	@$(eval MSG=$(filter-out $@,$(MAKECMDGOALS)))
	@if [ -z "$(MSG)" ]; then echo "Error: message is required. Use: make migrate <message>"; exit 1; fi
	docker exec fastapi_backend alembic revision --autogenerate -m "$(MSG)"
	docker exec fastapi_backend alembic upgrade head

rollback: ## Rollback the last migration
	docker exec fastapi_backend alembic downgrade -1

createmodule: ## Create a new module. Usage: make createmodule <name> <model_name1> <model_name2> ...
	@$(eval args=$(filter-out $@,$(MAKECMDGOALS)))
	@$(eval name=$(firstword $(args)))
	@$(eval models=$(wordlist 2,$(words $(args)),$(args)))
	@if [ -z "$(name)" ]; then echo "Error: 'name' is required. Use: make createmodule <name>"; exit 1; fi
	@if [ -d "app/$(name)" ]; then echo "Error: '$(name)' module already exists"; exit 1; fi
	mkdir -p app/$(name)
	touch app/$(name)/__init__.py
	touch app/$(name)/models.py
	touch app/$(name)/repository.py
	touch app/$(name)/schema.py
	touch app/$(name)/services.py
	touch app/$(name)/routes.py
	touch app/$(name)/helpers.py
	mkdir -p tests/integration/$(name)
	@if [ -z "$(models)" ]; then \
		touch tests/integration/$(name)/test_$(name)_create.py; \
		touch tests/integration/$(name)/test_$(name)_read.py; \
		touch tests/integration/$(name)/test_$(name)_update.py; \
		touch tests/integration/$(name)/test_$(name)_delete.py; \
	else \
		for model in $(models); do \
			mkdir -p tests/integration/$(name)/$$model; \
			touch tests/integration/$(name)/$$model/test_$${model}_create.py; \
			touch tests/integration/$(name)/$$model/test_$${model}_read.py; \
			touch tests/integration/$(name)/$$model/test_$${model}_update.py; \
			touch tests/integration/$(name)/$$model/test_$${model}_delete.py; \
		done; \
	fi

# Accept any target name as an argument to avoid "No rule to make target" errors
%:
	@: