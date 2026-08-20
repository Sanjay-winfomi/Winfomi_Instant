"""Company-portal authentication. Login is the only public endpoint here - everything
else requires a valid JWT (services/auth.get_current_company_user), enforced
server-side, never trusting anything the frontend claims about its own role."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.store import get_user_by_email
from schemas.auth import CompanyLoginRequest, CompanyLoginResponse, CompanyUser
from services.auth import CurrentCompanyUser, create_access_token, get_current_company_user, verify_password

router = APIRouter(prefix="/api/company/auth", tags=["company-auth"])


@router.post("/login", response_model=CompanyLoginResponse)
def login(request: CompanyLoginRequest) -> CompanyLoginResponse:
    user = get_user_by_email(request.email.strip().lower())
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return CompanyLoginResponse(access_token=create_access_token(user))


@router.get("/me", response_model=CompanyUser)
def me(current: CurrentCompanyUser = Depends(get_current_company_user)) -> CompanyUser:
    return CompanyUser(id=current.id, email=current.email, name=current.email.split("@")[0], role=current.role)
