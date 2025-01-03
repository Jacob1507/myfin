from ninja import Schema


class UserLoginSchema(Schema):
    username: str
    password: str


class RegisterSchema(Schema):
    username: str
    password: str
    repeat_password: str
    email: str


class TokenSchema(Schema):
    api_key: str
