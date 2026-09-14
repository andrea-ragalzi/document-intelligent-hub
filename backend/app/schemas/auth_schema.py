"""
Authentication and Registration Schemas

Pydantic models for user authentication and tier assignment via invitation codes.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegistrationData(BaseModel):
    """
    User registration request with Firebase ID token and optional invitation code.

    Attributes:
        id_token: Firebase ID token for user authentication
        invitation_code: Optional invitation code for elevated tier assignment
    """

    id_token: str = Field(..., description="Firebase ID token")
    invitation_code: str | None = Field(
        None, description="Optional invitation code for elevated tier assignment"
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

    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    email: EmailStr = Field(..., max_length=254, description="User's email address")

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_required_names(cls, value: object) -> object:
        """Reject whitespace-only public form values after normalization."""
        if isinstance(value, str):
            return value.strip()
        return value


class InvitationCodeRequestResponse(BaseModel):
    """
    Response after invitation code request submission.

    Attributes:
        status: Success status
        message: Confirmation message
    """

    status: str = Field(..., description="Request status")
    message: str = Field(..., description="Confirmation message")
