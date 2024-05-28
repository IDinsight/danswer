# This file is used to demonstrate how to use the backend APIs directly
# In this case, the equivalent of asking a question in Danswer Chat in a new chat session
import datetime
import json
import os

import pandas as pd
import requests
from slack_sdk import WebClient

CSV_PATH = "/app/scripts/hubgpt_eval.csv"

def create_new_chat_session(danswer_url: str, api_key: str | None) -> int:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
    session_endpoint = danswer_url + "/api/chat/create-chat-session"

    response = requests.post(session_endpoint, headers=headers, json={"persona_id": 0})
    response.raise_for_status()

    new_session_id = response.json()["chat_session_id"]
    return new_session_id


def process_question(danswer_url: str, question: str, api_key: str | None) -> None:
    message_endpoint = danswer_url + "/api/chat/send-message"

    chat_session_id = create_new_chat_session(danswer_url, api_key)

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None

    data = {
        "message": question,
        "chat_session_id": chat_session_id,
        "parent_message_id": None,
        # Default Question Answer prompt
        "prompt_id": 0,
        # Not specifying any specific docs to chat to, we want to run a search
        "search_doc_ids": None,
        "retrieval_options": {
            "run_search": "always",
            "real_time": True,
            "enable_auto_detect_filters": False,
            # No filters applied, check all sources, document-sets, time ranges, etc.
            "filters": {},
        },
    }

    with requests.post(message_endpoint, headers=headers, json=data) as response:
        response.raise_for_status()
        response_str = ""
        for packet in response.iter_lines():
            response_text = json.loads(packet.decode())
            # Can also check "top_documents" to capture the streamed search results
            # that include the highest matching documents to the query
            # or check "message_id" to get the message_id used as parent_message_id
            # to create follow-up messages
            new_token = response_text.get("answer_piece")
            if new_token:
                response_str += new_token
        return response_str


def upload_to_slack(filename, channel_id):
    slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
    size = os.stat(filename).st_size
    response = slack_client.files_getUploadURLExternal(filename=filename, length=size)
    upload_url = response.data["upload_url"]
    file_id = response.data["file_id"]
    post_response = requests.post(url=upload_url, data=open(filename, "rb"))
    if post_response.status_code == 200:
        upload_response = slack_client.files_completeUploadExternal(
            files=[{"id": file_id, "title": "Monthly Performance Evaluation"}], channel_id=channel_id
        )
    return upload_response.status_code

if __name__ == "__main__":
    print("Starting query run")
    data = pd.read_csv(CSV_PATH)
    
    queries_list = data.Query.tolist()
    
    responses = []
    
    for num, query in enumerate(queries_list):
        print(f"Query {num+1}/{len(queries_list)}: {query}")
        response = process_question(
            # Change to staging for staging testing
            danswer_url="https://hubgpt.idinsight.io", question=query, api_key=None
        )
        responses.append(response)
        print(response)
        print("\n ------------------- \n")
        
    today_str = str(datetime.date.today())
    data[today_str] = responses
    
    # Record + send info
    data.to_csv(CSV_PATH, index = False)
    print("Complete")
    CHANNEL_ID = os.environ.get("METRICS_CHANNEL_ID")
    upload_to_slack(CSV_PATH, CHANNEL_ID)
