from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

from main import graph

app = FastAPI(title="Invoice Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Allows your Svelte app
    allow_credentials=True,
    allow_methods=["*"], # Allows POST, GET, etc.
    allow_headers=["*"],
)

# API endpoint for extracting invoice data
@app.post("/api/extract")
async def extract_invoice(file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

        try:
            # Pass the file to your LangGraph orchestrator
            initial_state = {"file_path": temp_file_path}
            final_state = await graph.ainvoke(initial_state)

            # Return the extracted data to the frontend
            return{
            "status": "success", 
            "data": final_state.get("extracted_data"),
            "vendor_verified": final_state.get("vendor_verified"),
            "needs_review": final_state.get("needs_review"),
            "routing_message": final_state.get("routing_message")
        }

        except Exception as e:
            return {
                "status": "error", 
                "message": str(e), 
                "data": final_state.get("extracted_data"),
                "vendor_verified": final_state.get("vendor_verified"),
                "needs_review": final_state.get("needs_review"),
                "routing_message": f"Routing error: {final_state.get("routing_message")}."}
        
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)