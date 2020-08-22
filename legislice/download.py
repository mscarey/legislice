import datetime
from os import name
from typing import Any, Dict, List, Optional, Union

from marshmallow import ValidationError
import requests

from legislice.enactments import Enactment
from legislice.name_index import EnactmentIndex
from legislice.schemas import (
    ExpandableSchema,
    get_schema_for_node,
    enactment_needs_api_update,
)

RawEnactment = Dict[str, Any]


class LegislicePathError(Exception):
    pass


class LegisliceDateError(Exception):
    pass


def normalize_path(path: str) -> str:
    return "/" + path.strip("/")


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
            raise LegislicePathError(f"No enacted text found for query {query}")

        return response.json()

    def read_from_json(self, data: RawEnactment) -> Enactment:
        r"""
        Create a new :class:`Enactment` object using imported JSON data.

        If fields are missing from the JSON, they will be fetched using the API key.
        """
        data_has_selection_field = "selection" in data.keys()

        if enactment_needs_api_update(data):
            data = self.update_enactment_from_api(data)
        schema_class = get_schema_for_node(data["node"])
        schema = schema_class()
        enactment = schema.load(data)

        if not enactment.selected_text() and not data_has_selection_field:
            enactment.select_all()
        return enactment

    def read(self, path: str, date: Union[datetime.date, str] = "",) -> Enactment:
        """
        Fetches data from Client's assigned endpoint and builds Enactment or LinkedEnactment.

        All text is selected by default.

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
        enactment = self.read_from_json(raw_enactment)
        enactment.select_all()
        return enactment

    def update_enactment_from_api(self, data: RawEnactment) -> RawEnactment:
        data_from_api = self.fetch(path=data["node"], date=data.get("start_date"))
        new_data = {**data, **data_from_api}
        return new_data

    def list_enactments_needing_updates(
        self, enactment_index: EnactmentIndex
    ) -> List[str]:
        need_updates = []
        for name, record in enactment_index.items():
            if enactment_needs_api_update(record):
                need_updates.append(name)
        return need_updates

    def update_entries_in_enactment_index(
        self, enactment_index: EnactmentIndex
    ) -> EnactmentIndex:
        for key, value in enactment_index.items():
            if enactment_needs_api_update(value):
                enactment_index[key] = self.update_enactment_from_api(value)
        return enactment_index
