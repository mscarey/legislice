from copy import deepcopy
import datetime
from typing import Any, Dict, List, Union

import requests

from legislice.enactments import Enactment
from legislice.name_index import collect_enactments
from legislice.schemas import LinkedEnactmentSchema, EnactmentSchema, ValidationError

RawEnactment = Dict[str, Any]


def normalize_path(path: str) -> str:
    return "/" + path.strip("/")


def get_schema_for_node(path: str):
    if path.count("/") < 4:
        return LinkedEnactmentSchema
    return EnactmentSchema


class Client:
    def __init__(
        self, api_token: str = "", endpoint: str = "https://authorityspoke.com/api/v1"
    ):
        self.endpoint = endpoint

        if api_token.startswith("Token "):
            api_token = api_token.split("Token ")[1]
        self.api_token = api_token

    def fetch(self, path: str, date: Union[datetime.date, str] = "") -> RawEnactment:
        """
        Fetches data about legislation at specified path and date from Client's assigned endpoint.

        :param path:
            A path to the desired legislation section using the United States Legislation Markup
            tree-like citation format. Examples: "/us/const/amendment/IV", "/us/usc/t17/s103"

        :param date:
            A date when the desired version of the legislation was in effect. This does not need to
            be the "effective date" or the first date when the version was in effect. However, if
            you select a date when two versions of the provision were in effect at the same time,
            you will be given the version that became effective later.
        """
        query = self.endpoint + normalize_path(path)

        if isinstance(date, datetime.date):
            date = date.isoformat()
        if date:
            query = f"{query}@{date}"

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"

        response = requests.get(query, headers=headers)
        if response.status_code == 404:
            raise ValueError(f"No enacted text found for query {query}")

        return response.json()

    def read(self, path: str, date: Union[datetime.date, str] = "",) -> Enactment:
        """
        Fetches data from Client's assigned endpoint and builds Enactment or LinkedEnactment.

        :param path:
            A path to the desired legislation section using the United States Legislation Markup
            tree-like citation format. Examples: "/us/const/amendment/IV", "/us/usc/t17/s103"

        :param date:
            A date when the desired version of the legislation was in effect. This does not need to
            be the "effective date" or the first date when the version was in effect. However, if
            you select a date when two versions of the provision were in effect at the same time,
            you will be given the version that became effective later.
        """
        raw_enactment = self.fetch(path=path, date=date)
        schema_class = get_schema_for_node(path)
        schema = schema_class()
        enactment = schema.load(raw_enactment)
        return enactment

    def update_enactment_if_invalid(self, data: RawEnactment) -> RawEnactment:
        if not data.get("node"):
            raise ValueError(
                '"data" must contain a "node" field '
                "with a citation path to a legislative provision, "
                'for example "/us/const/amendment/IV"'
            )
        schema_class = get_schema_for_node(data["node"])
        schema = schema_class()
        try:
            schema.load(data)
        except ValidationError:
            data_from_api = self.fetch(path=data["node"], date=data.get("start_date"))
            new_data = {**data, **data_from_api}
            return new_data
        return data

    def read_from_json(self, data: List[RawEnactment]) -> List[Enactment]:
        r"""
        Create a new :class:`Enactment` object using imported JSON data.

        If fields are missing from the JSON, they will be fetched using the API key.
        """
        schema = EnactmentSchema()
        record, mentioned = collect_enactments(data)
        for key, value in mentioned.items():
            mentioned[key] = self.update_enactment_if_invalid(value)
        schema.context["mentioned"] = mentioned
        return schema.load(deepcopy(record))

