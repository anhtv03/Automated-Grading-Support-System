from fastapi import HTTPException, Depends

from app.db.models import Users
from app.services.jwt_service import JwtService


def login_required(http_authorization_credentials=Depends(JwtService().reusable_oauth2)):
    return JwtService().validate_token(http_authorization_credentials)


class PermissionRequired:
    def __init__(self, *args):
        self.user = None
        self.permissions = args

    def __call__(self, user: Users = Depends(login_required)):
        self.user = user
        if self.user.role.name not in self.permissions and self.permissions:
            raise HTTPException(status_code=400,
                                detail=f'You can not this permission')
