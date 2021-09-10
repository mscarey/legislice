import datetime
import os
from typing import Dict

from anchorpoint import TextQuoteSelector
from dotenv import load_dotenv
import pytest

from legislice.download import Client

load_dotenv()

API_ROOT = "https://authorityspoke.com/api/v1"
TOKEN = os.getenv("LEGISLICE_API_TOKEN")


@pytest.fixture(scope="module")
def vcr_config():
    return {
        # Replace the Authorization request header with "DUMMY" in cassettes
        "filter_headers": [("authorization", "DUMMY")],
    }


@pytest.fixture(scope="class")
def test_client() -> Client:
    client = Client(api_token=TOKEN)
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
                "url": "http://127.0.0.1:8000/api/v1/test/acts/47/6D/1@2018-03-11/",
            },
            {
                "heading": "",
                "content": "The determination of the Department of Beards as to what constitutes bona fide religious or cultural reasons shall be final and no right of appeal shall exist.",
                "children": [],
                "end_date": None,
                "node": "/test/acts/47/6D/2",
                "start_date": "1935-04-01",
                "url": "http://127.0.0.1:8000/api/v1/test/acts/47/6D/2@2018-03-11/",
            },
        ],
        "end_date": None,
        "node": "/test/acts/47/6D",
        "start_date": "1935-04-01",
        "url": "http://127.0.0.1:8000/api/v1/test/acts/47/6D@2018-03-11/",
        "parent": "http://127.0.0.1:8000/api/v1/test/acts/47@2018-03-11/",
    }


@pytest.fixture()
def section_8():
    return {
        "heading": "Notice to remedy",
        "start_date": "1935-04-01",
        "node": "/test/acts/47/8",
        "text_version": None,
        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/",
        "end_date": None,
        "children": [
            {
                "heading": "",
                "start_date": "1935-04-01",
                "node": "/test/acts/47/8/1",
                "text_version": {
                    "id": 1142679,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142679/",
                    "content": "Where an officer of the Department of Beards, Australian Federal Police, state or territorial police, or military police of the Australian Defence Force finds a person to be wearing a beard within the territory of the Commonwealth of Australia, and that person fails or is unable to produce a beardcoin as proof of holding an exemption under section 6, that officer shall in the first instance issue such person a notice to remedy.",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/8/1/",
                "end_date": None,
                "children": [],
                "citations": [
                    {
                        "target_uri": "/test/acts/47/6",
                        "target_url": "https://authorityspoke.com/api/v1/test/acts/47/6/",
                        "target_node": 1386965,
                        "reference_text": "section 6",
                    }
                ],
            },
            {
                "heading": "",
                "start_date": "1935-04-01",
                "node": "/test/acts/47/8/2",
                "text_version": {
                    "id": 1142683,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142683/",
                    "content": "Any such person issued a notice to remedy under subsection 1 must either:",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/",
                "end_date": None,
                "children": [
                    {
                        "heading": "",
                        "start_date": "1935-04-01",
                        "node": "/test/acts/47/8/2/a",
                        "text_version": {
                            "id": 1142680,
                            "url": "https://authorityspoke.com/api/v1/textversions/1142680/",
                            "content": "shave in such a way that they are no longer in breach of section 5, or",
                        },
                        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/a/",
                        "end_date": None,
                        "children": [],
                        "citations": [
                            {
                                "target_uri": "/test/acts/47/5",
                                "target_url": "https://authorityspoke.com/api/v1/test/acts/47/5/",
                                "target_node": 1386964,
                                "reference_text": "section 5",
                            }
                        ],
                    },
                    {
                        "heading": "",
                        "start_date": "2013-07-18",
                        "node": "/test/acts/47/8/2/b",
                        "text_version": {
                            "id": 1142702,
                            "url": "https://authorityspoke.com/api/v1/textversions/1142702/",
                            "content": "remove the beard with electrolysis, or",
                        },
                        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/b/",
                        "end_date": None,
                        "children": [],
                        "citations": [],
                    },
                    {
                        "heading": "",
                        "start_date": "2013-07-18",
                        "node": "/test/acts/47/8/2/b-con",
                        "text_version": None,
                        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/b-con/",
                        "end_date": None,
                        "children": [],
                        "citations": [],
                    },
                    {
                        "heading": "",
                        "start_date": "2013-07-18",
                        "node": "/test/acts/47/8/2/c",
                        "text_version": {
                            "id": 1142703,
                            "url": "https://authorityspoke.com/api/v1/textversions/1142703/",
                            "content": "remove the beard with a laser, or",
                        },
                        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/c/",
                        "end_date": None,
                        "children": [],
                        "citations": [],
                    },
                    {
                        "heading": "",
                        "start_date": "2013-07-18",
                        "node": "/test/acts/47/8/2/d",
                        "text_version": {
                            "id": 1142681,
                            "url": "https://authorityspoke.com/api/v1/textversions/1142681/",
                            "content": "obtain a beardcoin from the Department of Beards",
                        },
                        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/d/",
                        "end_date": None,
                        "children": [],
                        "citations": [],
                    },
                    {
                        "heading": "",
                        "start_date": "2013-07-18",
                        "node": "/test/acts/47/8/2/d-con",
                        "text_version": {
                            "id": 1142682,
                            "url": "https://authorityspoke.com/api/v1/textversions/1142682/",
                            "content": "within 14 days of such notice being issued to them.",
                        },
                        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/d-con/",
                        "end_date": None,
                        "children": [],
                        "citations": [],
                    },
                ],
                "citations": [
                    {
                        "target_uri": "/test/acts/47/8/1",
                        "target_url": "https://authorityspoke.com/api/v1/test/acts/47/8/1/",
                        "target_node": 1386980,
                        "reference_text": "subsection 1",
                    }
                ],
            },
        ],
        "citations": [],
        "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
    }


@pytest.fixture()
def old_section_8():
    return {
        "heading": "Notice to remedy",
        "start_date": "1935-04-01",
        "node": "/test/acts/47/8",
        "text_version": None,
        "url": "https://authorityspoke.com/api/v1/test/acts/47/8@1935-04-01",
        "end_date": None,
        "children": [
            {
                "heading": "",
                "start_date": "1935-04-01",
                "node": "/test/acts/47/8/1",
                "text_version": {
                    "id": 1142679,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142679/",
                    "content": "Where an officer of the Department of Beards, Australian Federal Police, state or territorial police, or military police of the Australian Defence Force finds a person to be wearing a beard within the territory of the Commonwealth of Australia, and that person fails or is unable to produce a beardcoin as proof of holding an exemption under section 6, that officer shall in the first instance issue such person a notice to remedy.",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/8/1@1935-04-01",
                "end_date": None,
                "children": [],
                "citations": [
                    {
                        "target_uri": "/test/acts/47/6",
                        "target_url": "https://authorityspoke.com/api/v1/test/acts/47/6@1935-04-01",
                        "target_node": 1386965,
                        "reference_text": "section 6",
                    }
                ],
            },
            {
                "heading": "",
                "start_date": "1935-04-01",
                "node": "/test/acts/47/8/2",
                "text_version": {
                    "id": 1142683,
                    "url": "https://authorityspoke.com/api/v1/textversions/1142683/",
                    "content": "Any such person issued a notice to remedy under subsection 1 must either:",
                },
                "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2@1935-04-01",
                "end_date": None,
                "children": [
                    {
                        "heading": "",
                        "start_date": "1935-04-01",
                        "node": "/test/acts/47/8/2/a",
                        "text_version": {
                            "id": 1142680,
                            "url": "https://authorityspoke.com/api/v1/textversions/1142680/",
                            "content": "shave in such a way that they are no longer in breach of section 5, or",
                        },
                        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/a@1935-04-01",
                        "end_date": None,
                        "children": [],
                        "citations": [
                            {
                                "target_uri": "/test/acts/47/5",
                                "target_url": "https://authorityspoke.com/api/v1/test/acts/47/5@1935-04-01",
                                "target_node": 1386964,
                                "reference_text": "section 5",
                            }
                        ],
                    },
                    {
                        "heading": "",
                        "start_date": "1935-04-01",
                        "node": "/test/acts/47/8/2/b",
                        "text_version": {
                            "id": 1142681,
                            "url": "https://authorityspoke.com/api/v1/textversions/1142681/",
                            "content": "obtain a beardcoin from the Department of Beards",
                        },
                        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/b@1935-04-01",
                        "end_date": "2013-07-18",
                        "children": [],
                        "citations": [],
                    },
                    {
                        "heading": "",
                        "start_date": "1935-04-01",
                        "node": "/test/acts/47/8/2/b-con",
                        "text_version": {
                            "id": 1142682,
                            "url": "https://authorityspoke.com/api/v1/textversions/1142682/",
                            "content": "within 14 days of such notice being issued to them.",
                        },
                        "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/b-con@1935-04-01",
                        "end_date": "2013-07-18",
                        "children": [],
                        "citations": [],
                    },
                ],
                "citations": [
                    {
                        "target_uri": "/test/acts/47/8/1",
                        "target_url": "https://authorityspoke.com/api/v1/test/acts/47/8/1@1935-04-01",
                        "target_node": 1386980,
                        "reference_text": "subsection 1",
                    }
                ],
            },
        ],
        "citations": [],
        "parent": "https://authorityspoke.com/api/v1/test/acts/47@1935-04-01",
    }


@pytest.fixture(scope="class")
def section_11_together():
    return {
        "heading": "Licensed repurchasers of beardcoin",
        "text_version": {
            "id": 1142710,
            "url": "https://authorityspoke.com/api/v1/textversions/1142710/",
            "content": "The Department of Beards may issue licenses to such barbers, hairdressers, or other male grooming professionals as they see fit to purchase a beardcoin from a customer whose beard they have removed, and to resell those beardcoins to the Department of Beards.",
        },
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


@pytest.fixture(scope="class")
def first_a(test_client):
    return test_client.read_from_json(
        {
            "heading": "AMENDMENT I.",
            "start_date": "1791-12-15",
            "node": "/us/const/amendment/I",
            "text_version": {
                "id": 735703,
                "url": "https://authorityspoke.com/api/v1/textversions/735703/",
                "content": "Congress shall make no law respecting an establishment of religion, or prohibiting the free exercise thereof; or abridging the freedom of speech, or of the press; or the right of the people peaceably to assemble, and to petition the Government for a redress of grievances.",
            },
            "url": "https://authorityspoke.com/api/v1/us/const/amendment/I/",
            "end_date": None,
            "children": [],
            "citations": [],
            "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
        }
    )


@pytest.fixture(scope="class")
def second_a(test_client):
    return test_client.read_from_json(
        {
            "heading": "AMENDMENT II.",
            "start_date": "1791-12-15",
            "node": "/us/const/amendment/II",
            "text_version": {
                "id": 735704,
                "url": "https://authorityspoke.com/api/v1/textversions/735704/",
                "content": "A well regulated Militia being necessary to the security of a free State, the right of the people to keep and bear arms, shall not be infringed.",
            },
            "url": "https://authorityspoke.com/api/v1/us/const/amendment/II/",
            "end_date": None,
            "children": [],
            "citations": [],
            "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
        }
    )


@pytest.fixture(scope="class")
def third_a(test_client):
    return test_client.read_from_json(
        {
            "heading": "AMENDMENT III.",
            "start_date": "1791-12-15",
            "node": "/us/const/amendment/III",
            "text_version": {
                "id": 735705,
                "url": "https://authorityspoke.com/api/v1/textversions/735705/",
                "content": "No soldier shall, in time of peace be quartered in any house, without the consent of the Owner, nor in time of war, but in a manner to be prescribed by law.",
            },
            "url": "https://authorityspoke.com/api/v1/us/const/amendment/III/",
            "end_date": None,
            "children": [],
            "citations": [],
            "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
        }
    )


@pytest.fixture(scope="class")
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
def fourth_a_no_text_version():
    return {
        "heading": "AMENDMENT IV.",
        "start_date": "1791-12-15",
        "node": "/us/const/amendment/IV",
        "content": "The right of the people to be secure in their persons, houses, papers, and effects, against unreasonable searches and seizures, shall not be violated, and no Warrants shall issue, but upon probable cause, supported by Oath or affirmation, and particularly describing the place to be searched, and the persons or things to be seized.",
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
        "start_date": "1791-12-15",
        "node": "/us/const/amendment/V",
        "text_version": {
            "id": 735707,
            "url": "https://authorityspoke.com/api/v1/textversions/735707/",
            "content": "No person shall be held to answer for a capital, or otherwise infamous crime, unless on a presentment or indictment of a Grand Jury, except in cases arising in the land or naval forces, or in the Militia, when in actual service in time of War or public danger; nor shall any person be subject for the same offence to be twice put in jeopardy of life or limb; nor shall be compelled in any Criminal Case to be a witness against himself; nor be deprived of life, liberty, or property, without due process of law; nor shall private property be taken for public use, without just compensation.",
        },
        "url": "https://authorityspoke.com/api/v1/us/const/amendment/V/",
        "end_date": None,
        "children": [],
        "citations": [],
        "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
    }


@pytest.fixture(scope="module")
def fourteenth_dp():
    return {
        "heading": "Citizenship: security and equal protection of citizens.",
        "start_date": "1868-07-28",
        "node": "/us/const/amendment/XIV/1",
        "text_version": {
            "id": 735717,
            "url": "https://authorityspoke.com/api/v1/textversions/735717/",
            "content": "All persons born or naturalized in the United States, and subject to the jurisdiction thereof, are citizens of the United States and of the State wherein they reside. No State shall make or enforce any law which shall abridge the privileges or immunities of citizens of the United States; nor shall any State deprive any person of life, liberty, or property, without due process of law; nor deny to any person within its jurisdiction the equal protection of the laws.",
        },
        "url": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/1/",
        "end_date": None,
        "children": [],
        "citations": [],
        "parent": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/",
    }


@pytest.fixture(scope="module")
def provision_with_text_anchor():
    return {
        "passage": {
            "enactment": {
                "node": "/us/usc/t17/s102/a",
                "name": "copyright protection provision",
            },
            "selection": {
                "quotes": {
                    "exact": "Copyright protection subsists, in accordance with this title, in original works of authorship fixed in any tangible medium of expression, now known or later developed, from which they can be perceived, reproduced, or otherwise communicated, either directly or with the aid of a machine or device."
                }
            },
        },
        "anchors": {
            "quotes": "qualify for copyright protection. |17 U.S.C. § 102(a)|."
        },
    }


@pytest.fixture(scope="class")
def copyright_clause(test_client):
    return test_client.read_from_json(
        {
            "heading": "Patents and copyrights.",
            "start_date": "1788-09-13",
            "node": "/us/const/article/I/8/8",
            "text_version": {
                "id": 735650,
                "url": "https://authorityspoke.com/api/v1/textversions/735650/",
                "content": "To promote the Progress of Science and useful Arts, by securing for limited Times to Authors and Inventors the exclusive Right to their respective Writings and Discoveries;",
            },
            "url": "https://authorityspoke.com/api/v1/us/const/article/I/8/8/",
            "end_date": None,
            "children": [],
            "citations": [],
            "parent": "https://authorityspoke.com/api/v1/us/const/article/I/8/",
        }
    )


@pytest.fixture(scope="class")
def copyright_statute(test_client):
    return test_client.read_from_json(
        {
            "heading": "",
            "start_date": "2013-07-18",
            "node": "/us/usc/t17/s102/b",
            "text_version": {
                "id": 1030580,
                "url": "https://authorityspoke.com/api/v1/textversions/1030580/",
                "content": "In no case does copyright protection for an original work of authorship extend to any idea, procedure, process, system, method of operation, concept, principle, or discovery, regardless of the form in which it is described, explained, illustrated, or embodied in such work.",
            },
            "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/b/",
            "end_date": None,
            "children": [],
            "citations": [],
            "parent": "https://authorityspoke.com/api/v1/us/usc/t17/s102/",
        }
    )
