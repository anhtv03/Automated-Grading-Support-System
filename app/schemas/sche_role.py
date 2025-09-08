from pydantic import BaseModel


class RoleBase(BaseModel):
    model_config = {
        "from_attributes": True
    }


class RoleResponse(RoleBase):
    id: int
    name: str
