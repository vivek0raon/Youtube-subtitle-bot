from redis import Redis
# from dotenv import load_dotenv 
import logging
# load_dotenv()
import os

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s]%(asctime)s - %(message)s"
)


log = logging.getLogger("Database")
log.info("\n\n Connecting to database")


try:
    REDIS_URI = os.getenv("REDIS_URI")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
except Exception as e:
    log.exception(e)
    exit(1)

REDIS_URI = REDIS_URI.split(":")
db = Redis(
    host=REDIS_URI[0],
    port=REDIS_URI[1],
    password=REDIS_PASSWORD,
    decode_responses=True
)

def str_to_list(text):
    return text.split(" ")

def list_to_str(list):
    str = " ".join(x for x in list)
    return str.strip()

def get_all(var) -> list:
    """ get user data """
    try:
        users = db.get(var)
    except Exception as e:
        log.exception(e)
    if users is None or users == "":
        return [""]
    else:
        return str_to_list(users)


def is_added(var, id) -> bool:
    """ check if user data is added """ 
    if not str(id).isdigit():
        return False
    users = get_all(var)
    return str(id) in users



def add_to_db(var, id) -> bool:
    """check if user is in database"""
    id = str(id)
    if not id.isdigit():
        return False
    try:
        users = get_all(var)
        users.append(id)
        db.set(var, list_to_str(users))
        return True
    except Exception as e:
        return False