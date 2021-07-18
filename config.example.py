from pathlib import Path

SERVERS = {
    "build": {
        "rcon": 1234,
        "location": Path("/home/mcadmin/mcservers/build")
    },
    "school": {
        "rcon": 1235,
        "location": Path("/home/mcadmin/mcservers/school")
    }
}

RCON_PASS = "passwOREd"
DESTINATION = Path("/home/mcadmin/backups")
