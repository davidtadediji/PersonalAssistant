import datetime
from app.llm_compiler.agent import chain
from langchain_core.messages import HumanMessage

# Function to save responses with a timestamp
def save_response(response):
    print(response)
    with open('responses.txt', 'a', encoding='utf-8') as f:  # Specify utf-8 encoding
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{timestamp}\n{response}\n---\n")

# Stream and save responses
# for step in chain.stream(
#         {"messages": [HumanMessage(content="Calculate bmi for 200pounds at 5'11")]}):
#     response = str(step)
#     save_response(response)

# Stream and save responses
# for step in chain.stream(
#         {"messages": [HumanMessage(content="What is turkesterone")]}):
#     response = str(step)
#     save_response(response)


# # Stream and save responses
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
#
# for step in chain.stream(
#         {"messages": [HumanMessage(content="How can I cook fish?")]}):
#     response = str(step)
#     save_response(response)
