from ..user.models import UserStatus, UserType
from ..user.schema import UserCreate, UserUpdate
from ..core.exceptions import BadRequestError

nullable_pwd_user_types = [UserType.SYSTEM, UserType.ROBOT, UserType.PLC]


def validate_auth_on_create(user: UserCreate) -> None:
    if user.password is not None and user.user_type in nullable_pwd_user_types:
        raise BadRequestError(f"Password is not allowed for user type {user.user_type.value}")
    
    if user.password is None and user.user_type not in nullable_pwd_user_types:
        raise BadRequestError(f"Password is required for user type {user.user_type.value}")

def validate_auth_on_update(user, updates: UserUpdate) -> None:
    user_type_update = updates.user_type if updates.user_type is not None else user.user_type
    status_update = updates.status if updates.status is not None else user.status
    is_password_sent = "password" in updates.model_fields_set
    password_hash_exists = user.password_hash is not None

    # if password is sent, derive resulting hash existence from payload intent
    if is_password_sent:
        password_hash_exists = updates.password is not None

    if user_type_update == UserType.HUMAN and not password_hash_exists:
        raise BadRequestError("Human users must have a password hash")

    if is_password_sent and updates.password is not None and user_type_update in nullable_pwd_user_types:
        raise BadRequestError(f"Password is not allowed for user type {user_type_update.value}")

    # transitioning to non-human/system-robot-plc with existing password hash is invalid
    if user_type_update in nullable_pwd_user_types and password_hash_exists:
        raise BadRequestError(f"Password must be removed before changing user type to {user_type_update.value}")
    
    # deleted users must not keep password hash per DB constraint
    if status_update == UserStatus.DELETED and password_hash_exists:
        raise BadRequestError("Deleted users must not keep password hash")