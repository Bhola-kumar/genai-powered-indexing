from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from typing import List
import tempfile
import traceback
import json

from documentProcessor.documentProcessor import audit_index_document_for_given_chapter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/process-documents")
async def process_documents(
    index_file: UploadFile = File(...),
    chapter_files: List[UploadFile] = File(...)
):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save index file
            index_path = os.path.join(tmpdir, index_file.filename)
            with open(index_path, "wb") as f:
                f.write(await index_file.read())

            # Save all chapter files
            chapter_paths = []
            for chapter_file in chapter_files:
                chapter_path = os.path.join(tmpdir, chapter_file.filename)
                with open(chapter_path, "wb") as f:
                    f.write(await chapter_file.read())
                chapter_paths.append(chapter_path)

            # Call audit function
            result_path = audit_index_document_for_given_chapter(
                CHAPTER_DOCUMENT_LIST=chapter_paths,
                INDEX_DOCUMENT_PATH=index_path
            )

            if not result_path or not os.path.exists(result_path):
                return JSONResponse(
                    status_code=500,
                    content={"error": "Processing failed. No output file generated."}
                )

            with open(result_path, 'r', encoding='utf-8') as f:
                result_json = json.load(f)

            return JSONResponse(content=result_json)

    except Exception as e:
        traceback_str = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback_str}
        )
