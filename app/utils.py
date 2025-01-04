from pathlib import Path


def get_resource_path(resource_name: str) -> Path:
    """
    Get the path to a resource file in the 'resources' directory.

    Args:
        resource_name (str): The name of the resource file (e.g., 'llm_compiler.png').

    Returns:
        Path: The full path to the resource file.
    """
    project_root = Path(__file__).resolve().parent
    resources_dir = project_root / "resources"

    # Ensure the resources directory exists
    resources_dir.mkdir(parents=True, exist_ok=True)

    # Return the full path to the requested resource
    return resources_dir / resource_name