from pathlib import Path
import json
import re

from setup.constants import (
    DEFAULT_USER_NAME,
    FILE_ENCODING,
    USERS_CONFIG_FILE,
    USERS_DIR,
    LOGS_DIR_NAME,
    SETTINGS_FILE_NAME,
)

# =============================================================================
class UserManager:

    def __init__(self) -> None:

        self.users: list[str] = []
        self.current_user: str = ""

        self.load()

    # ------------------------------------------------------------------
    def load(self) -> None:

        if not USERS_CONFIG_FILE.exists():

            self.users = [DEFAULT_USER_NAME]
            self.current_user = DEFAULT_USER_NAME

            self._create_user_directory(
                DEFAULT_USER_NAME
            )

            self.save()

            return

        try:

            with USERS_CONFIG_FILE.open(
                "r",
                encoding=FILE_ENCODING,
            ) as rfile:

                data = json.load(rfile)

            users = data.get("users", [])
            current = data.get("current_user")

            if not isinstance(users, list):
                raise ValueError

            users = [
                str(name)
                for name in users
                if str(name).strip()
            ]

            if not users:
                users = [DEFAULT_USER_NAME]

            if current not in users:
                current = users[0]

            self.users = users
            self.current_user = current

            for name in self.users:
                self._create_user_directory(name)

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):

            self.users = [DEFAULT_USER_NAME]
            self.current_user = DEFAULT_USER_NAME

            self._create_user_directory(
                DEFAULT_USER_NAME
            )

            self.save()

    # ------------------------------------------------------------------
    def save(self) -> None:

        USERS_CONFIG_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with USERS_CONFIG_FILE.open(
            "w",
            encoding=FILE_ENCODING,
        ) as wfile:

            json.dump(
                {
                    "current_user": self.current_user,
                    "users": self.users,
                },
                wfile,
                indent=4,
                ensure_ascii=False,
            )

    # ------------------------------------------------------------------
    def _create_user_directory(
        self,
        name: str,
    ) -> Path:

        user_dir = USERS_DIR / self.safe_name(name)

        user_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        (user_dir / LOGS_DIR_NAME).mkdir(
            exist_ok=True,
        )

        return user_dir

    # ------------------------------------------------------------------
    @staticmethod
    def safe_name(name: str) -> str:

        name = name.strip()

        name = re.sub(
            r'[<>:"/\\|?*]',
            "_",
            name,
        )

        name = name.rstrip(". ")

        return name or DEFAULT_USER_NAME

    # ------------------------------------------------------------------
    def user_dir(
        self,
        name: str | None = None,
    ) -> Path:

        if name is None:
            name = self.current_user

        return USERS_DIR / self.safe_name(name)

    # ------------------------------------------------------------------
    def settings_file(
        self,
        name: str | None = None,
    ) -> Path:

        return self.user_dir(name) / SETTINGS_FILE_NAME

    # ------------------------------------------------------------------
    def logs_dir(
        self,
        name: str | None = None,
    ) -> Path:

        return self.user_dir(name) / LOGS_DIR_NAME

    # ------------------------------------------------------------------
    def add_user(
        self,
        name: str,
    ) -> bool:

        name = name.strip()

        if not name:
            return False

        if name in self.users:
            return False

        self.users.append(name)

        self._create_user_directory(name)

        self.current_user = name

        self.save()

        return True

    # ------------------------------------------------------------------
    def select_user(
        self,
        name: str,
    ) -> bool:

        if name not in self.users:
            return False

        self.current_user = name

        self._create_user_directory(name)

        self.save()

        return True