BOT_DIR = ./src
DOCKER_COMPOSE_FILE = ./docker-compose.yaml

build:
	docker-compose -f $(DOCKER_COMPOSE_FILE) build

up:
	docker-compose -f $(DOCKER_COMPOSE_FILE) up -d

down:
	docker-compose -f $(DOCKER_COMPOSE_FILE) down

logs:
	docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f

clean:
	docker-compose -f $(DOCKER_COMPOSE_FILE) down --volumes --rmi all

rebuild: down build up

reup: down up

help:
	@echo "Доступные команды:"
	@echo "  build       - Собрать Docker контейнеры"
	@echo "  up          - Запустить Docker контейнеры в фоновом режиме"
	@echo "  down        - Остановить и удалить Docker контейнеры"
	@echo "  logs        - Просмотреть логи Docker контейнеров"
	@echo "  clean       - Удалить все контейнеры, образы и тома (осторожно!)"
	@echo "  rebuild     - Пересобрать и перезапустить Docker контейнеры"
	@echo "  reup        - Перезапустить контейнеры"
