from datetime import date
from typing import Any, Dict


import requests

RawEnactment = Dict[str, Any]


def fetch(uri: str, endpoint: str = "http://127.0.0.1:8000/api/v1") -> RawEnactment:
    query = endpoint + uri
    response = requests.get(query)
    return response.json()
