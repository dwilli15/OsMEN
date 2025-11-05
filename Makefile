.PHONY: help start stop restart logs status pull-models setup clean check-operational

help:
	@echo "OsMEN - Management Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup             - Initial setup (copy .env, create dirs)"
	@echo "  make start             - Start all services"
	@echo "  make stop              - Stop all services"
	@echo "  make restart           - Restart all services"
	@echo "  make logs              - View all logs"
	@echo "  make status            - Check service status"
	@echo "  make check-operational - Run comprehensive operational check"
	@echo "  make pull-models       - Pull Ollama models"
	@echo "  make clean             - Remove all containers and volumes"
	@echo ""

setup:
	@echo "Setting up OsMEN..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file"; fi
	@mkdir -p langflow/{flows,config} n8n/workflows postgres/init agents/{boot_hardening,daily_brief,focus_guardrails,content_editing,research_intel} tools/{simplewall,sysinternals,ffmpeg} docs logs
	@echo "Setup complete! Edit .env and run 'make start'"

start:
	@echo "Starting OsMEN services..."
	docker-compose up -d
	@echo "Services started!"
	@echo "Langflow: http://localhost:7860"
	@echo "n8n: http://localhost:5678"
	@echo "Qdrant: http://localhost:6333/dashboard"

stop:
	@echo "Stopping OsMEN services..."
	docker-compose down
	@echo "Services stopped!"

restart:
	@echo "Restarting OsMEN services..."
	docker-compose restart
	@echo "Services restarted!"

logs:
	docker-compose logs -f

status:
	@echo "OsMEN Service Status:"
	@docker-compose ps

pull-models:
	@echo "Pulling Ollama models..."
	docker exec -it osmen-ollama ollama pull llama2
	docker exec -it osmen-ollama ollama pull mistral
	@echo "Models pulled successfully!"

clean:
	@echo "WARNING: This will remove all containers and volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "Cleaned up!"; \
	fi

test-agents:
	@echo "Testing agents..."
	python agents/boot_hardening/boot_hardening_agent.py
	python agents/daily_brief/daily_brief_agent.py
	python agents/focus_guardrails/focus_guardrails_agent.py

backup:
	@echo "Creating backup..."
	@mkdir -p backups
	docker exec osmen-postgres pg_dumpall -U postgres > backups/postgres-$(shell date +%Y%m%d-%H%M%S).sql
	tar czf backups/config-$(shell date +%Y%m%d-%H%M%S).tar.gz n8n/workflows langflow/flows .env
	@echo "Backup complete!"

check-operational:
	@echo "Running operational status check..."
	@python3 check_operational.py
