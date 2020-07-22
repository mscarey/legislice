from typing import Dict

from anchorpoint import TextQuoteSelector
import pytest

from legislice.schemas import Enactment, EnactmentSchema


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
def section_11_subdivided():
    return {
        "heading": "Licensed repurchasers of beardcoin",
        "content": "The Department of Beards may issue licenses to such",
        "children": [
            {
                "heading": "",
                "content": "barbers,",
                "children": [],
                "end_date": None,
                "node": "/test/acts/47/11/i",
                "start_date": "2013-07-18",
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/i@2020-01-01",
            },
            {
                "heading": "",
                "content": "hairdressers, or",
                "children": [],
                "end_date": None,
                "node": "/test/acts/47/11/ii",
                "start_date": "2013-07-18",
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/ii@2020-01-01",
            },
            {
                "heading": "",
                "content": "other male grooming professionals",
                "children": [],
                "end_date": None,
                "node": "/test/acts/47/11/iii",
                "start_date": "2013-07-18",
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iii@2020-01-01",
            },
            {
                "heading": "",
                "content": "as they see fit to purchase a beardcoin from a customer",
                "children": [],
                "end_date": None,
                "node": "/test/acts/47/11/iii-con",
                "start_date": "2013-07-18",
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iii-con@2020-01-01",
            },
            {
                "heading": "",
                "content": "whose beard they have removed,",
                "children": [],
                "end_date": None,
                "node": "/test/acts/47/11/iv",
                "start_date": "2013-07-18",
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iv@2020-01-01",
            },
            {
                "heading": "",
                "content": "and to resell those beardcoins to the Department of Beards.",
                "children": [],
                "end_date": None,
                "node": "/test/acts/47/11/iv-con",
                "start_date": "2013-07-18",
                "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iv-con@2020-01-01",
            },
        ],
        "end_date": None,
        "node": "/test/acts/47/11",
        "start_date": "2013-07-18",
        "url": "https://authorityspoke.com/api/v1/test/acts/47/11@2020-01-01",
        "parent": "https://authorityspoke.com/api/v1/test/acts/47@2020-01-01",
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
        "content": "The right of the people to be secure in their persons, houses, papers, and effects, against unreasonable searches and seizures, shall not be violated, and no Warrants shall issue, but upon probable cause, supported by Oath or affirmation, and particularly describing the place to be searched, and the persons or things to be seized.",
        "children": [],
        "end_date": None,
        "node": "/us/const/amendment/IV",
        "start_date": "1791-12-15",
        "url": "https://authorityspoke.com/api/v1/us/const/amendment/IV/",
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
    }
