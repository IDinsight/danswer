re-deploy:
	cd /home/ec2-user/danswer/ && \
	git restore .
	cd /home/ec2-user/danswer/deployment/docker_compose && \
	echo "Current directory is: $$(pwd)" && \
	docker compose -p hubgpt down && \
	git pull origin prod && \
	docker compose -p hubgpt -f docker-compose.prod.yml up -d --build

send-slack-metrics:
	docker exec hubgpt-background-1 python /app/scripts/send_slack_report/send_slack_report.py

send-hubgpt-eval:
	cd /home/ec2-user/danswer/deployment/docker_compose && \
	docker compose -p hubgpt down && \
	docker compose -p hubgpt -f docker-compose.analytics.yml up -d --build
	sleep 150
	docker exec hubgpt-background-1 python /app/scripts/hubgpt_eval_automation.py
	cd /home/ec2-user/danswer/deployment/docker_compose && \
	docker compose -p hubgpt down && \
	docker compose -p hubgpt -f docker-compose.prod.yml up -d --build

