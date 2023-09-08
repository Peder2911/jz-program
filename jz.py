import logging
import json
from typing import List, Optional
import os
import requests
import pydantic
import datetime
import humps
from functools import reduce


logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)
CACHE_DIR = os.path.expanduser("~/.cache/jz")

class Speaker(pydantic.BaseModel):
    name: str
    bio:  str

class Session(pydantic.BaseModel):
    intended_audience: Optional[str]               = None
    length:            Optional[int]               = None
    format:            Optional[str]               = None
    abstract:          Optional[str]               = None
    language:          Optional[str]               = None
    title:             Optional[str]               = None
    room:              Optional[str]               = None
    start_time:        Optional[datetime.datetime] = None
    end_time:          Optional[datetime.datetime] = None
    id:                Optional[str]               = None
    session_id:        Optional[str]               = None
    conference_id:     Optional[str]               = None
    start_slot:        Optional[str]               = None
    speakers:          Optional[List[Speaker]]     = None

    model_config = pydantic.ConfigDict(alias_generator=humps.camelize)

class Program(pydantic.BaseModel):
    sessions: List[Session]

    def __add__(self, other: "Program"):
        return Program(sessions = self.sessions + other.sessions)

def filecache(folder: str, model):
    def wrapper(fn):
        def inner(arg):
            cache_file_location = os.path.join(folder,arg) + ".json"
            try:
                with open(cache_file_location) as f:
                    result = model.model_validate_json(f.read())
                logger.info(f"Fetched {arg} from cache")
            except (FileNotFoundError, pydantic.ValidationError, json.JSONDecodeError):
                logger.info(f"{arg} not in cache, fetching from web")
                result = fn(arg)
                if result is not None:
                    with open(cache_file_location, "w") as f:
                        f.write(result.model_dump_json(by_alias = True))
            return result
        return inner
    return wrapper

class Conference(pydantic.BaseModel):
    id: str
    name: str
    slug: str

class Conferences(pydantic.BaseModel):
    conferences: List[Conference]

@filecache(CACHE_DIR, Program)
def fetch_conference_program(slug: str) -> Program:
    try:
        raw = requests.get(f"https://sleepingpill.javazone.no/public/allSessions/{slug}").content
        return Program.model_validate_json(raw)
    except pydantic.ValidationError:
        return None

def fetch_all_sessions():
    conferences = Conferences.model_validate_json(requests.get("https://sleepingpill.javazone.no/public/allSessions").content)
    conference_programs = [fetch_conference_program(c.slug) for c in conferences.conferences]
    return reduce(lambda a,b: a+b, [p for p in conference_programs if p is not None])

if __name__ == "__main__":
    print(fetch_all_sessions().json())
