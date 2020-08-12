import datetime
import json
import os
from typing import Dict, Optional, Union

from legislice.download import (
    Client,
    LegislicePathError,
    LegisliceDateError,
    RawEnactment,
    normalize_path,
)

# A dict indexing responses by iso-format date strings.
ResponsesByDate = Dict[str, Dict]
ResponsesByDateByPath = Dict[str, Dict[str, Dict]]


class JSONRepository(Client):
    """Repository for mocking API responses locally."""

    def __init__(self, responses: ResponsesByDateByPath):
        self.responses = responses

    def get_entry_closest_to_cited_path(self, path: str) -> Optional[ResponsesByDate]:
        path = normalize_path(path)
        if self.responses.get(path):
            return self.responses[path]
        branches_that_start_path = [
            entry for entry in self.responses.keys() if path.startswith(entry)
        ]
        if not branches_that_start_path:
            return None
        name_of_best_entry = max(branches_that_start_path, key=len)
        return self.responses[name_of_best_entry]

    def search_tree_for_path(
        self, path: str, branch: Dict
    ) -> Optional[ResponsesByDate]:
        path = normalize_path(path)
        if branch["node"] == path:
            return branch
        branches_that_start_path = [
            nested_node
            for nested_node in branch["children"]
            if nested_node["node"].startswith(path)
        ]
        if branches_that_start_path:
            return self.search_tree_for_path(
                path=path, branch=branches_that_start_path[0]
            )
        return None

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
        responses = self.get_entry_closest_to_cited_path(path)
        if not responses:
            raise LegislicePathError(f"No enacted text found for query {path}")

        if isinstance(date, datetime.date):
            date = date.isoformat()

        if not date:
            selected_date = max(responses.keys())
        else:
            versions_not_later_than_query = [
                version_date
                for version_date in responses.keys()
                if version_date <= date
            ]
            if not versions_not_later_than_query:
                raise LegisliceDateError(
                    f"No enacted text found for query {path} after date {date}"
                )
            selected_date = max(versions_not_later_than_query)

        selected_version = responses[selected_date]

        result = self.search_tree_for_path(path=path, branch=selected_version)
        if not result:
            raise LegislicePathError(
                f"No enacted text found for query {path} after date {date}"
            )
        return result


def get_mock_responses(filename: str) -> Dict[str, Dict]:
    this_directory = os.path.dirname(os.path.abspath(__file__))
    responses_filepath = this_directory + "/mock_responses/" + filename
    with open(responses_filepath, "r") as f:
        responses = json.load(f)
    return responses


MOCK_USC_RESPONSES = get_mock_responses("usc.json")
MOCK_BEARD_ACT_RESPONSES = get_mock_responses("beard_act.json")

MOCK_USC_CLIENT = JSONRepository(responses=MOCK_USC_RESPONSES)
MOCK_BEARD_ACT_CLIENT = JSONRepository(responses=MOCK_BEARD_ACT_RESPONSES)
