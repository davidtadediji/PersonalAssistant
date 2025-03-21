import datetime

from langchain_core.messages import HumanMessage

from src.assistant.planning.agent import chain


# Function to save responses with a timestamp
def save_response(response):
    print(response)
    with open('../../resources/responses.txt', 'a', encoding='utf-8') as f:  # Specify utf-8 encoding
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp}\n{response}\n---\n")


for step in chain.stream(
        {"messages": [HumanMessage(content="visit https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/translate-natural-language-query-dsl-opensearch-elasticsearch.html and extract the complete steps to implement the system described")]}):
    response = str(step)
    save_response(response)


# for step in chain.stream(
#         {"messages": [HumanMessage(content="What is my current location, find the temperature and get the distance "
#                                            "it and new york, and store the distance for me as next trip, store that I love hiking, find the temperature for tokyo")]}):
#     response = str(step)
#     save_response(response)

# for step in chain.stream(
#         {"messages": [HumanMessage(content="Calculate bmi for 200pounds at 5'11")]}):
#     response = str(step)
#     save_response(response)
#
# for step in chain.stream(
#         {"messages": [HumanMessage(content="What is turkesterone")]}):
#     response = str(step)
#     save_response(response)
#
# for step in chain.stream(
#         {"messages": [HumanMessage(content="Hi, How are you?")]}):
#     response = str(step)
#     save_response(response)
#
# for step in chain.stream(
#         {"messages": [HumanMessage(content="What is the hometown of the 2024 Australia Open winner")]}):
#     response = str(step)
#     save_response(response)
#
# for step in chain.stream(
#         {"messages": [HumanMessage(content="My name is David")]}):
#     response = str(step)
#     save_response(response)
# #
# for step in chain.stream(
#         {"messages": [HumanMessage(content="How can I cook fish?")]}):
#     response = str(step)
#     save_response(response)
#
#
# for step in chain.stream(
#         {"messages": [HumanMessage(content="Go to Reddit, search for 'browser-use' in the search bar, "
#                                            "click on the first post and return the first comment.")]}):
#     response = str(step)
#     save_response(response)
