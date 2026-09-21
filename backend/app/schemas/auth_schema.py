"""
Authentication and Registration Schemas
Pydantic models for user authentication and tier assignment.
"""

from pydantic import BaseModel, Field


class RegistrationData(BaseModel):
    """
    User registration request with Firebase ID token.

    Attributes:
        id_token: Firebase ID token for user authentication
    """

    id_token: str = Field(..., description="Firebase ID token")


class RegistrationResponse(BaseModel):
    """
    Response after successful registration with tier assignment.

    Attributes:
        status: Success status
        tier: Assigned tier (FREE, PRO, or UNLIMITED)
        message: Informational message about token refresh
    """

    status: str = Field(..., description="Registration status")
    tier: str = Field(..., description="Assigned tier (FREE, PRO, UNLIMITED)")
    message: str = Field(..., description="Additional information")
