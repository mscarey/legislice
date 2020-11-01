import datetime
from os import name
from typing import Any, Dict, List, Optional, Union

from marshmallow import ValidationError
from marshmallow.fields import Raw
import requests
from requests import status_codes

from legislice.enactments import Enactment, CrossReference, InboundReference
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


class LegisliceTokenError(Exception):
    pass


def normalize_path(path: str) -> str:
    return "/" + path.strip("/")


class Client:
    def __init__(
        self, api_token: str = "", api_root: str = "https://authorityspoke.com/api/v1"
    ):
        """Create download client with an API token and an API address."""
        self.api_root = api_root

        if api_token.startswith("Token "):
            api_token = api_token.split("Token ")[1]
        self.api_token = api_token

    def fetch(
        self, query: Union[str, CrossReference], date: Union[datetime.date, str] = ""
    ) -> RawEnactment:
        """
        Download legislative provision from string identifier or cross-reference.

        :param query:
            A cross-reference to the desired legislative provision, or a path to the
            desired legislation section using the United States Legislation Markup
            tree-like citation format.

        :param date:
            The date of the desired version of the provision to be downloaded. This is
            not needed if a :class:`~legislice.enactments.CrossReference` passed to the
            ``query`` param specifies a date. If no date is provided, the API will use the
            most recent date.
        """
        if isinstance(query, CrossReference):
            return self.fetch_cross_reference(query=query, date=date)
        return self.fetch_uri(query=query, date=date)

    def fetch_cross_reference(
        self, query: CrossReference, date: Union[datetime.date, str] = ""
    ) -> RawEnactment:
        """
        Download legislative provision from cross-reference.

        :param query:
            A cross-reference to the desired legislative provision. Found by calling the
            :meth:`~legislice.enactments.Enactment.cross_references` method on an
            :class:`~legislice.enactments.Enactment` that contains one or more citations
            to other provisions.

        :param date:
            The date of the desired version of the provision to be downloaded. This is
            not needed if the :class:`~legislice.enactments.CrossReference` passed to the
            ``query`` param specifies a date. If no date is provided, the API will use the
            most recent date.
        """
        if isinstance(date, datetime.date):
            date = date.isoformat()

        target = query.target_url

        if date:
            if "@" in target:
                if not target.endswith(date):
                    raise ValueError(
                        f"Date param {date} does not match date in URL {target}"
                    )
            else:
                target = f"{target}@{date}"

        if not target.startswith(self.api_root):
            raise ValueError(
                f'target_url of cross-reference, "{target}", does not start with Client\'s api_root, "{self.api_root}"'
            )
        return self._fetch_from_url(url=target)

    def fetch_uri(
        self, query: str, date: Union[datetime.date, str] = ""
    ) -> RawEnactment:
        """
        Fetches data about legislation at specified path and date from Client's assigned API root.

        :param query:
            A path to the desired legislation section using the United States Legislation Markup
            tree-like citation format. Examples: "/us/const/amendment/IV", "/us/usc/t17/s103"

        :param date:
            A date when the desired version of the legislation was in effect. This does not need to
            be the "effective date" or the first date when the version was in effect. However, if
            you select a date when two versions of the provision were in effect at the same time,
            you will be given the version that became effective later.
        """
        query_with_root = self.api_root + normalize_path(query)

        if isinstance(date, datetime.date):
            date = date.isoformat()
        if date:
            query_with_root = f"{query_with_root}@{date}"

        return self._fetch_from_url(url=query_with_root)

    def citations_to(
        self, enactment: Enactment, limit: int = 1
    ) -> List[InboundReference]:
        return []

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

    def read(
        self, query: Union[str, CrossReference], date: Union[datetime.date, str] = "",
    ) -> Enactment:
        """
        Fetches data from Client's assigned API root and builds Enactment or LinkedEnactment.

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
        raw_enactment = self.fetch(query=query, date=date)
        enactment = self.read_from_json(raw_enactment)
        enactment.select_all()
        return enactment

    def update_enactment_from_api(self, data: RawEnactment) -> RawEnactment:
        """
        Use API to fill in missing fields in a dict representing an :class:`~legislice.enactments.Enactment`.

        Useful when the dict has missing data because it was created by a user.
        """

        data_from_api = self.fetch(query=data["node"], date=data.get("start_date"))
        new_data = {**data, **data_from_api}
        return new_data

    def update_entries_in_enactment_index(
        self, enactment_index: EnactmentIndex
    ) -> EnactmentIndex:
        for key, value in enactment_index.items():
            if enactment_needs_api_update(value):
                enactment_index[key] = self.update_enactment_from_api(value)
        return enactment_index

    def _fetch_from_url(self, url: str) -> RawEnactment:
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"

        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            raise LegislicePathError(f"No enacted text found for query {url}")
        if response.status_code == 403:
            raise LegisliceTokenError(f"{response.json().get('detail')}")

        return response.json()
