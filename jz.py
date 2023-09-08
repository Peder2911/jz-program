from typing import List, Optional
import os
import re
import requests
import bs4
import chompjs
import pydantic
import datetime
import humps

class Speaker(pydantic.BaseModel):
    name: str
    bio:  str

class Session(pydantic.BaseModel):
    intended_audience: Optional[str]               = None
    length:            Optional[int]               = None
    format:            Optional[str]               = None
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


def fetch_program(cache_folder: str, url: str, year: int = 2023):
    cache_path = os.path.join(cache_folder, f"{year}.json")
    try:
        with open(cache_path) as f:
            program = Program.model_validate_json(f.read())
    except FileNotFoundError:
        rsp = requests.get(url)
        soup = bs4.BeautifulSoup(rsp.content)
        scripts = soup.find_all("script")
        objects = chompjs.parse_js_object(chompjs.parse_js_object(scripts[-1].text)[1])
        program = Program(sessions = sessions([*objects]))
        with open(cache_path,"w") as f:
            f.write(program.model_dump_json(by_alias = True))
    return program

def find_json(code):
    return re.findall("\\{[^\\}]+\\}",code)

def dequote(code,marker:str="DEEPQUOTEMARKER"):
    return code.replace("\\\\\\",marker).replace("\\","").replace(marker,"\\")

def sessions(objects):
    return dictfind("sessions", objects)


def dictfind(key: str, x):
    if type(x) is list:
        for item in x:
            found = dictfind(key, item)
            if found:
                return found
    elif type(x) is dict:
        found = x.get(key)
        if not found:
            for subkey in x:
                found = dictfind(key, x[subkey])
                if found:
                    return found 
        else:
            return found
    return None

if __name__ == "__main__":
    cache_folder = os.path.expanduser("~/.cache/jz")
    os.makedirs(cache_folder, exist_ok = True)
    print(fetch_program(cache_folder, "https://2023.javazone.no/program").json())
