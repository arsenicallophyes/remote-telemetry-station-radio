from typing import Set, Dict, Tuple
from ...models.model import UserID


# Rework entire class, compare hashes not passwords, load from environment/database not variables
class AuthService:

    def __init__(self, admin_users: Set[UserID], users_list: Dict[UserID, Tuple[str, str]]) -> None:
        self._admins = admin_users
        self.users_list = users_list

    def is_admin(self, user: UserID) -> bool:
        return user in self._admins

    def verify_user(self, user: UserID, password: str):
        """Return *True* iff the supplied credentials match the user registry."""
        try:
            return self.users_list[user][0] == password
        except KeyError:
            return False
