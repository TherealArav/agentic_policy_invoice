import os
import json
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import TypedDict
from docling.document_converter import DocumentConverter

from google import genai
from google.genai import types

from langgraph.graph import StateGraph, START, END


# Load environment variables and configure observability
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY") # Langchain defaults to looking for GOOGLE_API_KEY

# Add the nested LineItem schema
class LineItem(BaseModel):
    description: str = Field(description="Description of the product or service.")
    quantity: float = Field(description="Quantity of the item.", default=1.0)
    unit_price: float = Field(description="Price per individual unit.")
    total: float = Field(description="Total price for this line item.")

# Define the JSON schema required
class InvoiceData(BaseModel):
    vender_name: str = Field(description="The name of the vendor or company.")
    total_amount: float = Field(description="The total monetary amount of the invoice.")
    line_items: list[LineItem] = Field(description="List of all individual items billed in the invoice.")
    
#   Graph State
class AgentState(TypedDict):
    file_path: str
    markdown_content: str
    extracted_data: dict


# Initialize the Unified GenAI Client
client = genai.Client()

async def parse_document(state: AgentState) -> AgentState:
    """Parse the document at the given file path and convert it to markdown"""

    print(f"Parsing {state['file_path']} with Docling...")
    converter = DocumentConverter()
    result = converter.convert(state['file_path'])
    return {"markdown_content": result.document.export_to_markdown()}

async def extract_entities(state: AgentState) -> AgentState:
    print("Extracting data natively with the Google GenAI SDK...")
    prompt = (
        f"Extract the vendor name and total amount from this invoice.\n\n"
        f"INVOICE TEXT:\n{state['markdown_content']}"
    )
    
    response = await client.aio.models.generate_content(
        model='gemini-3.6-flash', 
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=InvoiceData,
            temperature=0,
        ),
    )
    
    extracted_obj: InvoiceData = response.parsed
    return {"extracted_data": extracted_obj.model_dump()}

# Build the LangGraph Workflow
builder = StateGraph(AgentState)
builder.add_node("parse_document", parse_document)
builder.add_node("extract_entities", extract_entities)

# Define the flow
builder.add_edge(START, "parse_document")
builder.add_edge("parse_document", "extract_entities")
builder.add_edge("extract_entities", END)

graph = builder.compile()

# Execute the Graph
async def main():
    pdf_path = "sample_invoice.pdf"
    
    # Initialize the state
    initial_state = {"file_path": pdf_path}
    
    # Run the graph
    final_state = await graph.ainvoke(initial_state)
    
    print("\n=== Extracted JSON Payload (GenAI SDK) ===")
    print(json.dumps(final_state["extracted_data"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())