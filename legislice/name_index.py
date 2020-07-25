from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

RawSelector = Union[str, Dict[str, str]]
RawEnactment = Dict[str, Union[Any, str, List[RawSelector]]]
RawPredicate = Dict[str, Union[str, bool]]
RawFactor = Dict[str, Union[RawPredicate, Sequence[Any], str, bool]]


class EnactmentIndex(OrderedDict):
    """Index of cross-referenced objects, keyed to phrases that reference them."""

    def insert_by_name(self, obj: Dict) -> None:
        """Add record to dict, using value of record's "name" field as the dict key."""
        self[obj["name"]] = obj.copy()
        self[obj["name"]].pop("name")
        return None

    def get_by_name(self, name: str) -> Dict:
        """
        Convert retrieved record so name is a field rather than the key for the whole record.
        :param name:
            the name of the key where the record can be found in the Mentioned dict.
        :returns:
            the value stored at the key "name", plus a name field.
        """
        if not self.get(name):
            raise ValueError(
                f'Name "{name}" not found in the index of mentioned Factors'
            )
        value = {"name": name}
        value.update(self[name])
        return value

    def sorted_by_length(self) -> Mentioned:
        """
        Sort dict items from longest to shortest.
        Used to ensure that keys nearer the start can't be substrings of later keys.
        """
        return Mentioned(sorted(self.items(), key=lambda t: len(t[0]), reverse=True))

    def __str__(self):
        return f"Mentioned({str(dict(self))})"

    def __repr__(self):
        return f"Mentioned({repr(dict(self))})"

    def enactment_has_anchor(
        self, enactment_name: str, anchor: Dict[str, Union[str, int]]
    ) -> bool:
        anchors_for_selected_element = self[enactment_name].get("anchors") or []
        return any(
            existing_anchor == anchor
            for existing_anchor in anchors_for_selected_element
        )

    def add_anchor_for_enactment(
        self, enactment_name: str, anchor: Dict[str, Union[str, int]]
    ) -> None:
        anchors_for_selected_element = self[enactment_name].get("anchors") or []
        if not self.enactment_has_anchor(enactment_name, anchor):
            anchors_for_selected_element.append(anchor)
        self[enactment_name]["anchors"] = anchors_for_selected_element

    def index_enactment(self, obj: RawEnactment) -> None:
        r"""
        Update index of mentioned Factors with 'obj', if obj is named.
        If there is already an entry in the mentioned index with the same name
        as obj, the old entry won't be replaced. But if any additional text
        anchors are present in the new obj, the anchors will be added.
        If obj has a name, it will be collapsed to a name reference.

        :param obj:
            data from JSON to be loaded as a :class:`.Enactment`
        """
        if obj.get("name"):
            if obj["name"] in self:
                if obj.get("anchors"):
                    for anchor in obj["anchors"]:
                        self.add_anchor_for_enactment(
                            enactment_name=obj["name"], anchor=anchor
                        )
            else:
                self.insert_by_name(obj)
        return None


def collect_mentioned(
    obj: Union[RawFactor, List[Union[RawFactor, str]]],
    mentioned: Optional[EnactmentIndex] = None,
    keys_to_ignore: Sequence[str] = ("predicate", "anchors"),
) -> Tuple[RawFactor, EnactmentIndex]:
    """
    Make a dict of all nested objects labeled by name, creating names if needed.
    To be used during loading to expand name references to full objects.
    """
    mentioned = mentioned or EnactmentIndex()
    if isinstance(obj, List):
        new_list = []
        for item in obj:
            new_item, new_mentioned = collect_mentioned(item, mentioned)
            mentioned.update(new_mentioned)
            new_list.append(new_item)
        obj = new_list
    if isinstance(obj, Dict):

        obj, mentioned = update_name_index_from_fact_content(obj, mentioned)

        for key, value in obj.items():
            if key not in keys_to_ignore:
                if isinstance(value, (Dict, List)):
                    new_value, new_mentioned = collect_mentioned(value, mentioned)
                    mentioned.update(new_mentioned)
                    obj[key] = new_value
        obj = ensure_factor_has_name(obj)

        obj, mentioned = update_name_index_with_factor(obj, mentioned)
    return obj, mentioned
