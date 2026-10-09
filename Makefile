.PHONY: up down build logs seed clean

up:
	docker compose -f infrastructure/docker-compose.yml up -d

down:
	docker compose -f infrastructure/docker-compose.yml down

build:
	docker compose -f infrastructure/docker-compose.yml build

logs:
	docker compose -f infrastructure/docker-compose.yml logs -f

seed:
	docker compose -f infrastructure/docker-compose.yml exec backend python app/scripts/seed_data.py

clean:
	docker compose -f infrastructure/docker-compose.yml down -v
