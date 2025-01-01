# router.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from graph import graph

router = APIRouter(
    prefix="/api",
    tags=["Form Generator"],
    responses={404: {"description": "Not found"}},
)


# Define the expected JSON body schema
class RequirementsRequest(BaseModel):
    requirements: str  # The key in the JSON body containing the requirements string


@router.post("/generate-form/", response_class=JSONResponse)
async def generate_form(request: RequirementsRequest):
    """
    Generate a form based on the design requirements provided in the JSON body.

    Args:
        request (RequirementsRequest): JSON object with a "requirements" key.

    Returns:
        JSONResponse: Generated form or error message.
    """
    try:
        # Extract the requirements from the parsed JSON body
        requirements = request.requirements

        # Debug: Log the input
        print("Received Requirements:", requirements)

        # Prepare inputs for the graph
        messages = [HumanMessage(content=requirements)]

        # Invoke the graph
        result = graph.invoke({"messages": messages})

        # Debug: Log the result
        print("Generated Form Result:", result)

        # Extract the last message content from the result
        if result and isinstance(result, dict) and "messages" in result:
            # Ensure the messages list is not empty
            if result["messages"]:
                last_message = result["messages"][-1]  # Select the last message
                if hasattr(last_message, "content"):
                    response = (
                        last_message.content
                    )  # Get the content of the last message
                else:
                    response = "No response."
            else:
                response = "No response."
        else:
            response = "No response."

        # Return the result with the extracted message content
        return JSONResponse(content={"generated_response": response}, status_code=200)

    except Exception as e:
        # Handle errors
        print("Error generating form:", e)
        return JSONResponse(
            content={"error": "Failed to generate form", "details": str(e)},
            status_code=500,
        )
