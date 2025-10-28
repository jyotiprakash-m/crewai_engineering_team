from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import SQLModel, Field, Session, select, func
import os
from typing import List
import zipfile

# Initialize the API router for core functionality
router = APIRouter(prefix="/core", tags=["Core Functionality"])

#=============================
# Router endpoints
#=============================

@router.get("/list-files/{project_name}", response_model=List[str])
async def list_files(project_name: str):
    """
    List all file names in output/{project_name} directory.
    """
    directory = os.path.join("output", project_name)
    try:
        if not os.path.exists(directory):
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/zip-project/{project_name}")
async def zip_project_api(project_name: str):
    """
    Zips the entire output/{project_name} folder and stores the zip file in the same folder.
    Returns the path to the created zip file and download link.
    """
    folder_path = os.path.join("output", project_name)
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")
    try:
        zip_path = zip_project_folder(project_name)
        # Return a download link using the /public static mount
        download_url = f"/public/{project_name}/{project_name}.zip"
        return {"zip_path": zip_path, "download_url": download_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#=============================
# Service functions
#=============================

def zip_project_folder(project_name: str) -> str:
    """
    Zips the entire output/{project_name} folder and stores the zip file in the same folder.
    Returns the path to the created zip file.
    """
    folder_path = os.path.join("output", project_name)
    zip_path = os.path.join(folder_path, f"{project_name}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Store files with relative path inside the zip
                arcname = os.path.relpath(file_path, folder_path)
                if arcname != f"{project_name}.zip":  # Avoid zipping the zip itself
                    zipf.write(file_path, arcname)
    return zip_path


