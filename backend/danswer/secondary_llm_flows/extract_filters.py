import json
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from dateutil.parser import parse

from danswer.configs.app_configs import DISABLE_TIME_FILTER_EXTRACTION
from danswer.llm.build import get_default_llm
from danswer.llm.utils import dict_based_prompt_to_langchain_prompt
from danswer.server.models import QuestionRequest
from danswer.utils.logger import setup_logger
from danswer.utils.timing import log_function_time

logger = setup_logger()


def best_match_time(time_str: str) -> datetime | None:
    preferred_formats = ["%m/%d/%Y", "%m-%d-%Y"]

    for fmt in preferred_formats:
        try:
            # As we don't know if the user is interacting with the API server from
            # the same timezone as the API server, just assume the queries are UTC time
            # the few hours offset (if any) shouldn't make any significant difference
            dt = datetime.strptime(time_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    # If the above formats don't match, try using dateutil's parser
    try:
        dt = parse(time_str)
        return (
            dt.astimezone(timezone.utc)
            if dt.tzinfo
            else dt.replace(tzinfo=timezone.utc)
        )
    except ValueError:
        return None


@log_function_time()
def extract_time_filter(query: str) -> tuple[datetime | None, bool]:
    """Returns a datetime if a hard time filter should be applied for the given query
    Additionally returns a bool, True if more recently updated Documents should be
    heavily favored"""

    def _get_time_filter_messages(query: str) -> list[dict[str, str]]:
        messages = [
            {
                "role": "system",
                "content": "You are a tool to identify time filters to apply to a user query for "
                "a downstream search application. The downstream application is able to "
                "use a recency bias or apply a hard cutoff to remove all documents "
                "before the cutoff. Identify the correct filters to apply for the user "
                "query.\n\n"
                "Always answer with ONLY a json which contains the keys "
                '"filter_type", "filter_value", "value_multiple" and "date".\n\n'
                'The valid values for "filter_type" are "hard cutoff", '
                '"favors recent", or "not time sensitive".\n'
                'The valid values for "filter_value" are "day", "week", "month", '
                '"quarter", "half", or "year".\n'
                'The valid values for "value_multiple" is any number.\n'
                'The valid values for "date" is a date in format MM/DD/YYYY.',
            },
            {
                "role": "user",
                "content": "What documents in Confluence were written in the last two quarters",
            },
            {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "filter_type": "hard cutoff",
                        "filter_value": "quarter",
                        "value_multiple": 2,
                    }
                ),
            },
            {"role": "user", "content": "What's the latest on project Corgies?"},
            {
                "role": "assistant",
                "content": json.dumps({"filter_type": "favor recent"}),
            },
            {
                "role": "user",
                "content": "Which customer asked about security features in February of 2022?",
            },
            {
                "role": "assistant",
                "content": json.dumps(
                    {"filter_type": "hard cutoff", "date": "02/01/2022"}
                ),
            },
            {"role": "user", "content": query},
        ]
        return messages

    def _extract_time_filter_from_llm_out(
        model_out: str,
    ) -> tuple[datetime | None, bool]:
        """Returns a datetime for a hard cutoff and a bool for if the"""
        try:
            model_json = json.loads(model_out, strict=False)
        except json.JSONDecodeError:
            return None, False

        # If filter type is not present, just assume something has gone wrong
        # Potentially model has identified a date and just returned that but
        # better to be conservative and not identify the wrong filter.
        if "filter_type" not in model_json:
            return None, False

        if "hard" in model_json["filter_type"] or "recent" in model_json["filter_type"]:
            favor_recent = "recent" in model_json["filter_type"]

            if "date" in model_json:
                extracted_time = best_match_time(model_json["date"])
                if extracted_time is not None:
                    return extracted_time, favor_recent

            time_diff = None
            multiplier = 1.0

            if "value_multiple" in model_json:
                try:
                    multiplier = float(model_json["value_multiple"])
                except ValueError:
                    pass

            if "filter_value" in model_json:
                filter_value = model_json["filter_value"]
                if "day" in filter_value:
                    time_diff = timedelta(days=multiplier)
                elif "week" in filter_value:
                    time_diff = timedelta(weeks=multiplier)
                elif "month" in filter_value:
                    # Have to just use the average here, too complicated to calculate exact day
                    # based on current day etc.
                    time_diff = timedelta(days=multiplier * 30.437)
                elif "quarter" in filter_value:
                    time_diff = timedelta(days=multiplier * 91.25)
                elif "year" in filter_value:
                    time_diff = timedelta(days=multiplier * 365)

            if time_diff is not None:
                current = datetime.now(timezone.utc)
                return current - time_diff, favor_recent

            # If we failed to extract a hard filter, just pass back the value of favor recent
            return None, favor_recent

        return None, False

    messages = _get_time_filter_messages(query)
    filled_llm_prompt = dict_based_prompt_to_langchain_prompt(messages)
    model_output = get_default_llm().invoke(filled_llm_prompt)
    logger.debug(model_output)

    return _extract_time_filter_from_llm_out(model_output)


def extract_question_time_filters(
    question: QuestionRequest,
    disable_llm_extraction: bool = DISABLE_TIME_FILTER_EXTRACTION,
) -> tuple[datetime | None, bool]:
    time_cutoff = question.filters.time_cutoff
    favor_recent = question.favor_recent
    # Frontend needs to be able to set this flag so that if user deletes the time filter,
    # we don't automatically reapply it. The env variable is a global disable of this feature
    # for the sake of latency
    if not question.enable_auto_detect_filters or disable_llm_extraction:
        if favor_recent is None:
            favor_recent = False
        return time_cutoff, favor_recent

    llm_cutoff, llm_favor_recent = extract_time_filter(question.query)

    # For all extractable filters, don't overwrite the provided values if any is provided
    if time_cutoff is None:
        time_cutoff = llm_cutoff

    if favor_recent is None:
        favor_recent = llm_favor_recent

    return time_cutoff, favor_recent


if __name__ == "__main__":
    # Just for testing purposes, too tedious to unit test as it relies on an LLM
    while True:
        user_input = input("Query to Extract Time: ")
        cutoff, recency_bias = extract_time_filter(user_input)
        print(f"Time Cutoff: {cutoff}")
        print(f"Favor Recent: {recency_bias}")
