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
WITH subquery AS (
    SELECT cm.time_sent, cs.user_id, cm.message, cm.id, cf.is_positive, cf.feedback_text,
           ROW_NUMBER() OVER (PARTITION BY cm.chat_session_id ORDER BY cm.time_sent ASC) AS rn
    FROM chat_message cm
    LEFT JOIN chat_session cs ON cs.id = cm.chat_session_id
    LEFT JOIN chat_feedback cf ON cf.chat_message_id = cm.id
    WHERE cm.time_sent >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days'
      AND cm.message_type = 'USER'
)
SELECT time_sent, user_id, message, id, is_positive, feedback_text
FROM subquery
WHERE rn = 1
ORDER BY time_sent ASC;
"""
