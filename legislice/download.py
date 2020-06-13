import datetime
from typing import Any, Dict, Optional, Union

import requests

from legislice.enactments import Enactment
from legislice.schemas import EnactmentSchema

RawEnactment = Dict[str, Any]


class Client:
    def __init__(
        self, api_token: str = "", endpoint: str = "https://authorityspoke.com/api/v1"
    ):
        self.endpoint = endpoint

        if api_token.startswith("Token "):
            api_token = api_token.split("Token ")[1]
        self.api_token = api_token

    def fetch(self, uri: str, date: Union[datetime.date, str] = "") -> RawEnactment:
        query = self.endpoint + uri
        if isinstance(date, datetime.date):
            date = date.isoformat()
        if date:
            query = f"{query}@{date}"

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"

        response = requests.get(query, headers=headers)
        return response.json()

    def read(self, uri: str, date: Union[datetime.date, str] = "") -> Enactment:
        raw_enactment = self.fetch(uri=uri, date=date)
        schema = EnactmentSchema()
        enactment = schema.load(raw_enactment)
        return enactment
