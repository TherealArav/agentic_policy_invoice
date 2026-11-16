import os
import shutil
import uuid
import logging, tempfile
from typing import Literal
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from main import builder

# Lock down msgpack deserialization before initializing the SQLite checkpointer
os.environ["LANGGRAPH_STRICT_MSGPACK"] = "true"
DB_PATH = os.getenv("CHECKPOINT_DB_PATH", "checkpoints.sqlite")

logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
PUBLIC_STATE_KEYS = ("extracted_data", "vendor_verified", "needs_review", "routing_message")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the persistent async SQLite connection lifecycle."""
    async with AsyncSqliteSaver.from_conn_string(DB_PATH) as saver:
        app.state.graph = builder.compile(
            checkpointer=saver,
            interrupt_before=["human_review"]
        )
        yield # Server runs here while connection stays open

app = FastAPI(title="UAE Agentic Invoice API", lifespan=lifespan)

# Configure CORS for your Svelte 5 frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    reviewer_notes: str = ""


def _public_state(state: dict) -> dict:
    return {k: state.get(k) for k in PUBLIC_STATE_KEYS}

@app.post("/api/extract")
async def extract_invoice(request: Request, file: UploadFile = File(...)):
    """
    1. Saves the uploaded PDF temporarily.
    2. Starts a new stateful LangGraph thread.
    3. Returns the extracted state, thread_id, and whether the graph paused at human_review.
    """
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    if await file.read(5) != b"%PDF-":                      # check the file's first bytes
        raise HTTPException(status_code=400, detail="File is not a valid PDF.")
    await file.seek(0)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": str(thread_id)}}
    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            temp_file_path = tmp.name                       # path not built from user input
            size = 0
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="PDF exceeds 10MB limit.")
                tmp.write(chunk)

        result = await request.app.state.graph.ainvoke({"file_path": temp_file_path}, config=config)
        snapshot = await request.app.state.graph.aget_state(config)
        next_nodes = list(snapshot.next or [])

        return {
            "status": "paused_for_review" if "human_review" in next_nodes else "completed",
            "thread_id": str(thread_id),
            "next_step": next_nodes,
            **_public_state(result),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Pipeline failed for thread %s", thread_id)
        raise HTTPException(status_code=500, detail="Invoice processing failed.") from e
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/api/review/{thread_id}")
async def review_invoice(request: Request, thread_id: uuid.UUID, payload: ReviewRequest):
    """
    Resumes or halts a paused LangGraph execution thread after human intervention.
    """
    config = {"configurable": {"thread_id": str(thread_id)}}

    # Verify the thread exists in the Checkpointer (MemorySaver / SqliteSaver)
    snapshot = await request.app.state.graph.aget_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found.")

    if "human_review" not in (snapshot.next or ()):
        raise HTTPException(
            status_code=400,
            detail="This invoice thread is not currently awaiting human review.",
        )

    # Path A: Human Rejects the Invoice
    if payload.action == "reject":
        note = f" ({payload.reviewer_notes})" if payload.reviewer_notes else ""
        rejection_msg = f"Rejected by AP Reviewer{note}. Blocked from ERP submission."

        # Update state and use as_node="erp_submission" so the graph marks itself as finished (END)
        # without executing the actual erp_submission_node
        await request.app.state.graph.aupdate_state(
            config,
            {
                "vendor_verified": False,
                "needs_review": False,
                "routing_message": rejection_msg,
            },
            as_node="erp_submission",
        )
        updated_snapshot = await request.app.state.graph.aget_state(config)
        return {
            "status": "rejected",
            "thread_id": str(thread_id),
            **_public_state(...),
        }

    # Path B: Human Approves the Invoice -> Resume Graph Execution
    note = f" ({payload.reviewer_notes})" if payload.reviewer_notes else ""
    await request.app.state.graph.aupdate_state(
        config,
        {
            "needs_review": False,
            "routing_message": f"Manual Override: Approved by AP Reviewer{note}.",
        },
    )

    # Passing None tells LangGraph to continue from the paused breakpoint ("human_review" -> "erp_submission")
    final_state = await request.app.state.graph.ainvoke(None, config=config)

    return {
        "status": "approved_and_submitted",
        "thread_id": str(thread_id),
        **_public_state(...),
    }