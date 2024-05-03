# This script stores all SQL queries which are used
# to get HubGPT usage stats

MEDIUMS = ["slack_messages", "web_messages", "distinct_web_users"]


USAGE_QUERIES = {
    "last_7_days": {
        "slack_messages": """
            SELECT COUNT(*)
            FROM chat_session
            WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days')
            AND user_id IS NULL
        """,
        "web_messages": """
            SELECT COUNT(*)
            FROM chat_session
            WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days')
            AND user_id IS NOT NULL
        """,
        "distinct_web_users": """
            SELECT COUNT(DISTINCT user_id)
            FROM chat_session
            WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days')
            AND user_id IS NOT NULL
        """,
    },
    "day_14_to_7": {
        "slack_messages": """
            SELECT COUNT(*)
            FROM chat_session
            WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '14 days')
            AND time_created < (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days'
            AND user_id IS NULL
        """,
        "web_messages": """
            SELECT COUNT(*)
            FROM chat_session
            WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '14 days')
            AND time_created < (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days'
            AND user_id IS NOT NULL
        """,
        "distinct_web_users": """
            SELECT COUNT(DISTINCT user_id)
            FROM chat_session
            WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '14 days')
            AND time_created < (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days'
            AND user_id IS NOT NULL
        """,
    },
    "day_35_to_28": {
        "slack_messages": """
            SELECT COUNT(*)
            FROM chat_session
            WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '35 days')
            AND time_created < (NOW() AT TIME ZONE 'UTC') - INTERVAL '28 days'
            AND user_id IS NULL
        """,
        "web_messages": """
            SELECT COUNT(*)
            FROM chat_session
            WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '35 days')
            AND time_created < (NOW() AT TIME ZONE 'UTC') - INTERVAL '28 days'
            AND user_id IS NOT NULL
        """,
        "distinct_web_users": """
            SELECT COUNT(DISTINCT user_id)
            FROM chat_session
            WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '35 days')
            AND time_created < (NOW() AT TIME ZONE 'UTC') - INTERVAL '28 days'
            AND user_id IS NOT NULL
        """,
    },
}
INITIAL_MESSAGES_QUERY = """
    SELECT message as initial_query FROM (
        SELECT *,
            ROW_NUMBER() OVER (PARTITION BY chat_session_id ORDER BY time_sent ASC) as rn
        FROM chat_message
        WHERE (time_sent >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days')
        AND (message_type = 'USER')
    ) sub
    WHERE sub.rn = 1
    ORDER BY sub.time_sent ASC;"""
