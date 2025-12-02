"""
Authentication and Registration Schemas

Pydantic models for user authentication and tier assignment via invitation codes.
"""

from typing import Optional

from pydantic import BaseModel, Field


class RegistrationData(BaseModel):
    """
    User registration request with Firebase ID token and optional invitation code.

    Attributes:
        id_token: Firebase ID token for user authentication
        invitation_code: Optional invitation code for tier assignment (required if user not in unlimited list)
    """

    id_token: str = Field(..., description="Firebase ID token")
    invitation_code: Optional[str] = Field(
        None, description="Invitation code for tier assignment"
    )


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


class InvitationCodeRequest(BaseModel):
    """
    Request for invitation code from user.

    Attributes:
        first_name: User's first name
        last_name: User's last name
        email: User's email address
    """

    first_name: str = Field(
        ..., min_length=1, max_length=100, description="User's first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="User's last name"
    )
    email: str = Field(..., description="User's email address")


class InvitationCodeRequestResponse(BaseModel):
    """
    Response after invitation code request submission.

    Attributes:
        status: Success status
        message: Confirmation message
    """

    status: str = Field(..., description="Request status")
    message: str = Field(..., description="Confirmation message")
