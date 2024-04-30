import re

PROJECTS = [
    "Can you list all the projects in education that IDinsight has ever done?",
    "Hello - can you give me a list of all the projects Karan Nagpal has worked on as a\
        Director? Source answers from Slack channel project updates.",
    "have we done any work in social protection",
    "Is the Philippines' Health Promotion and Literacy Longitudinal Study considered an\
        impact evaluation project",
    "What was the most recent MLE project IDinsight completed?",
    "project summary dobu",
    "Give me a summary of what has happened on a care LP in the last 13 months",
]

POLICIES = [
    "How do you sign up on surveystream",
    "How do I use Unit4",
    "Where do I submit my expenses",
    "How do I install perimeter81?",
    "What is the link for accessing timesheets?",
]

RESOURCES = [
    "can you share with me the IDi doc templates link",
    "Can you give me an example of IRB submission",
    "Hello! Where can I find the user manual to be filled for a project on-boarding?",
    "workplans for a mixed methods process evaluation",
    "An example of a short proposal pitch for work IDinsight has done in Microfinance",
    "can anyone share a MELA proposal that we've done recently in education? WNA is developing\
a proposal for a MELA engagement with the MEN in Cote d'Ivoire.",
]

TEAMS = [
    "About Dinabandhu Bharti",
    "Tell me about Mark Botterell",
    "Who is Zia",
    "who is amit kumar",
    "tell me about dinabandhu bharti field manager at idinsight",
    "Who is DS team director?",
]

MISCELLANEOUS = [
    "hi",
    "Test",
    "Hi <!channel>",
    "holiday calendar",
    "what is 'hubgpt'",
    "What are the list of holidays in India in 2024",
    "Qualgpt",
    "what was the temperature in Delhi on 25th February 2024?",
    "mumbwa",
]

CONTEXT_PROMPT = f"""

You are a labeling bot. Your job is to give a label to a question asked by a\
    user and return a one-word label.

The labels you can choose from are as follows: "PROJECTS", "POLICIES", "RESOURCES",\
    "TEAMS", or "MISCELLANEOUS".
I have provided you with some demonstrations as to how you MUST classify a question:

Questions suitable for the "PROJECTS" label will involve past or current projects,\
    services, work, interventions,
or experiences at IDinsight. Here are some examples: {PROJECTS}

Questions suitable for the "POLICIES" label are questions that involve eligibility\
    and steps of all global or
regional policies, processes, benefits, and all queries related to Unit4. Here are\
    some examples: {POLICIES}

The "RESOURCES" label applies to questions about guidelines, tools, products, and\
    resources that support
organizational work, such as guidelines for project execution, service-related\
    resources, or questions about
tools like the GDH Dashboard, HubGPT, KM processes, etc. Here are some examples:\
    {RESOURCES}

Questions suitable for the "TEAMS" label involve IDinsight personnel-related\
    questions around people's
designations, roles and responsibilities, regions, and who to contact for a\
    specific task, as well as organizational
structure. Here are some examples: {TEAMS}

Questions suitable for the "MISCELLANEOUS" label include anything that doesn't\
    clearly fall into the above
four categories, such as random questions about IDinsight, or general non-IDinsight\
    questions that
can be asked to chatGPT. Here are some examples: {MISCELLANEOUS}
"""

TASK_PROMPT = """

Example usage:

Submitted question from user: "Who is the head of Human Resources?"
Answer: "TEAMS"

Consider the lists and labels, then read the user text in triple backticks below, then\
    provide your one-word classification.

Submitted question from user: ```{question}```

What is the most accurate label for the submitted question from the user?

Output your response between the tags <Response> and </Response>, without any additional text.

"""


def insert_question(user_question):
    full_prompt = CONTEXT_PROMPT + TASK_PROMPT.format(question=user_question)
    return full_prompt


def label_question(user_question, client):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": insert_question(user_question),
            }
        ],
        model="gpt-3.5-turbo",
    )
    output = chat_completion.choices[0].message.content
    label = re.findall(r"<Response>\s*([\s\S]*?)\s*</Response>", output)[0]
    return label
