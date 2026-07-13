import os

TOKEN = os.getenv("8389405270:AAHbJvyYXB7vySLnTaUkukHyt5oob5vWZJA")

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