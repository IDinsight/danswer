# This script stores all SQL queries which are used
# to get HubGPT usage stats

SLACK_MESSAGES_QUERY = """SELECT COUNT(*)
    FROM chat_session
    WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') -
    INTERVAL '7 days')
    AND user_id IS NULL
"""

WEB_MESSAGES_QUERY = """SELECT COUNT(*)
    FROM chat_session
    WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') -
    INTERVAL '7 days')
    AND user_id IS NOT NULL
"""

WEB_USERS_QUERY = """
    SELECT COUNT(DISTINCT user_id)
    FROM chat_session
    WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') -
    INTERVAL '7 days')
    AND user_id IS NOT NULL
"""
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
