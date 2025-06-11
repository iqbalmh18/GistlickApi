from fastapi import Header, HTTPException, Depends, status
from typing import Optional

from gistlick_core import GistLick

# Mengambil GITHUB_TOKEN dari environment variable.
# Anda perlu memastikan dotenv dimuat di main.py jika menggunakan .env file.
# atau gunakan Config management seperti Pydantic Settings
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

async def get_gistlick_instance(authorization: Optional[str] = Header(None)) -> GistLick:
    """
    Dependency to provide an authenticated GistLick instance.
    Expects a Bearer token in the Authorization header.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid. Use Bearer token."
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be 'Bearer TOKEN'"
        )
    
    github_token = parts[1]
    
    try:
        gist_lick = GistLick(token=github_token)
        # Verify the token by trying to get user info. This raises HTTPError if invalid.
        user_info = gist_lick.user 
        if not user_info.get('id'): # Check if user data is empty or invalid
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid GitHub token. Could not authenticate with GitHub."
            )
        return gist_lick
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {e}"
        )

# Dependency to get user info (optional, if you want to expose user info to endpoints)
async def get_current_user_info(gist_lick: GistLick = Depends(get_gistlick_instance)) -> Dict[str, Any]:
    return gist_lick.user