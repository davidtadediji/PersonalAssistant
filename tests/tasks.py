from app.llm_compiler.agent import chain
from langchain_core.messages import HumanMessage


for step in chain.stream(
        {"messages": [HumanMessage(content="Hi, How are you?")]}
):
    print(step)
    print("---")


for step in chain.stream(
        {"messages": [HumanMessage(content="What is the hometown of the 2024 australia open winner")]}
):
    print(step)
    print("---")



for step in chain.stream(
        {"messages": [HumanMessage(content="My name is david")]}
):
    print(step)
    print("---")

