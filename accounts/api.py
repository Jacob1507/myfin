from ninja import Router

from .logic import create_user
from .schemas import RegisterSchema

register_router = Router()


REGISTER_ERROR_RESULT = dict(msg="Provided register information is not correct")


@register_router.post("/register/")
def register_user(request, data: RegisterSchema):
    if data.password != data.repeat_password:
        return 400, REGISTER_ERROR_RESULT

    create_user(username=data.username, password=data.password, email=data.email)
    return 200, dict(msg="Registered successfully")
