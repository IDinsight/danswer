SHELL=/bin/zsh

all:
	@echo ${SHELL}

run-dep-containers:
	cd deployment/docker_compose && \
	docker compose -f docker-compose.dev.yml -p danswer-stack up -d relational_db && \
	docker compose -f docker-compose.dev.yml -p danswer-stack up -d vector_db && \
	docker compose -f docker-compose.dev.yml -p danswer-stack up -d search_engine 

run-web-dev:
	cd web && \
	DISABLE_AUTH=true npm run dev 

run-backend-dev:
	cd backend && alembic upgrade head && \
	DISABLE_AUTH=True TYPESENSE_API_KEY=local_dev_typesense DYNAMIC_CONFIG_DIR_PATH=./dynamic_config_storage uvicorn danswer.main:app --reload --port 8080

run-background-dev:
	cd backend && \
	PYTHONPATH=. TYPESENSE_API_KEY=local_dev_typesense \
	DYNAMIC_CONFIG_DIR_PATH=./dynamic_config_storage python danswer/background/update.py

run-dev: run-dep-containers
	${MAKE} -j3 run-web-dev run-backend-dev run-background-dev

re-deploy:
	cd /home/ec2-user/danswer/deployment/docker_compose && \
	echo "Current directory is: $$(pwd)" && \
	docker compose -p danswer-stack down && \
	git pull origin prod && \
	docker compose -p danswer-stack -f docker-compose.prod.yml up -d --build

send-slack-metrics:
	docker exec danswer-stack-background-1 python /app/scripts/send_slack_report/send_slack_report.py

send-hubgpt-eval:
	cd /home/ec2-user/danswer/deployment/docker_compose && \
	docker compose -p danswer-stack -f docker-compose.analytics.yml up -d --build 
	sleep 150
	docker exec danswer-stack-background-1 python /app/scripts/hubgpt_eval_automation.py
	docker compose -p danswer-stack -f docker-compose.prod.yml up -d --build 

