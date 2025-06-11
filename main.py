from fastapi import FastAPI, Depends, HTTPException, status, Query, Path
from typing import List, Optional, Any, Dict, Union
from dotenv import load_dotenv
from datetime import datetime

import requests
import os

load_dotenv()

from gistlick import GistLick
from models import UserInfo, GistCreate, GistUpdate, GistResponse, LicenseCreate, LicenseResponse, MessageResponse, DeletedCountResponse, LicenseUpdate
from dependencies import get_gistlick_instance, get_current_user_info

app = FastAPI(
    title="GistLick GitHub API",
    description="A REST API for managing GitHub Gists and Licenses via your GitHub Personal Access Token.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Root Endpoint (Optional) ---
@app.get("/", summary="API Root", response_model=MessageResponse)
async def root():
    return {"message": "Welcome to GistLick GitHub API! Access documentation at /docs"}

# --- User Endpoints ---
@app.get("/user/me", summary="Get Authenticated User Info", response_model=UserInfo)
async def get_user_me(user_info: Dict[str, Any] = Depends(get_current_user_info)):
    """
    Retrieve details of the authenticated GitHub user.
    """
    return user_info

# --- Gist Endpoints ---
@app.get("/gists", summary="List Gists", response_model=List[GistResponse])
async def list_gists(
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Retrieve a list of all Gists owned by the authenticated user.
    """
    try:
        gists = gist_lick.get_gist()
        return gists
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/gists/{gist_id}", summary="Get Gist Details", response_model=GistResponse)
async def get_single_gist(
    gist_id: str = Path(..., example="your_gist_id", description="The ID of the Gist to retrieve"),
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Retrieve details for a specific Gist by its ID.
    """
    try:
        gist_data = gist_lick.get_gist_data(gist_id)
        return gist_data
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gist with ID '{gist_id}' not found.")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/gists", summary="Create Gist", response_model=GistResponse, status_code=status.HTTP_201_CREATED)
async def create_gist(
    gist_create: GistCreate,
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Create a new Gist.
    """
    try:
        new_gist = gist_lick.create_gist(
            name=gist_create.name,
            public=gist_create.public,
            description=gist_create.description
        )
        return new_gist
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.put("/gists/{gist_id}", summary="Update Gist", response_model=GistResponse)
async def update_gist(
    gist_id: str = Path(..., example="your_gist_id", description="The ID of the Gist to update"),
    gist_update: GistUpdate,
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Update an existing Gist. All fields are optional; only provided fields will be updated.
    If 'content' is provided, it will overwrite the existing content of the first file.
    """
    try:
        updated_gist_data = gist_lick.update_gist(
            gist_id=gist_id,
            name=gist_update.name,
            public=gist_update.public,
            content=gist_update.content,
            description=gist_update.description
        )
        return updated_gist_data
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gist with ID '{gist_id}' not found.")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except ValueError as e: # Catch ValueErrors from GistLick (e.g., file not found)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.delete("/gists/{gist_id}", summary="Delete Gist", response_model=MessageResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_gist(
    gist_id: str = Path(..., example="your_gist_id", description="The ID of the Gist to delete"),
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Delete a Gist by its ID.
    """
    try:
        gist_lick.delete_gist(gist_id)
        return MessageResponse(message=f"Gist with ID '{gist_id}' has been deleted.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gist with ID '{gist_id}' not found.")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- License Endpoints ---
@app.get("/gists/{gist_id}/licenses", summary="List Licenses in a Gist", response_model=List[LicenseResponse])
async def list_licenses_in_gist(
    gist_id: str = Path(..., example="your_gist_id", description="The ID of the Gist to fetch licenses from"),
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Retrieve all license entries stored within a specific Gist.
    """
    try:
        gist_content = gist_lick.get_gist_content(gist_id)
        if not isinstance(gist_content, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Gist '{gist_id}' content is not a list of licenses. Please ensure it's a JSON array."
            )
        
        licenses = []
        for item in gist_content:
            if not isinstance(item, dict): continue # Skip non-dict items
            
            is_expired_status = False
            try:
                if 'expired' in item and item['expired']:
                    expired_dt = datetime.strptime(item['expired'], '%Y-%m-%d %H:%M:%S')
                    is_expired_status = datetime.now() > expired_dt
            except (ValueError, TypeError):
                pass # Malformed date, treat as not expired for safety
            
            licenses.append(LicenseResponse(
                gist_id=gist_id,
                gist_name=gist_lick.get_gist_data(gist_id)['name'], # Get Gist name
                is_expired=is_expired_status,
                **item # Unpack existing license data
            ))
        return licenses
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gist with ID '{gist_id}' not found.")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/gists/{gist_id}/licenses", summary="Create License in a Gist", response_model=LicenseResponse, status_code=status.HTTP_201_CREATED)
async def create_license_in_gist(
    gist_id: str = Path(..., example="your_gist_id", description="The ID of the Gist to store the license"),
    license_create_data: LicenseCreate, # Use LicenseCreate model for body
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Create a new license entry within a specified Gist.
    Note: 'gist_id' in body is not used, only 'gist_id' in path.
    """
    # Validate plan against GistLick's allowed plans (e.g., ['free', 'trial', 'premium'])
    # This assumes gist_lick_core.py has a 'plan' attribute or list of valid plans.
    # For this example, we assume valid_plans are hardcoded in gistlick_core.py.
    
    try:
        new_license = gist_lick.create_license(
            gist_id=gist_id,
            user=license_create_data.user,
            plan=license_create_data.plan,
            machine=license_create_data.machine,
            expired_days=license_create_data.expired_days
        )
        return new_license
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gist with ID '{gist_id}' not found.")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.put("/gists/{gist_id}/licenses/{license_key}", summary="Update License in a Gist", response_model=LicenseResponse)
async def update_license_in_gist(
    gist_id: str = Path(..., example="your_gist_id", description="The ID of the Gist containing the license"),
    license_key: str = Path(..., example="ABCD-EFGH-IJKL-MNOP", description="The unique license key to update"),
    license_update_data: LicenseUpdate,
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Update a specific license entry within a Gist.
    """
    try:
        updated_license = gist_lick.update_license(
            gist_id=gist_id,
            license_key_to_update=license_key,
            user=license_update_data.user,
            plan=license_update_data.plan,
            machine=license_update_data.machine,
            created=license_update_data.created,
            expired=license_update_data.expired
        )
        return updated_license
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gist with ID '{gist_id}' not found.")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) # Use 404 for not found license
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/gists/{gist_id}/licenses/{license_key}", summary="Delete License from a Gist", response_model=MessageResponse, status_code=status.HTTP_204_NO_CONTENT)
async def delete_license_from_gist(
    gist_id: str = Path(..., example="your_gist_id", description="The ID of the Gist containing the license"),
    license_key: str = Path(..., example="ABCD-EFGH-IJKL-MNOP", description="The unique license key to delete"),
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Delete a specific license entry from a Gist.
    """
    try:
        gist_lick.delete_license(gist_id=gist_id, license_key=license_key)
        return MessageResponse(message=f"License '{license_key}' deleted from Gist '{gist_id}'.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gist with ID '{gist_id}' not found.")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) # Use 404 for not found license
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/gists/{gist_id}/licenses/expired", summary="Delete All Expired Licenses in a Gist", response_model=DeletedCountResponse)
async def delete_expired_licenses_in_gist(
    gist_id: str = Path(..., example="your_gist_id", description="The ID of the Gist to delete expired licenses from"),
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Delete all expired license entries from a specific Gist.
    """
    try:
        result = gist_lick.delete_expired_licenses(gist_id=gist_id)
        return DeletedCountResponse(message=result['message'], deleted_count=result['deleted_count'])
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gist with ID '{gist_id}' not found.")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- Raw Data Endpoints (Previously Logs) ---
@app.get("/gists/{gist_id}/raw_data", summary="Get Raw Gist Content", response_model=Union[str, List[Any], Dict[str, Any]])
async def get_raw_gist_content(
    gist_id: str = Path(..., example="your_gist_id", description="The ID of the Gist to retrieve raw content from"),
    file_name: Optional[str] = Query(None, description="Optional: Specify the filename if the Gist has multiple files. Defaults to the first file."),
    gist_lick: GistLick = Depends(get_gistlick_instance)
):
    """
    Retrieve the raw content of a specific Gist file.
    Content can be JSON (parsed into an object) or plain text.
    """
    try:
        content = gist_lick.get_gist_content(gist_id, file_name=file_name)
        return content
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Gist with ID '{gist_id}' not found.")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except ValueError as e: # Catch ValueErrors from GistLick (e.g., file not found in gist)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))