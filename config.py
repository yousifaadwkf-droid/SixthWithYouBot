import os

TOKEN = os.getenv("8389405270:AAENsM_XpYBfnbI54JWeTt9NqaD7pVqaA7E")

OWNER_ID = int(os.getenv("OWNER_ID", "606221907"))

ADMINS = list(
    map(
        int,
        os.getenv(
            "ADMINS",
            "606221907,1343055427,1736876324"
        ).split(",")
    )
)

BOT_NAME = os.getenv("BOT_NAME", "مساعد تجي🤍")