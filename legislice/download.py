import datetime
from typing import Any, Dict, List, Optional, Union

import requests

from legislice.enactments import (
    Enactment,
    CrossReference,
    CitingProvisionLocation,
    InboundReference,
)
from legislice.name_index import EnactmentIndex
from legislice.schemas import (
    InboundReferenceSchema,
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
        self,
        api_token: str = "",
        api_root: str = "https://authorityspoke.com/api/v1",
        update_coverage_from_api: bool = True,
    ):
        """Create download client with an API token and an API address."""
        self.api_root = api_root

        if api_token.startswith("Token "):
            api_token = api_token.split("Token ")[1]
        self.api_token = api_token
        self.coverage: Dict[str, Dict[str, Union[datetime.date, str]]] = {
            "/us/const": {
                "first_published": datetime.date(1788, 6, 21),
                "earliest_in_db": datetime.date(1788, 6, 21),
            }
        }
        self.update_coverage_from_api = update_coverage_from_api

    def fetch(
        self,
        query: Union[str, CitingProvisionLocation, CrossReference, InboundReference],
        date: Union[datetime.date, str] = "",
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
        elif isinstance(query, CitingProvisionLocation):
            return self.fetch_citing_provision(query=query)
        elif isinstance(query, InboundReference):
            return self.fetch_inbound_reference(query=query)
        return self.fetch_uri(query=query, date=date)

    def fetch_citing_provision(self, query: CitingProvisionLocation) -> RawEnactment:
        """
        Download legislative provision as Enactment from CitingProvisionLocation.

        CitingProvisionLocations are found in the `locations` attribute of the `InboundReference`
        objects obtained when using the `citations_to` method.
        """
        return self.fetch_uri(query=query.node, date=query.start_date)

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
        return self._fetch_from_url(url=target).json()

    def fetch_db_coverage(self, code_uri: str) -> Dict[str, datetime.date]:
        target = self.api_root + "/coverage" + code_uri
        coverage = self._fetch_from_url(url=target).json()
        for k, v in coverage.items():
            if k not in ("uri", "latest_heading"):
                coverage[k] = datetime.date.fromisoformat(v)
        return coverage

    def fetch_inbound_reference(self, query: InboundReference) -> RawEnactment:
        """
        Download legislative provision from InboundReference.

        :param query:
            An InboundReference identifying a provision containing a citation.

        :returns:
            An Enactment representing the provision containing the citation (not the cited provision).

        If the InboundReference has been enacted more than once, the latest one will be chosen.
        """
        most_recent = max(query.locations)
        return self.fetch_citing_provision(query=most_recent)

    def get_db_coverage(self, uri: str) -> str:
        """
        Add data about the API's coverage date range to the Enactment to be loaded.

        As a side effect, changes the Client's "coverage" attribute.

        :param uri:
            identifier for the Enactment to be created

        :returns:
            identifier for the Code of the Enactment to be created
        """
        uri_parts = uri.split("/")
        code_uri = ""
        if len(uri_parts) > 2:
            code_uri = f"/{uri_parts[1]}/{uri_parts[2]}"
            if self.update_coverage_from_api and not self.coverage.get(code_uri):
                self.coverage[code_uri] = self.fetch_db_coverage(code_uri)
        return code_uri

    def url_from_enactment_uri(
        self, uri: str, date: Union[datetime.date, str] = ""
    ) -> str:
        query_with_root = self.api_root + normalize_path(uri)

        if isinstance(date, datetime.date):
            date = date.isoformat()
        if date:
            query_with_root = f"{query_with_root}@{date}"
        elif not query_with_root.endswith("/"):
            query_with_root += "/"
        return query_with_root

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
        url = self.url_from_enactment_uri(uri=query, date=date)
        response = self._fetch_from_url(url=url)
        return response.json()

    def uri_from_query(self, target: Union[str, Enactment, CrossReference]) -> str:
        if isinstance(target, Enactment):
            return target.node
        elif isinstance(target, CrossReference):
            return target.target_uri
        return target

    def fetch_citations_to(
        self, target: Union[str, Enactment, CrossReference]
    ) -> List[Dict]:
        """
        Query API for citations to a given target node, withoout loading them as InboundCitations.

        :param target:
            a string URI for the cited node, an Enactment at the cited node, or
            a CrossReference to the cited node

        :returns:
            a list of dicts representing citations to the cited node
        """
        uri = self.uri_from_query(target)
        query_with_root = self.api_root + "/citations_to" + uri
        api_response = self._fetch_from_url(query_with_root)
        return api_response.json()["results"]

    def citations_to(
        self, target: Union[str, Enactment, CrossReference]
    ) -> List[InboundReference]:
        r"""
        Load an InboundReference object for each provision citing the target USLM provision URI.

        :param target:
            a string URI for the cited node, an Enactment at the cited node, or
            a CrossReference to the cited node

        :returns:
            a list of InboundReferences to the cited node
        """
        target_uri = self.uri_from_query(target)
        json_citations = self.fetch_citations_to(target_uri)
        for entry in json_citations:
            entry["target_uri"] = target_uri
        schema = InboundReferenceSchema(many=True)
        citations = schema.load(json_citations)
        return citations

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

        # update client's data about the database's coverage
        code_uri = self.get_db_coverage(data["node"])
        if self.coverage.get(code_uri):
            schema.context["coverage"] = self.coverage[code_uri]

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
        """Fill in missing fields in every entry in an :class:`~legislice.name_index.EnactmentIndex`."""
        for key, value in enactment_index.items():
            if enactment_needs_api_update(value):
                enactment_index[key] = self.update_enactment_from_api(value)
        return enactment_index

    def _fetch_from_url(self, url: str) -> requests.Response:
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Token {self.api_token}"

        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            raise LegislicePathError(f"No enacted text found for query {url}")
        if response.status_code == 403:
            raise LegisliceTokenError(f"{response.json().get('detail')}")

        return response
