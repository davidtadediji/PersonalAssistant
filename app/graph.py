# graph.py
from PIL import Image as PILImage
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

memory = MemorySaver()

load_dotenv()

#
# class GeneratorState(MessagesState):
#     context: Annotated[list, operator.add]  # Source docs


instructions = """You are an expert at {goal}

When generating the JSON, follow these steps and guidelines:

**Step 1:**  
First, retrieve the metadata for the entities defined in the user’s prompt. Follow these guidelines for Step 1
**Step 2:**
After the entity metadata has been retrieve JSON schema. Use the schema provider
**Step 3:**
After the json schema has been retrieved, consider:
    a) Consider any extra UI requirements, such as the available headers specified or whether a field is visible. Ensure that these UI requirements are integrated into the form generation.
    b) Consider any extra validation rules specified by the user. Ensure that they do not conflict with the validation rules provided in the entity metadata.
**Step 4:
Use all the extracted metadata and the information gathered from the extra UI requirements and validation steps as a reference to generate the form JSON. Follow the provided form JSON schema for structured output.
---
**Guidelines for Step 1:**

1. **Use only the entities specified in the user prompt.**  
   - Do not consider any entities that are not explicitly mentioned in the user's input.

2. If no entities are specified in the user prompt, **abort the process** and request the user to specify the entities they would like to generate a form for.

3. Retrieve the **metadata for each specified entity.**  
   - If metadata is not available for an entity, skip it and move on to the next entity and if no metadata is available, tell user.
---
### Guidelines for Step 4 (Form JSON Generation):

1. Use only the information provided in the context. 

2. Do not introduce external information or make assumptions beyond what is explicitly stated in the context.

3. Strictly adhere to the JSON schema structure and requirements.

4. Generate only the JSON object, with no additional accompaniment or explanation.

5. If no metadata is present for an entity, ignore it and move on to the next.

6. Do not generate a form for an entity if metadata is not available for that entity.

7. Follow these additional guidelines:  
   - All entity names must be unique. If necessary, apply a unique suffix to entity names.
   - The available headers to include in the JSON properties are: "help", "form", "verify", "attachments", and "submit".
   - "form" and "submit" headers are mandatory.
   - Understand that each entity displays as a page with fields when rendered.
   - Available item layout actions include: "viewMoreButton", "deleteButton", and "editButton".
"""

instructions2 = """You are an expert at {goal}

When generating the JSON, follow these steps and guidelines:

**Step 1:**  
First, retrieve the metadata for the entities defined in the user’s prompt. Follow these guidelines for Step 1:

**Guidelines for Step 1:**

1. **Use only the entities specified in the user prompt.**  
   - Do not consider any entities that are not explicitly mentioned in the user's input.

2. If no entities are specified in the user prompt, **abort the process** and request the user to specify the entities they would like to generate a form for.

3. Retrieve the **metadata for each specified entity.**  
   - If metadata is not available for an entity, skip it and move on to the next entity and if no metadata is available, tell user.

**Step 2:**  
Consider any extra UI requirements, such as the available headers specified or whether a field is visible. Ensure that these UI requirements are integrated into the form generation.

**Step 3:**  
Consider any extra validation rules specified by the user. Ensure that they do not conflict with the validation rules provided in the entity metadata.

**Step 4:**  
Use all the extracted metadata and the information gathered from the extra UI requirements and validation steps as a reference to generate the form JSON. Follow the provided form JSON schema for structured output.

---

### Guidelines for Step 4 (Form JSON Generation):

1. Use only the information provided in the context. 

2. Do not introduce external information or make assumptions beyond what is explicitly stated in the context.

3. Strictly adhere to the JSON schema structure and requirements.

4. Generate only the JSON object, with no additional accompaniment or explanation.

5. If no metadata is present for an entity, ignore it and move on to the next.

6. Do not generate a form for an entity if metadata is not available for that entity.

7. Follow these additional guidelines:  
   - All entity names must be unique. If necessary, apply a unique suffix to entity names.
   - The available headers to include in the JSON properties are: "help", "form", "verify", "attachments", and "submit".
   - "form" and "submit" headers are mandatory.
   - Understand that each entity displays as a page with fields when rendered.
   - Available item layout actions include: "viewMoreButton", "deleteButton", and "editButton".
"""

tools = []
# form_json_schema = schema_provider()
llm = ChatOpenAI(model="gpt-4o-2024-08-06")
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)
# structured_output_llm = llm.with_structured_output(form_json_schema, strict=True)

system_message = SystemMessage(
    content=instructions.format(
        goal="generating form rendering/definition JSON based entity metadata and json schema provided"
    )
)

system_message2 = SystemMessage(
    content=instructions2.format(
        goal="generating form rendering/definition JSON based entity metadata provided"
    )
)

print(system_message)


# def respond(state: MessagesState):
#
#     response = structured_output_llm.invoke(
#         [HumanMessage(content=state["messages"][-2].content)]
#     )
#     return {"final_response": response}


# Define node function for tool calling
def call_node(state: MessagesState):
    return {"messages": [llm_with_tools.invoke([system_message] + state["messages"])]}


# Define node function for answering with context
# def answer_with_context(state: GeneratorState):
#     """
#     Node to generate form definition JSON
#     """
#     messages = state["messages"]
#     context = state["context"]
#
#     # Generate form JSON
#     system_message = instructions.format(
#         goal="generating form rendering/definition JSON based on a specific JSON schema.",
#         context=context,
#         guidelines=additional_guidelines,
#     )
#     #
#     # answer = llm.invoke([SystemMessage(content=system_message)] + messages)
#     structured_llm = llm.with_structured_output(context, method="json_mode")
#
#     answer = structured_llm.invoke([SystemMessage(content=system_message)] + messages)
#     state["context"] = []  # just added may cause issues remove
#
#     # append it to state
#     return {"messages": [answer]}


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    print(last_message)
    if not last_message.tool_calls:
        return "respond"


# Build graph
workflow = StateGraph(MessagesState)
# workflow.add_node("respond", respond)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("form_generator", call_node)
# builder.add_node("answer_with_context", tool_calling_llm)

# Graph Logic
workflow.add_edge(START, "form_generator")
workflow.add_conditional_edges(
    "form_generator",
    tools_condition,
)
workflow.add_edge("tools", "form_generator")
# workflow.add_edge("respond", END)


# Compile graph
graph = workflow.compile(checkpointer=memory)

# Display graph
image_data = graph.get_graph().draw_mermaid_png()

# View

from pathlib import Path

# Get the absolute path to the project root or app directory
project_root = (
    Path(__file__).resolve().parent
)  # This is the directory where server.py is located
resources_dir = (
    project_root / "resources"
)  # Use the / operator to join paths (pathlib feature)

# Ensure the resources directory exists
resources_dir.mkdir(parents=True, exist_ok=True)

graph_image = resources_dir / "graph.png"  # Creates an absolute path to the file

with open(graph_image, "wb") as f:
    f.write(image_data)

img = PILImage.open("../resources/graph.png")
img.show()
