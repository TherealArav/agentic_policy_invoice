import os
import json
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import TypedDict, Optional
from docling.document_converter import DocumentConverter

from google import genai
from google.genai import types

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langsmith import traceable, get_current_run_tree

from schemas import InvoiceData
from validators import validate_vendor_node

# Load environment variables and configure observability
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

#   Graph State
class AgentState(TypedDict):
    file_path: str
    extracted_data: Optional[dict]
    markdown_content: str
    vendor_verified: bool     
    needs_review: bool        
    routing_message: str      


# Initialize the Unified GenAI Client
client = genai.Client()

def run_traceable(response: types.GenerateContentConfig):
    """Helper function to log token usage for traceable runs."""
    run = get_current_run_tree()
    if run and hasattr(response, "usage_metadata"):
        run.add_metadata({
            "usage_metadata": {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }
        })
    
async def parse_document_node(state: AgentState) -> AgentState:
    """Parse the document at the given file path and convert it to markdown"""

    print(f"Parsing {state['file_path']} with Docling...")
    converter = DocumentConverter()
    result = converter.convert(state['file_path'])
    return {"markdown_content": result.document.export_to_markdown()}

@traceable(name="Gemini Extraction", run_type="llm")
async def extract_entities_node(state: AgentState) -> AgentState:
    print("Extracting data natively with the Google GenAI SDK...")
    prompt = (
        f"Extract the vendor name, 15-digit UAE Tax Registration Number (TRN), "
        f"invoice number, subtotal, tax amount, total amount, and line items from this invoice.\n\n"
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

    run_traceable(response)
    
    extracted_obj: InvoiceData = response.parsed
    return {"extracted_data": extracted_obj.model_dump()}

def erp_submission_node(state: AgentState):
    """The final node that pushes data to the real ERP. We pause BEFORE this if flagged."""
    # In production, this makes an API call to SAP/Oracle
    return {"routing_message": "Successfully submitted to ERP."}

def human_review_node(state: AgentState):
    """Dummy node. The graph pauses BEFORE executing this. 
    When resumed, it simply passes the state forward."""
    return {}

def route_after_validation(state: AgentState):
    """Conditional edge routing based on the deterministic validation."""
    if state.get("needs_review"):
        return "human_review" # We route to the node we want to interrupt
    
    return "erp_submission"

# Build the LangGraph Workflow
builder = StateGraph(AgentState)
builder.add_node("parse_document", parse_document_node)
builder.add_node("extract_entities", extract_entities_node)
builder.add_node("validate_vendor", validate_vendor_node)
builder.add_node("human_review" ,human_review_node)
builder.add_node("erp_submission", erp_submission_node)

# Define the flow
builder.add_edge(START, "parse_document")
builder.add_edge("parse_document", "extract_entities")
builder.add_edge("extract_entities", "validate_vendor")
builder.add_conditional_edges("validate_vendor",route_after_validation,  {
    "human_review": "human_review", # Human review resumes into ERP submission
    "erp_submission": "erp_submission"
})
builder.add_edge("human_review", "erp_submission")
builder.add_edge("erp_submission", END)

memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["human_review"] # The graph pauses right before executing this node
)

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