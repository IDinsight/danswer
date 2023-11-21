# This script stores all SQL queries which are used
# to get HubGPT usage stats

SLACK_MESSAGES_QUERY = """SELECT COUNT(*)
    FROM query_event
    WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') -
    INTERVAL '7 days')
    AND user_id IS NULL
"""

WEB_MESSAGES_QUERY = """SELECT COUNT(*)
    FROM query_event
    WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') -
    INTERVAL '7 days')
    AND user_id IS NOT NULL
"""

WEB_USERS_QUERY = """
    SELECT COUNT(DISTINCT user_id)
    FROM query_event
    WHERE (time_created >= (NOW() AT TIME ZONE 'UTC') -
    INTERVAL '7 days')
    AND user_id IS NOT NULL
"""
