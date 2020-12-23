import datetime
import json
import os
from typing import Dict

from anchorpoint import TextQuoteSelector
from dotenv import load_dotenv
import pytest

from legislice.download import Client

load_dotenv()

API_ROOT = os.getenv("API_ROOT")
TOKEN = os.getenv("LEGISLICE_API_TOKEN")


@pytest.fixture(scope="module")
def vcr_config():
    return {
        # Replace the Authorization request header with "DUMMY" in cassettes
        "filter_headers": [("authorization", "DUMMY")],
    }


@pytest.fixture(scope="class")
def test_client() -> Client:
    client = Client(api_token=TOKEN, api_root=API_ROOT)
    client.coverage["/us/usc"] = {
        "latest_heading": "United States Code (USC)",
        "first_published": datetime.date(1926, 6, 30),
        "earliest_in_db": datetime.date(2013, 7, 18),
        "latest_in_db": datetime.date(2020, 8, 8),
    }
    client.coverage["/test/acts"] = {
        "latest_heading": "Test Acts",
        "first_published": datetime.date(1935, 4, 1),
        "earliest_in_db": datetime.date(1935, 4, 1),
        "latest_in_db": datetime.date(2013, 7, 18),
    }
    return client


@pytest.fixture(scope="class")
def section6d():
    return {
        "heading": "Waiver of beard tax in special circumstances",
        "content": "",
        "children": [
            {
                "heading": "",
                "content": "The Department of Beards shall waive the collection of beard tax upon issuance of beardcoin under Section 6C where the reason the maintainer wears a beard is due to bona fide religious, cultural, or medical reasons.",
                "children": [],
                "end_date": None,
                "node": "/test/acts/47/6D/1",
                "start_date": "2013-07-18",
                "url": "http://127.0.0.1:8000/api/v1/test/acts/47/6D/1@2018-03-11",
            },
            {
                "heading": "",
                "content": "The determination of the Department of Beards as to what constitutes bona fide religious or cultural reasons shall be final and no right of appeal shall exist.",
                "children": [],
                "end_date": None,
                "node": "/test/acts/47/6D/2",
                "start_date": "1935-04-01",
                "url": "http://127.0.0.1:8000/api/v1/test/acts/47/6D/2@2018-03-11",
            },
        ],
        "end_date": None,
        "node": "/test/acts/47/6D",
        "start_date": "1935-04-01",
        "url": "http://127.0.0.1:8000/api/v1/test/acts/47/6D@2018-03-11",
        "parent": "http://127.0.0.1:8000/api/v1/test/acts/47@2018-03-11",
    }


@pytest.fixture(scope="class")
def section_11_together():
    return {
        "heading": "Licensed repurchasers of beardcoin",
        "content": "The Department of Beards may issue licenses to such barbers, hairdressers, or other male grooming professionals as they see fit to purchase a beardcoin from a customer whose beard they have removed, and to resell those beardcoins to the Department of Beards.",
        "children": [],
        "end_date": "2013-07-18",
        "node": "/test/acts/47/11",
        "start_date": "1935-04-01",
        "url": "https://authorityspoke.com/api/v1/test/acts/47/11@1999-01-01",
        "parent": "https://authorityspoke.com/api/v1/test/acts/47@1999-01-01",
    }


@pytest.fixture(scope="class")
def citation_to_6c():
    return {
        "target_uri": "/test/acts/47/6C",
        "target_url": f"{API_ROOT}/test/acts/47/6C@1940-01-01",
        "target_node": 1660695,
        "reference_text": "Section 6C",
    }


@pytest.fixture(scope="function")
def section_11_subdivided():
    return {
        "heading": "Licensed repurchasers of beardcoin",
        "start_date": "2013-07-18",
        "node": "/test/acts/47/11",
        "text_version": {
            "id": 1142710,
            "url": "https://authorityspoke.com/api/v1/textversions/1142710/",
            "content": "The Department of Beards may issue licenses to such",
        },
        "url": "https://authorityspoke.com/api/v1/test/acts/47/11/",
        "end_date": None,
        "children": [
            {
                "heading": "",
                "start_date": "2013-07-18",
                "node": "/test/acts/47/11/i",
                "text_version": {
                    "id": 1142704,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142704/",
                    "content": "barbers,",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/i/",
                "end_date": None,
                "children": [],
                "citations": [],
            },
            {
                "heading": "",
                "start_date": "2013-07-18",
                "node": "/test/acts/47/11/ii",
                "text_version": {
                    "id": 1142705,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142705/",
                    "content": "hairdressers, or",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/ii/",
                "end_date": None,
                "children": [],
                "citations": [],
            },
            {
                "heading": "",
                "start_date": "2013-07-18",
                "node": "/test/acts/47/11/iii",
                "text_version": {
                    "id": 1142706,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142706/",
                    "content": "other male grooming professionals",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iii/",
                "end_date": None,
                "children": [],
                "citations": [],
            },
            {
                "heading": "",
                "start_date": "2013-07-18",
                "node": "/test/acts/47/11/iii-con",
                "text_version": {
                    "id": 1142707,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142707/",
                    "content": "as they see fit to purchase a beardcoin from a customer",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iii-con/",
                "end_date": None,
                "children": [],
                "citations": [],
            },
            {
                "heading": "",
                "start_date": "2013-07-18",
                "node": "/test/acts/47/11/iv",
                "text_version": {
                    "id": 1142708,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142708/",
                    "content": "whose beard they have removed,",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iv/",
                "end_date": None,
                "children": [],
                "citations": [],
            },
            {
                "heading": "",
                "start_date": "2013-07-18",
                "node": "/test/acts/47/11/iv-con",
                "text_version": {
                    "id": 1142709,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142709/",
                    "content": "and to resell those beardcoins to the Department of Beards.",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iv-con/",
                "end_date": None,
                "children": [],
                "citations": [],
            },
        ],
        "citations": [],
        "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
    }


@pytest.fixture(scope="module")
def make_selector() -> Dict[str, TextQuoteSelector]:
    return {
        "bad_selector": TextQuoteSelector(exact="text that doesn't exist in the code"),
        "preexisting material": TextQuoteSelector(
            exact=(
                "protection for a work employing preexisting material in which "
                + "copyright subsists does not extend to any part of the work in "
                + "which such material has been used unlawfully."
            )
        ),
        "copyright": TextQuoteSelector(suffix="idea, procedure,"),
        "copyright_requires_originality": TextQuoteSelector(
            suffix="fixed in any tangible"
        ),
    }


@pytest.fixture(scope="module")
def fourth_a():
    return {
        "heading": "AMENDMENT IV.",
        "start_date": "1791-12-15",
        "node": "/us/const/amendment/IV",
        "text_version": {
            "id": 735706,
            "url": "https://authorityspoke.com/api/v1/textversions/735706/",
            "content": "The right of the people to be secure in their persons, houses, papers, and effects, against unreasonable searches and seizures, shall not be violated, and no Warrants shall issue, but upon probable cause, supported by Oath or affirmation, and particularly describing the place to be searched, and the persons or things to be seized.",
        },
        "url": "https://authorityspoke.com/api/v1/us/const/amendment/IV/",
        "end_date": None,
        "children": [],
        "citations": [],
        "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
    }


@pytest.fixture(scope="module")
def fifth_a():
    return {
        "heading": "AMENDMENT V.",
        "content": "No person shall be held to answer for a capital, or otherwise infamous crime, unless on a presentment or indictment of a Grand Jury, except in cases arising in the land or naval forces, or in the Militia, when in actual service in time of War or public danger; nor shall any person be subject for the same offence to be twice put in jeopardy of life or limb; nor shall be compelled in any Criminal Case to be a witness against himself; nor be deprived of life, liberty, or property, without due process of law; nor shall private property be taken for public use, without just compensation.",
        "children": [],
        "end_date": None,
        "node": "/us/const/amendment/V",
        "start_date": "1791-12-15",
        "url": "https://authorityspoke.com/api/v1/us/const/amendment/V/",
        "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
        "selection": True,
    }


@pytest.fixture(scope="module")
def fourteenth_dp():
    return {
        "heading": "Citizenship: security and equal protection of citizens.",
        "content": "All persons born or naturalized in the United States, and subject to the jurisdiction thereof, are citizens of the United States and of the State wherein they reside. No State shall make or enforce any law which shall abridge the privileges or immunities of citizens of the United States; nor shall any State deprive any person of life, liberty, or property, without due process of law; nor deny to any person within its jurisdiction the equal protection of the laws.",
        "children": [],
        "end_date": None,
        "node": "/us/const/amendment/IV",
        "start_date": "1868-07-28",
        "url": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/1/",
        "parent": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/",
        "selection": True,
    }


@pytest.fixture(scope="module")
def provision_with_text_anchor():
    return {
        "node": "/us/usc/t17/s102/a",
        "exact": "Copyright protection subsists, in accordance with this title, in original works of authorship fixed in any tangible medium of expression, now known or later developed, from which they can be perceived, reproduced, or otherwise communicated, either directly or with the aid of a machine or device.",
        "name": "copyright protection provision",
        "anchors": "qualify for copyright protection. |17 U.S.C. § 102(a)|.",
    }

