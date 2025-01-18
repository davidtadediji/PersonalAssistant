from typing import List, Dict, Any
from fpdf import FPDF
from langchain.tools import StructuredTool
from pydantic import BaseModel
from app.logger import configured_logger  # Assuming the logger is imported


class CreateFileInput(BaseModel):
    filename: str
    file_type: str  # The type of file to create (e.g., 'pdf', 'txt')
    content: List[Dict[str, Any]]  # A list of content sections


def create_file(filename: str, file_type: str, content: List[Dict[str, Any]]) -> str:
    """
    Create a file of the specified type and write content to it.

    Args:
        filename (str): The name of the file to be created.
        file_type (str): The type of file to create ('pdf' or 'txt').
        content (List[Dict[str, Any]]): A list of content sections to write.
            For PDFs, each section is a dictionary with:
            - 'text' (str): The text to add.
            - 'size' (int, optional): Font size for the text (default is 12).
            - 'align' (str, optional): Alignment of the text ('L', 'C', 'R', default is 'L').
            - 'new_line' (bool, optional): Whether to add a new line after the text (default is True).
            For text files, only the 'text' key is used.

    Returns:
        str: The path to the created file.
    """
    configured_logger.info(f"Starting file creation: {filename} with type {file_type}.")

    try:
        if file_type.lower() == "pdf":
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            for section in content:
                text = section.get("text", "")
                size = section.get("size", 12)
                align = section.get("align", "L")
                new_line = section.get("new_line", True)

                pdf.set_font_size(size)
                pdf.multi_cell(0, 10, txt=text, align=align)

                if new_line:
                    pdf.ln()

            pdf.output(filename)
            configured_logger.info(f"PDF file created successfully at: {filename}")
            return f"PDF created successfully at: {filename}"

        elif file_type.lower() == "txt":
            with open(filename, "w") as file:
                for section in content:
                    text = section.get("text", "")
                    file.write(text + "\n")
            configured_logger.info(f"Text file created successfully at: {filename}")
            return f"Text file created successfully at: {filename}"

        else:
            configured_logger.error(f"Unsupported file type: {file_type}")
            raise ValueError(f"Unsupported file type: {file_type}")

    except Exception as e:
        configured_logger.error(f"Error occurred while creating file {filename}: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}


def get_create_file_tool():
    return StructuredTool.from_function(
        name="create_file",
        func=create_file,
        description=(
            "Create a file of the specified type and write content to it. "
            "Supported file types include PDF and text files."
            "\n\n"
            "### Arguments:\n"
            "- `filename` (str): The name of the file to be created.\n"
            "- `file_type` (str): The type of file to create ('pdf', 'txt').\n"
            "- `content` (List[Dict[str, Any]]): A list of sections containing text and formatting options. "
            "For PDFs, each section can include:\n"
            "  - 'text' (str): The text to add to the file.\n"
            "  - 'size' (int, optional): Font size for PDFs (default is 12).\n"
            "  - 'align' (str, optional): Alignment for PDFs ('L', 'C', 'R', default is 'L').\n"
            "  - 'new_line' (bool, optional): Whether to add a new line after the text (default is True)."
            "\nFor text files, only 'text' is used."
        ),
        input_schema=CreateFileInput,
    )
