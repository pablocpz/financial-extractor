from __future__ import annotations

from dataclasses import dataclass, field
from fastmcp import FastMCP
from file_data_extraction import file_data_extraction
from agent_field_matching import field_matching
from excel_exporting import export_excel

import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional, Union, List
from urllib.parse import urlparse, unquote

import anyio
import asyncio
import tempfile
import httpx
import aiofiles


mcp = FastMCP(name="DocumentsExtractor")


# ---------------------------
# Per-run state
# ---------------------------
@dataclass
class RunState:
    run_id: str
    base_dir: Path
    reports_dir: Path
    out_dir: Path
    status: str = "idle"
    final_excel: Optional[Path] = None
    errors: List[str] = field(default_factory=list)          # <-- per-run errors
    lock: anyio.abc.Lock = field(default_factory=anyio.Lock) # serialize mutating ops


# All runs live here, keyed by run_id
RUNS: Dict[str, RunState] = {}

# Guard the RUNS dict itself (create/delete runs)
RUNS_LOCK = asyncio.Lock()


# ---------------------------
# Utilities
# ---------------------------
def _safe_filename_from_url(url: str) -> str:
    name = unquote(Path(urlparse(url).path).name)
    return name or "file"

def _unique_path(dirpath: Path, filename: str) -> Path:
    base = Path(filename).stem
    ext = Path(filename).suffix
    candidate = dirpath / filename
    i = 1
    while candidate.exists():
        candidate = dirpath / f"{base}-{i}{ext}"
        i += 1
    return candidate

def _ensure_run(run_id: str) -> RunState:
    state = RUNS.get(run_id)
    if not state:
        raise ValueError(f"Unknown run_id: {run_id}")
    return state


# ---------------------------
# 1) START: create run + download (async, non-blocking)
# ---------------------------
@mcp.tool
async def download_supabase_s3_documents(urls: Union[str, List[str]]) -> str:
    """
    Start a new run: creates unique temp dirs and downloads documents concurrently.
    Returns: run_id (string)
    """
    url_list = [urls] if isinstance(urls, str) else list(urls)

    # Create unique dirs for this run
    base_dir = Path(tempfile.mkdtemp(prefix="docsextractor_"))
    reports_dir = base_dir / "reports"
    out_dir = base_dir / "out"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = uuid.uuid4().hex
    state = RunState(
        run_id=run_id,
        base_dir=base_dir,
        reports_dir=reports_dir,
        out_dir=out_dir,
        status="preparing_folders",
    )

    # Register the run
    async with RUNS_LOCK:
        RUNS[run_id] = state

    # Perform downloads (concurrently, bounded) with per-task error capture
    state.status = "downloading"
    async with httpx.AsyncClient(timeout=120) as client:
        sem = anyio.Semaphore(5)  # cap concurrency to be gentle on remote

        async def download_one(url: str):
            async with sem:
                try:
                    async with client.stream("GET", url) as resp:
                        resp.raise_for_status()
                        filename = _safe_filename_from_url(url)
                        target = _unique_path(reports_dir, filename)
                        async with aiofiles.open(target, "wb") as f:
                            async for chunk in resp.aiter_bytes(chunk_size=1024 * 256):
                                if chunk:
                                    await f.write(chunk)
                except Exception as e:
                    # Capture error instead of letting TaskGroup raise ExceptionGroup
                    state.errors.append(f"{url}: {e}")

        # Run all downloads concurrently; individual failures are recorded
        async with anyio.create_task_group() as tg:
            for u in url_list:
                tg.start_soon(download_one, u)

    # Decide overall status
    state.status = "download_errors" if state.errors else "ready"
    return run_id


# ---------------------------
# 2) PROCESS: CPU-heavy pipeline (off event loop)
# ---------------------------
def _process_documents_sync(state: RunState) -> str:
    """Synchronous heavy work; runs in a worker thread."""
    state.status = "parsing_docs_to_markdown"
    file_data_extraction(
        reports_folder_name=str(state.reports_dir),
        output_folder_name=str(state.out_dir),
    )

    state.status = "matching_fields_with_llm"
    field_matching(DATA_FOLDER=str(state.out_dir))

    state.status = "exporting_final_excel"
    # Tool: get_new_pdfs_in_out_dir
    
    final_excel_path = Path(export_excel(out_dir=str(state.out_dir)))
    state.final_excel = final_excel_path

    state.status = "done"
    return str(final_excel_path)


@mcp.tool
async def process_documents(run_id: str) -> str:
    """
    Run the extraction → matching → export for a given run_id.
    Returns: final Excel path (string)
    """
    state = _ensure_run(run_id)
    async with state.lock:
        if state.status not in {"ready", "error", "idle", "download_errors"}:
            # prevent double processing
            return str(state.final_excel) if state.final_excel else "already_processing"

        if state.status == "download_errors":
            # You can choose to proceed or to fail fast; here we fail fast.
            raise RuntimeError(f"Cannot process; download errors present: {state.errors}")

        state.status = "starting"
        # Offload CPU-bound pipeline so we don't block the event loop
        try:
            return await anyio.to_thread.run_sync(_process_documents_sync, state)
        except Exception as e:
            state.status = f"error: {e}"
            raise


# ---------------------------
# 3) STATUS
# ---------------------------
@mcp.tool
def get_process_status(run_id: str) -> dict:
    """
    Get status + minimal metadata for a given run_id.
    """
    state = _ensure_run(run_id)
    return {
        "run_id": state.run_id,
        "status": state.status,
        "base_dir": str(state.base_dir),
        "reports_dir": str(state.reports_dir),
        "out_dir": str(state.out_dir),
        "final_excel": str(state.final_excel) if state.final_excel else None,
        "errors": list(state.errors),  # expose captured per-URL errors
    }





# ---------------------------
# 4) READ FINAL DOCUMENT (async, non-blocking)
# ---------------------------
@mcp.tool
async def read_final_document(run_id: str) -> bytes:
    """
    Read the final Excel bytes for a given run_id.
    """
    state = _ensure_run(run_id)
    if not state.final_excel:
        raise ValueError("Final Excel not available yet. Did you call process_documents?")

    path = state.final_excel
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    async with aiofiles.open(path, "rb") as f:
        return await f.read()


# ---------------------------
# 5) CLEANUP: delete artifacts and forget the run
# ---------------------------
@mcp.tool
async def cleanup_run(run_id: str) -> dict:
    """
    Delete the run's temp directory and remove it from registry.
    Do this after you've retrieved/used the final Excel.
    """
    async with RUNS_LOCK:
        state = RUNS.pop(run_id, None)

    if not state:
        return {"run_id": run_id, "status": "not_found"}

    # Best-effort cleanup
    summary = {}
    try:
        if state.base_dir.exists():
            shutil.rmtree(state.base_dir)
            summary[str(state.base_dir)] = "deleted"
        else:
            summary[str(state.base_dir)] = "not_found"
    except Exception as e:
        summary[str(state.base_dir)] = f"error: {e}"

    return {"run_id": run_id, "cleanup": summary}


if __name__ == "__main__":
    mcp.run(transport="http")