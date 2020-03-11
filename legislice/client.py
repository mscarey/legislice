import datetime
from typing import Any, Dict, Union


import requests

RawEnactment = Dict[str, Any]


def fetch(
    uri: str,
    date: Union[datetime.date, str] = "",
    endpoint: str = "http://127.0.0.1:8000/api/v1",
) -> RawEnactment:
    query = endpoint + uri
    if isinstance(date, datetime.date):
        date = date.isoformat()
    if date:
        query = f"{query}@{date}"
    response = requests.get(query)
    return response.json()
