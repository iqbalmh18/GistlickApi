from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserInfo(BaseModel):
    id: int
    user: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    created: str
    updated: str
    followers: int
    following: int

class GistBase(BaseModel):
    name: str = Field(..., example="my_awesome_gist.json", description="Filename of the Gist (e.g., 'data.json')")
    public: bool = Field(False, description="Whether the Gist is public")
    description: Optional[str] = Field(None, example="My description", description="Description of the Gist")

class GistCreate(GistBase):
    pass 

class GistUpdate(GistBase):
    content: Optional[Union[str, List[Any], Dict[str, Any]]] = Field(None, description="Content of the Gist file (can be JSON or plain text)")

class GistResponse(GistBase):
    id: str = Field(..., example="a1b2c3d4e5f6g7h8i9j0", description="Unique ID of the Gist")
    url: str = Field(..., example="https://gist.githubusercontent.com/username/gist_id/raw", description="Raw URL of the Gist content")
    created: str = Field(..., example="2023-01-01T12:00:00Z", description="Creation timestamp")
    updated: str = Field(..., example="2023-01-01T13:00:00Z", description="Last update timestamp")

    @validator('created', 'updated', pre=True)
    def parse_github_datetime(cls, v):
        if isinstance(v, str) and 'T' in v and 'Z' in v:
            return v
        return v 
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class LicenseBase(BaseModel):
    user: str = Field(..., example="john.doe", description="User or client name for the license")
    plan: str = Field(..., example="premium", description="License plan (e.g., 'free', 'trial', 'premium')")
    machine: str = Field(..., example="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6", description="Unique machine identifier (SHA256 hash)")
    created: str = Field(..., example="2024-01-01 10:00:00", description="License creation timestamp (YYYY-MM-DD HH:MM:SS)")
    expired: str = Field(..., example="2024-01-31 10:00:00", description="License expiration timestamp (YYYY-MM-DD HH:MM:SS)")

class LicenseCreate(LicenseBase):
    gist_id: str = Field(..., example="your_gist_id", description="ID of the Gist where the license will be stored")
    expired_days: int = Field(30, gt=0, description="Number of days until the license expires from creation")

class LicenseUpdate(LicenseBase):
    pass 

class LicenseResponse(LicenseBase):
    license: str = Field(..., example="ABCD-EFGH-IJKL-MNOP", description="The unique license key")
    is_expired: bool = Field(False, description="True if the license has expired")
    gist_id: Optional[str] = Field(None, description="The Gist ID where this license resides")
    gist_name: Optional[str] = Field(None, description="The name of the Gist file")

class MessageResponse(BaseModel):
    message: str = Field(..., example="Operation successful.")

class DeletedCountResponse(BaseModel):
    message: str
    deleted_count: int