import json
import os

import pandas as pd
import plotly.express as px
import requests
from initial_query_classification import label_question
from openai import OpenAI
from queries import INITIAL_MESSAGES_QUERY
from queries import MEDIUMS
from queries import USAGE_QUERIES
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
    """Fetches counts based on the specified period from the global queries dictionary."""
    results = {"medium": [], "time_period": [], "count": []}

    engine = get_engine()

    with engine.connect() as connection:
        for period in USAGE_QUERIES.keys():
            for key, query in USAGE_QUERIES[period].items():
                result = connection.execute(text(query.replace("\n", "")))
                results["count"].append(result.scalar())
                results["medium"].append(key)
                results["time_period"].append(period)

    return pd.DataFrame(results)


def get_last_week_counts(df):
    """Take a DataFrame and returns a dictionary of counts ofr users
    from the last 7 days across Slack, Web and unique users"""
    last_week_count = {}
    for medium in MEDIUMS:
        count = df.query(f"time_period =='last_7_days' and medium == '{medium}'")[
            "count"
        ].iloc[0]
        last_week_count[medium] = count
    return last_week_count


def save_bar_plot(df, filename):
    fig = px.bar(df, x="medium", y="count", color="time_period", barmode="group")
    fig.write_image(file=filename, format="jpg")
    return filename


def upload_to_slack_and_delete(filename, channel_id):
    slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
    size = os.stat(filename).st_size
    response = slack_client.files_getUploadURLExternal(filename=filename, length=size)
    upload_url = response.data["upload_url"]
    file_id = response.data["file_id"]
    post_response = requests.post(url=upload_url, data=open(filename, "rb"))
    if post_response.status_code == 200:
        upload_response = slack_client.files_completeUploadExternal(
            files=[{"id": file_id, "title": "Metrics graph"}], channel_id=channel_id
        )
    # Clean up
    os.remove(filename)
    return upload_response.status_code


def classify_initial_queries():
    engine = get_engine()
    with engine.connect() as connection:
        df = pd.read_sql_query(INITIAL_MESSAGES_QUERY, connection)
        logger.info("Initial queries recieved")
        client = OpenAI(api_key=os.environ.get("GEN_AI_API_KEY"))
        label_series = df["initial_query"].map(lambda x: label_question(x, client))
        logger.info("Labelling complete")
        tally_json = json.loads(label_series.value_counts().to_json())
        classifications = ""
        total_initial_queries = sum(tally_json.values())
        for k, v in tally_json.items():
            percentage = v / total_initial_queries * 100
            classifications += f"{k}: {v} queries ({percentage:.1f}%)\n"
        return classifications


def create_message(last_week_count, classifications):
    message = (
        f"Hello Users!\n\n"
        f"Here are some updates from HubGPT regarding the last 7 days:\n"
        f"- {last_week_count['slack_messages']}: Slack messages in the last 7 days.\n"
        f"- {last_week_count['web_messages']}: Web App messages in the last 7 days.\n"
        f"- {last_week_count['distinct_web_users']}: Unique users on the Web App.\n"
        "Usage breakdown:\n"
        f"{classifications}"
    )
    return message


def send_message(user_id, message):
    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
    if not SLACK_BOT_TOKEN:
        logger.debug(
            "Slack OAuth token not provided. Check env prod template for guidance"
        )
        return None
    logger.info("Initializing Slack client")

    slack_client = WebClient(token=SLACK_BOT_TOKEN)

    logger.info("Sending Slack message")
    # Send a message to the user
    slack_client.chat_postMessage(channel=user_id, text=message)
    logger.info("Message sent")
    return None


def send_usage_report_to_slack(channel_id):
    counts_df = get_counts()
    classifications = classify_initial_queries()

    last_week_counts = get_last_week_counts(counts_df)

    file = save_bar_plot(counts_df, "metrics.jpg")

    message = create_message(last_week_counts, classifications)

    send_message(channel_id, message)
    upload_status = upload_to_slack_and_delete(file, channel_id)

    return upload_status


if __name__ == "__main__":
    try:
        CHANNEL_ID = os.environ.get("METRICS_CHANNEL_ID")
        if CHANNEL_ID:
            logger.info("Starting Slack usage report")
            send_usage_report_to_slack(CHANNEL_ID)
        else:
            logger.warning("Slack Metrics Channel ID token not provided.")
            logger.warning("Check env prod template for guidance.")
    except Exception as e:
        logger.exception("An error occurred while sending usage report to Slack: %s", e)
