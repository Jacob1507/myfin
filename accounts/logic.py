from django.contrib.auth import get_user_model


User = get_user_model()


def create_user(username: str, password: str, email: str) -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user
