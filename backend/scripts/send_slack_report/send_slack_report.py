import json
import os

import pandas as pd
from initial_query_classification import label_question
from openai import OpenAI
from queries import INITIAL_MESSAGES_QUERY
from queries import SLACK_MESSAGES_QUERY
from queries import WEB_MESSAGES_QUERY
from queries import WEB_USERS_QUERY
from slack_sdk import WebClient
from sqlalchemy import create_engine
from sqlalchemy import text

from danswer.utils.logger import setup_logger

logger = setup_logger()


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
    logger.info("Connecting to SQL database")
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
    logger.info("Counts retrieved")
    return slack_messages, web_messages, web_users


def classify_initial_queries():
    engine = get_engine()
    with engine.connect() as connection:
        df = pd.read_sql_query(INITIAL_MESSAGES_QUERY, connection)
        logger.info("Initial queries recieved")
        client = OpenAI(api_key=os.environ["GEN_AI_API_KEY"])
        label_series = df["initial_query"].map(lambda x: label_question(x, client))
        logger.info("Labelling complete")
        tally_json = json.loads(label_series.value_counts().to_json())
        classifications = ""
        total_initial_queries = sum(tally_json.values())
        for k, v in tally_json.items():
            percentage = v / total_initial_queries * 100
            classifications += f"There were {v} queries (representing {percentage:.1f}% of\
 all initial queries) about {k}\n"
        return classifications


def create_message(slack_messages, web_messages, web_users, classifications):
    message = (
        f"Hello Users!\n\n"
        f"Here are some updates from HubGPT regarding the last 7 days:\n"
        f"- {slack_messages}: Slack messages in the last 7 days.\n"
        f"- {web_messages}: Web App messages in the last 7 days.\n"
        f"- {web_users}: Unique users on the Web App.\n"
        "Usage breakdown:\n"
        f"{classifications}"
    )
    return message


def send_message(user_id, message):
    SLACK_TOKEN = os.environ["SLACK_BOT_TOKEN"]
    if not SLACK_TOKEN:
        logger.debug(
            "Slack OAuth token not provided. Check env prod template for guidance"
        )
        return None
    logger.info("Initializing Slack client")

    slack_client = WebClient(token=SLACK_TOKEN)

    logger.info("Sending Slack message")
    # Send a message to the user
    slack_client.chat_postMessage(channel=user_id, text=message)
    logger.info("Message sent")
    return None


def send_usage_report_to_slack(user_id):
    slack, web, web_users = get_counts()
    classifications = classify_initial_queries()
    message = create_message(slack, web, web_users, classifications)
    send_message(user_id, message)

    return None


if __name__ == "__main__":
    USER_ID = os.environ["METRICS_CHANNEL_ID"]
    if not USER_ID:
        logger.debug(
            "Slack Metrics Channel ID token not provided. \
Check env prod template for guidance"
        )
    else:
        logger.info("Starting Slack usage report")
        send_usage_report_to_slack(USER_ID)
