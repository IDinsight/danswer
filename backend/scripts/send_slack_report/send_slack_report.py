import json
import os
import re

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

# Global Variables and Paths
CSV_PATH = "/app/scripts/send_slack_report/all_data.csv"
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
GEN_AI_API_KEY = os.environ.get("GEN_AI_API_KEY")
METRICS_CHANNEL_ID = os.environ.get("METRICS_CHANNEL_ID")

# Setup Logger
logger = setup_logger()


def get_engine():
    """Create and return a SQLAlchemy engine."""
    engine = create_engine(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    return engine


def execute_numerical_query(engine, query):
    """Execute a SQL query and return the resulting number."""
    with engine.connect() as connection:
        result = connection.execute(text(query.replace("\n", "")))
        return result.scalar()


def get_counts():
    """Fetch usage counts based on the specified period from the global queries dictionary."""
    results = {"medium": [], "time_period": [], "count": []}
    engine = get_engine()

    for period in USAGE_QUERIES.keys():
        for key, query in USAGE_QUERIES[period].items():
            count = execute_numerical_query(engine, query)
            results["count"].append(count)
            results["medium"].append(key)
            results["time_period"].append(period)

    return pd.DataFrame(results)


def get_last_week_counts(df):
    """Return counts for the last 7 days across different mediums."""
    last_week_count = {}
    for medium in MEDIUMS:
        count = df.query(f"time_period == 'last_7_days' and medium == '{medium}'")[
            "count"
        ].iloc[0]
        last_week_count[medium] = count
    return last_week_count


def save_bar_plot(df, filename):
    """Save a bar plot of the data and return the filename."""
    fig = px.bar(df, x="medium", y="count", color="time_period", barmode="group")
    fig.write_image(file=filename, format="jpg")
    return filename


def upload_file_to_slack(filename, channel_id, title, delete_after_upload=False):
    """Upload a file to Slack and optionally delete it locally."""
    slack_client = WebClient(token=SLACK_BOT_TOKEN)
    size = os.stat(filename).st_size
    response = slack_client.files_getUploadURLExternal(filename=filename, length=size)
    upload_url = response["upload_url"]
    file_id = response["file_id"]

    with open(filename, "rb") as file:
        post_response = requests.post(url=upload_url, data=file)

    if post_response.status_code == 200:
        slack_client.files_completeUploadExternal(
            files=[{"id": file_id, "title": title}], channel_id=channel_id
        )
        if delete_after_upload:
            os.remove(filename)
        return 200
    else:
        logger.error(f"Failed to upload {filename} to Slack.")
        return post_response.status_code


def categorize(text):
    """Categorize the given text based on predefined categories."""
    categories = ["PROJECTS", "POLICIES", "RESOURCES", "TEAMS", "MISCELLANEOUS"]
    regex_pattern = r"\b(" + "|".join(categories) + r")\b"
    match = re.search(regex_pattern, text, re.IGNORECASE)
    return match.group(1).upper() if match else "MISCELLANEOUS"


def gather_and_combine_data():
    """Gather past week's data, concatenate with existing data, and dispatch as a CSV."""
    engine = get_engine()
    with engine.connect() as connection:
        df = pd.read_sql_query(INITIAL_MESSAGES_QUERY, connection)
    logger.info("Initial queries received")

    # Fill missing user IDs with 'SLACK'
    df["user_id"] = df["user_id"].fillna("SLACK")
    clean_weekly = df.drop_duplicates(subset="id").copy()
    clean_weekly["time_sent"] = clean_weekly["time_sent"].dt.date

    # Combine with historic data
    overlap_ids = clean_weekly["id"]
    full_df = pd.read_csv(CSV_PATH)
    clean_all_time_df = full_df[~full_df["id"].isin(overlap_ids)]
    combined_df = (
        pd.concat([clean_all_time_df, clean_weekly])
        .sort_values(by="time_sent")
        .reset_index(drop=True)
    )
    combined_df.to_csv(CSV_PATH, index=False)
    logger.info("Combined with historic data and saved to CSV")

    return clean_weekly


def classify_initial_queries(clean_weekly):
    """Classify the initial queries and prepare a summary."""
    # Label data using OpenAI
    client = OpenAI(api_key=GEN_AI_API_KEY)
    clean_weekly["labels"] = clean_weekly["message"].apply(
        lambda x: label_question(x, client)
    )
    clean_weekly["labels"] = clean_weekly["labels"].apply(categorize)
    logger.info("Labelling complete")

    # Prepare classification summary
    tally_json = json.loads(clean_weekly["labels"].value_counts().to_json())
    total_initial_queries = sum(tally_json.values())
    classifications = "\n".join(
        f"{k}: {v} queries ({v / total_initial_queries * 100:.1f}%)"
        for k, v in tally_json.items()
    )
    return classifications


def create_message(last_week_count, classifications):
    """Create a summary message to send to Slack."""
    return (
        f"Hello Users!\n\n"
        f"Here are some updates from HubGPT regarding the last 7 days:\n"
        f"- {last_week_count.get('slack_messages', 0)} Slack messages in the last 7 days.\n"
        f"- {last_week_count.get('web_messages', 0)} Web App messages in the last 7 days.\n"
        f"- {last_week_count.get('distinct_web_users', 0)} Unique users on the Web App.\n"
        "Usage breakdown:\n"
        f"{classifications}"
    )


def send_message(channel_id, message):
    """Send a message to the specified Slack channel."""
    try:
        slack_client = WebClient(token=SLACK_BOT_TOKEN)
        slack_client.chat_postMessage(channel=channel_id, text=message)
        logger.info("Message sent to Slack channel")
    except Exception as e:
        logger.error(f"Failed to send message to Slack channel {channel_id}: {e}")


def send_usage_report_to_slack(channel_id):
    """Generate and send the usage report to Slack."""
    counts_df = get_counts()
    clean_weekly = gather_and_combine_data()
    classifications = classify_initial_queries(clean_weekly)
    last_week_counts = get_last_week_counts(counts_df)
    plot_filename = save_bar_plot(counts_df, "metrics.jpg")
    message = create_message(last_week_counts, classifications)

    send_message(channel_id, message)

    upload_file_to_slack(
        plot_filename, channel_id, "Metrics graph", delete_after_upload=True
    )
    upload_file_to_slack(CSV_PATH, channel_id, "Historic data")


if __name__ == "__main__":
    try:
        if METRICS_CHANNEL_ID:
            logger.info("Starting Slack usage report")
            send_usage_report_to_slack(METRICS_CHANNEL_ID)
        else:
            logger.warning(
                "Slack Metrics Channel ID token not provided. Check env prod template for guidance."
            )
    except Exception as e:
        logger.exception(
            "An error occurred while sending usage report to Slack", exc_info=e
        )
