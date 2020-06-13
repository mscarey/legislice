import pytest


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
