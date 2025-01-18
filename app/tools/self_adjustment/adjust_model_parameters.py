from pydantic import BaseModel
from langchain_core.tools import StructuredTool

class AdjustModelParametersRequest(BaseModel):
    parameter_name: str  # The name of the parameter to adjust
    new_value: str       # The new value for the parameter

def adjust_model_parameters(parameter_name: str, new_value: str) -> str:
    """Adjust the given model parameter to a new value.

    Args:
        parameter_name (str): The name of the parameter to adjust.
        new_value (str): The new value for the parameter.

    Returns:
        str: A confirmation message indicating the parameter adjustment.
    """
    # Placeholder for parameter adjustment logic
    return f"Parameter '{parameter_name}' adjusted to '{new_value}'."  # Example response

def get_adjust_model_parameters_tool():
    return StructuredTool.from_function(
        name="adjust_model_parameters",
        func=adjust_model_parameters,
        description=(
            "Adjust the given model parameter to a new value.\n"
            "adjust_model_parameters(parameter_name: str, new_value: str) -> str:\n"
            " - parameter_name: The name of the parameter to adjust.\n"
            " - new_value: The new value for the parameter.\n"
            " - Returns a confirmation message indicating the adjustment."
        ),
        input_schema=AdjustModelParametersRequest,
    )
