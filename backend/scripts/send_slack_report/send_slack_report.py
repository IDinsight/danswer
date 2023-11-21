import os

import yaml
from queries import SLACK_MESSAGES_QUERY
from queries import WEB_MESSAGES_QUERY
from queries import WEB_USERS_QUERY
from slack_sdk import WebClient
from sqlalchemy import create_engine
from sqlalchemy import text


def get_engine():
    POSTGRES_USER = os.environ.get("POSTGRES_USER") or "postgres"
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD") or "password"
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST") or "localhost"
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT") or "5432"
    POSTGRES_DB = os.environ.get("POSTGRES_DB") or "postgres"

    engine = create_engine(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    return engine


def get_counts():
    engine = get_engine()

    with engine.connect() as connection:
        num_messages = connection.execute(text(SLACK_MESSAGES_QUERY))
        slack_messages = num_messages.fetchone()[0]

    with engine.connect() as connection:
        unique_users = connection.execute(text(WEB_MESSAGES_QUERY))
        web_messages = unique_users.fetchone()[0]

    with engine.connect() as connection:
        unique_users = connection.execute(text(WEB_USERS_QUERY))
        web_users = unique_users.fetchone()[0]

    return slack_messages, web_messages, web_users


def create_message(slack_messages, web_messages, web_users):
    message = (
        f"Hello Users!\n\n"
        f"Here are some updates from HubGPT regarding the last 7 days:\n"
        f"- {slack_messages}: Slack messages in the last 7 days.\n"
        f"- {web_messages}: Web App messages in the last 7 days.\n"
        f"- {web_users}: Unique users on the Web App."
    )
    return message


def send_message(user_id, message):
    # Get Slack token from yaml
    with open("secrets.yaml", "r") as file:
        secrets = yaml.safe_load(file)

    SLACK_TOKEN = secrets["SLACK_BOT_TOKEN"]
    slack_client = WebClient(token=SLACK_TOKEN)

    print("Sending message")
    # Send a message to the user
    slack_client.chat_postMessage(channel=user_id, text=message)
    print("Message sent")
    return None


def send_usage_report_to_slack(user_id):
    slack, web, web_users = get_counts()
    message = create_message(slack, web, web_users)
    send_message(user_id, message)

    return None


if __name__ == "__main__":
    USER_ID = "C05K8F6RXU3"
    print("Starting...")
    # send_usage_report_to_slack(USER_ID)
