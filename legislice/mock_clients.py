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
from legislice.enactments import CrossReference

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
            if path.startswith(nested_node["node"])
        ]
        if branches_that_start_path:
            return self.search_tree_for_path(
                path=path, branch=branches_that_start_path[0]
            )
        return None

    def fetch(
        self, query: Union[str, CrossReference], date: Union[datetime.date, str] = ""
    ) -> RawEnactment:
        """
        Fetches data about legislation at specified path and date from Client's assigned API root.

        :param path:
            A path to the desired legislation section using the United States Legislation Markup
            tree-like citation format. Examples: "/us/const/amendment/IV", "/us/usc/t17/s103"

        :param date:
            A date when the desired version of the legislation was in effect. This does not need to
            be the "effective date" or the first date when the version was in effect. However, if
            you select a date when two versions of the provision were in effect at the same time,
            you will be given the version that became effective later.
        """
        responses = self.get_entry_closest_to_cited_path(query)
        if not responses:
            raise LegislicePathError(f"No enacted text found for query {query}")

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
                    f"No enacted text found for query {query} after date {date}"
                )
            selected_date = max(versions_not_later_than_query)

        selected_version = responses[selected_date]

        result = self.search_tree_for_path(path=query, branch=selected_version)
        if not result:
            raise LegislicePathError(
                f"No enacted text found for query {query} after date {date}"
            )
        return result


MOCK_USC_RESPONSES = {
    "/us/const/article/I/8/8": {
        "1788-09-13": {
            "heading": "Patents and copyrights.",
            "content": "To promote the Progress of Science and useful Arts, by securing for limited Times to Authors and Inventors the exclusive Right to their respective Writings and Discoveries;",
            "children": [],
            "end_date": None,
            "node": "/us/const/article/I/8/8",
            "start_date": "1788-09-13",
            "url": "https://authorityspoke.com/api/v1/us/const/article/I/8/8/",
            "parent": "https://authorityspoke.com/api/v1/us/const/article/I/8/",
        }
    },
    "/us/const/amendment/IV": {
        "1791-12-15": {
            "heading": "AMENDMENT IV.",
            "content": "The right of the people to be secure in their persons, houses, papers, and effects, against unreasonable searches and seizures, shall not be violated, and no Warrants shall issue, but upon probable cause, supported by Oath or affirmation, and particularly describing the place to be searched, and the persons or things to be seized.",
            "children": [],
            "end_date": None,
            "node": "/us/const/amendment/IV",
            "start_date": "1791-12-15",
            "url": "https://authorityspoke.com/api/v1/us/const/amendment/IV/",
            "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
        }
    },
    "/us/const/amendment/V": {
        "1791-12-15": {
            "heading": "AMENDMENT V.",
            "content": "No person shall be held to answer for a capital, or otherwise infamous crime, unless on a presentment or indictment of a Grand Jury, except in cases arising in the land or naval forces, or in the Militia, when in actual service in time of War or public danger; nor shall any person be subject for the same offence to be twice put in jeopardy of life or limb; nor shall be compelled in any Criminal Case to be a witness against himself; nor be deprived of life, liberty, or property, without due process of law; nor shall private property be taken for public use, without just compensation.",
            "children": [],
            "end_date": None,
            "node": "/us/const/amendment/V",
            "start_date": "1791-12-15",
            "url": "https://authorityspoke.com/api/v1/us/const/amendment/V/",
            "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
        }
    },
    "/us/const/amendment/XIV": {
        "1868-07-28": {
            "heading": "AMENDMENT XIV.",
            "content": "",
            "children": [
                {
                    "heading": "Citizenship: security and equal protection of citizens.",
                    "content": "All persons born or naturalized in the United States, and subject to the jurisdiction thereof, are citizens of the United States and of the State wherein they reside. No State shall make or enforce any law which shall abridge the privileges or immunities of citizens of the United States; nor shall any State deprive any person of life, liberty, or property, without due process of law; nor deny to any person within its jurisdiction the equal protection of the laws.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/const/amendment/XIV/1",
                    "start_date": "1868-07-28",
                    "url": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/1/",
                },
                {
                    "heading": "Apportionment of representation.",
                    "content": "Representatives shall be apportioned among the several States according to their respective numbers, counting the whole number of persons in each State, excluding Indians not taxed. But when the right to vote at any election for the choice of electors for President and Vice President of the United States, Representatives in Congress, the Executive and Judicial officers of a State, or the members of the Legislature thereof, is denied to any of the male inhabitants of such State, being twenty-one years of age, and citizens of the United States, or in any way abridged, except for participation in rebellion, or other crime, the basis of representation therein shall be reduced in the proportion which the number of such male citizens shall bear to the whole number of male citizens twenty-one years of age in such State.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/const/amendment/XIV/2",
                    "start_date": "1868-07-28",
                    "url": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/2/",
                },
                {
                    "heading": "Loyalty as a qualification of Senators and Representatives.",
                    "content": "No person shall be a Senator or Representative in Congress, or elector of President and Vice President, or hold any office, civil or military, under the United States, or under any State, who, having previously taken an oath, as a member of Congress, or as an officer of the United States, or as a member of any State legislature, or as an executive or judicial officer of any State, to support the Constitution of the United States, shall have engaged in insurrection or rebellion against the same, or given aid or comfort to the enemies thereof. But Congress may by a vote of two-thirds of each House, remove such disability.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/const/amendment/XIV/3",
                    "start_date": "1868-07-28",
                    "url": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/3/",
                },
                {
                    "heading": "Validity of the national debt, etc.",
                    "content": "The validity of the public debt of the United States, authorized by law, including debts incurred for payment of pensions and bounties for services in suppressing insurrection or rebellion, shall not be questioned. But neither the United States nor any State shall assume or pay any debt or obligation incurred in aid of insurrection or rebellion against the United States, or any claim for the loss or emancipation of any slave; but all such debts, obligations and claims shall be held illegal and void.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/const/amendment/XIV/4",
                    "start_date": "1868-07-28",
                    "url": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/4/",
                },
                {
                    "heading": "Enforcement of the 14th amendment.",
                    "content": "The Congress shall have power to enforce, by appropriate legislation, the provisions of this article.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/const/amendment/XIV/5",
                    "start_date": "1868-07-28",
                    "url": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/5/",
                },
            ],
            "end_date": None,
            "node": "/us/const/amendment/XIV",
            "start_date": "1868-07-28",
            "url": "https://authorityspoke.com/api/v1/us/const/amendment/XIV/",
            "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
        }
    },
    "/us/const/amendment/XV": {
        "1870-03-30": {
            "heading": "AMENDMENT XV.",
            "content": "",
            "children": [
                {
                    "heading": "Suffrage not to be abridged for race, color, etc.",
                    "content": "The right of citizens of the United States to vote shall not be denied or abridged by the United States or by any State on account of race, color, or previous condition of servitude.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/const/amendment/XV/1",
                    "start_date": "1870-03-30",
                    "url": "https://authorityspoke.com/api/v1/us/const/amendment/XV/1/",
                },
                {
                    "heading": "Section 2.",
                    "content": "The Congress shall have power to enforce this article by appropriate legislation.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/const/amendment/XV/2",
                    "start_date": "1870-03-30",
                    "url": "https://authorityspoke.com/api/v1/us/const/amendment/XV/2/",
                },
            ],
            "end_date": None,
            "node": "/us/const/amendment/XV",
            "start_date": "1870-03-30",
            "url": "https://authorityspoke.com/api/v1/us/const/amendment/XV/",
            "parent": "https://authorityspoke.com/api/v1/us/const/amendment/",
        }
    },
    "/us/usc/t17/s102/a": {
        "2013-07-18": {
            "heading": "",
            "content": "Copyright protection subsists, in accordance with this title, in original works of authorship fixed in any tangible medium of expression, now known or later developed, from which they can be perceived, reproduced, or otherwise communicated, either directly or with the aid of a machine or device. Works of authorship include the following categories:",
            "children": [
                {
                    "heading": "",
                    "content": "literary works;",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s102/a/1",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/a/1/",
                },
                {
                    "heading": "",
                    "content": "musical works, including any accompanying words;",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s102/a/2",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/a/2/",
                },
                {
                    "heading": "",
                    "content": "dramatic works, including any accompanying music;",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s102/a/3",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/a/3/",
                },
                {
                    "heading": "",
                    "content": "pantomimes and choreographic works;",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s102/a/4",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/a/4/",
                },
                {
                    "heading": "",
                    "content": "pictorial, graphic, and sculptural works;",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s102/a/5",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/a/5/",
                },
                {
                    "heading": "",
                    "content": "motion pictures and other audiovisual works;",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s102/a/6",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/a/6/",
                },
                {
                    "heading": "",
                    "content": "sound recordings; and",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s102/a/7",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/a/7/",
                },
                {
                    "heading": "",
                    "content": "architectural works.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s102/a/8",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/a/8/",
                },
            ],
            "end_date": None,
            "node": "/us/usc/t17/s102/a",
            "start_date": "2013-07-18",
            "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/a/",
            "parent": "https://authorityspoke.com/api/v1/us/usc/t17/s102/",
        }
    },
    "/us/usc/t17/s102/b": {
        "2013-07-18": {
            "heading": "",
            "content": "In no case does copyright protection for an original work of authorship extend to any idea, procedure, process, system, method of operation, concept, principle, or discovery, regardless of the form in which it is described, explained, illustrated, or embodied in such work.",
            "children": [],
            "end_date": None,
            "node": "/us/usc/t17/s102/b",
            "start_date": "2013-07-18",
            "url": "https://authorityspoke.com/api/v1/us/usc/t17/s102/b/",
            "parent": "https://authorityspoke.com/api/v1/us/usc/t17/s102/",
        }
    },
    "/us/usc/t17/s103": {
        "2013-07-18": {
            "heading": "Subject matter of copyright: Compilations and derivative works",
            "content": "",
            "children": [
                {
                    "heading": "",
                    "content": "The subject matter of copyright as specified by section 102 includes compilations and derivative works, but protection for a work employing preexisting material in which copyright subsists does not extend to any part of the work in which such material has been used unlawfully.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s103/a",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s103/a/",
                },
                {
                    "heading": "",
                    "content": "The copyright in a compilation or derivative work extends only to the material contributed by the author of such work, as distinguished from the preexisting material employed in the work, and does not imply any exclusive right in the preexisting material. The copyright in such work is independent of, and does not affect or enlarge the scope, duration, ownership, or subsistence of, any copyright protection in the preexisting material.",
                    "children": [],
                    "end_date": None,
                    "node": "/us/usc/t17/s103/b",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/us/usc/t17/s103/b/",
                },
            ],
            "end_date": None,
            "node": "/us/usc/t17/s103",
            "start_date": "2013-07-18",
            "url": "https://authorityspoke.com/api/v1/us/usc/t17/s103/",
            "parent": "https://authorityspoke.com/api/v1/us/usc/t17/",
        }
    },
    "/us/usc/t17/s410/c": {
        "2013-07-18": {
            "heading": "",
            "content": "In any judicial proceedings the certificate of a registration made before or within five years after first publication of the work shall constitute prima facie evidence of the validity of the copyright and of the facts stated in the certificate. The evidentiary weight to be accorded the certificate of a registration made thereafter shall be within the discretion of the court.",
            "children": [],
            "end_date": None,
            "node": "/us/usc/t17/s410/c",
            "start_date": "2013-07-18",
            "url": "https://authorityspoke.com/api/v1/us/usc/t17/s410/c/",
            "parent": "https://authorityspoke.com/api/v1/us/usc/t17/s410/",
        }
    },
    "/us/cfr/t37/s202.1": {
        "1992-02-21": {
            "node": "/us/cfr/t37/s202.1",
            "heading": "Material not subject to copyright.",
            "content": "The following are examples of works not subject to copyright and applications for registration of such works cannot be entertained:",
            "children": [
                {
                    "node": "/us/cfr/t37/s202.1/a",
                    "start_date": "1992-02-21",
                    "selection": True,
                    "heading": "",
                    "content": "Words and short phrases such as names, titles, and slogans; familiar symbols or designs; mere variations of typographic ornamentation, lettering or coloring; mere listing of ingredients or contents;",
                },
                {
                    "node": "/us/cfr/t37/s202.1/b",
                    "start_date": "1992-02-21",
                    "selection": True,
                    "heading": "",
                    "content": "Ideas, plans, methods, systems, or devices, as distinguished from the particular manner in which they are expressed or described in a writing;  ",
                },
                {
                    "node": "/us/cfr/t37/s202.1/c",
                    "start_date": "1992-02-21",
                    "selection": True,
                    "heading": "",
                    "content": "Blank forms, such as time cards, graph paper, account books, diaries, bank checks, scorecards, address books, report forms, order forms and the like, which are designed for recording information and do not in themselves convey information;",
                },
                {
                    "node": "/us/cfr/t37/s202.1/d",
                    "start_date": "1992-02-21",
                    "selection": True,
                    "heading": "",
                    "content": "Works consisting entirely of information that is common property containing no original authorship, such as, for example: Standard calendars, height and weight charts, tape measures and rulers, schedules of sporting events, and lists or tables taken from public documents or other common sources.",
                },
                {
                    "node": "/us/cfr/t37/s202.1/e",
                    "start_date": "1992-02-21",
                    "selection": True,
                    "heading": "",
                    "content": "Typeface as typeface.",
                },
            ],
            "start_date": "1992-02-21",
            "name": "short phrases copyright exception",
            "suffix": "familiar symbols or designs",
        }
    },
}
MOCK_BEARD_ACT_RESPONSES = {
    "/test/acts/47/1": {
        "1935-04-01": {
            "heading": "Short title",
            "content": "This Act may be cited as the Australian Beard Tax (Promotion of Enlightenment Values) Act 1934.",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/1",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/1/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/2": {
        "1935-04-01": {
            "heading": "Commencement",
            "content": "This Act shall commence on 1 April 1935.",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/2",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/2/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/3": {
        "1935-04-01": {
            "heading": "Purpose",
            "content": "",
            "children": [
                {
                    "heading": "",
                    "content": "This Act is enacted for the purpose of the promotion of enlightenment values.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/3/a",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/3/a/",
                }
            ],
            "end_date": None,
            "node": "/test/acts/47/3",
            "start_date": "2013-07-18",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/3/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/4": {
        "1935-04-01": {
            "heading": "Beard, defined",
            "content": "In this Act, beard means any facial hair no shorter than 5 millimetres in length that:",
            "children": [
                {
                    "heading": "",
                    "content": "occurs on or below the chin, or",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/4/a",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/4/a/",
                },
                {
                    "heading": "",
                    "content": "exists in an uninterrupted line from the front of one ear to the front of the other ear below the nose.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/4/b",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/4/b/",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/4",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/4/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/5": {
        "1935-04-01": {
            "heading": "Prohibition of beards",
            "content": "The wearing of any beard whatsoever, except as provided in section 6, is prohibited within the Commonwealth of Australia.",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/5",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/5/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/6": {
        "1935-04-01": {
            "heading": "Exemption",
            "content": "",
            "children": [
                {
                    "heading": "",
                    "content": "The office of the Department of Beards may, from time to time or as they see fit, grant exemptions to persons from the prohibition contained in section 5.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/6/1",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/6/1/",
                },
                {
                    "heading": "",
                    "content": "Any such exemption granted under subsection 1 is to be for no longer than a period of 12 months.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/6/2",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/6/2/",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/6",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/6/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/6A": {
        "1935-04-01": {
            "heading": "Levy of beard tax",
            "content": "Where the Department provides an exemption from the prohibition in section 5, except as defined in section 6D, the person to whom such exemption is granted shall be liable to pay to the Department of Beards such fee as may be levied under section 6B.",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/6A",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/6A/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/6B": {
        "1935-04-01": {
            "heading": "Regulatory power of the Minister for Beards",
            "content": "The Minister for Beards may, by Order in Council, issue such regulations, including but not limited to levies to be paid by persons exempted under section 6 from the prohibition in section 5, as is necessary for the good governance and financial stability of the Department of Beards.",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/6B",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/6B/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/6C": {
        "2013-07-18": {
            "heading": "Issuance of beardcoin",
            "content": "Where an exemption is granted under section 6, the Department of Beards shall issue to the person so exempted a token, hereinafter referred to as a beardcoin, that shall for all purposes be regarded as substantive proof of such exemption.",
            "children": [
                {
                    "heading": "",
                    "content": "The beardcoin shall be a cryptocurrency token using a blockchain approved by the Department of Beards.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/6C/1",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/6C/1/",
                },
                {
                    "heading": "",
                    "content": "The beardcoin's blockchain shall be in substantially the following form. WHEREAS this beardcoin is approved by the Department of Beards under section 6,\n                     it is secured by the following blockchain: □□□□□□□□□□.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/6C/1-con",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/6C/1-con/",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/6C",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/6C/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/6D": {
        "1935-04-01": {
            "heading": "Waiver of beard tax in special circumstances",
            "content": "",
            "children": [
                {
                    "heading": "",
                    "content": "The Department of Beards shall waive the collection of beard tax upon issuance of beardcoin under Section 6C where the reason the maintainer wears a beard is due to bona fide religious or cultural reasons.",
                    "children": [],
                    "end_date": "2013-07-18",
                    "node": "/test/acts/47/6D/1",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/6D/1@1935-04-01",
                },
                {
                    "heading": "",
                    "content": "The determination of the Department of Beards as to what constitutes bona fide religious or cultural reasons shall be final and no right of appeal shall exist.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/6D/2",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/6D/2@1935-04-01",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/6D",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/6D@1935-04-01",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47@1935-04-01",
        },
        "2013-07-18": {
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
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/6D/1/",
                },
                {
                    "heading": "",
                    "content": "The determination of the Department of Beards as to what constitutes bona fide religious or cultural reasons shall be final and no right of appeal shall exist.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/6D/2",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/6D/2/",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/6D",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/6D/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        },
    },
    "/test/acts/47/7": {
        "1935-04-01": {
            "heading": "Wearing of a beard without exemption",
            "content": "Any person found to be wearing a beard within the Commonwealth of Australia without proper exemption as granted under section 6 commits an offence.",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/7",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/7/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/7A": {
        "1935-04-01": {
            "heading": "Improper transfer of beardcoin",
            "content": "It shall be an offence to buy, sell, lend, lease, gift, transfer or receive in any way a beardcoin from any person or body other than the Department of Beards, except as provided in Part 4.",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/7A",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/7A/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/7B": {
        "1935-04-01": {
            "heading": "Counterfeit beardcoin",
            "content": "",
            "children": [
                {
                    "heading": "",
                    "content": "It shall be an offense to produce, alter, or manufacture tokens with the appearance of and purporting to be genuine beardcoin.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/7B/1",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/7B/1/",
                },
                {
                    "heading": "",
                    "content": "It shall be no defense to a charge under section 7A that the purchase, sale, lease, gift, transfer or receipt was of counterfeit beardcoin rather than genuine beardcoin.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/7B/2",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/7B/2/",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/7B",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/7B/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/8": {
        "1935-04-01": {
            "heading": "Notice to remedy",
            "content": "",
            "children": [
                {
                    "heading": "",
                    "content": "Where an officer of the Department of Beards, Australian Federal Police, state or territorial police, or military police of the Australian Defence Force finds a person to be wearing a beard within the territory of the Commonwealth of Australia, and that person fails or is unable to produce a beardcoin as proof of holding an exemption under section 6, that officer shall in the first instance issue such person a notice to remedy.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/8/1",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/8/1@1935-04-01",
                },
                {
                    "heading": "",
                    "content": "Any such person issued a notice to remedy under subsection 1 must either:",
                    "children": [
                        {
                            "heading": "",
                            "content": "shave in such a way that they are no longer in breach of section 5, or",
                            "children": [],
                            "end_date": None,
                            "node": "/test/acts/47/8/2/a",
                            "start_date": "1935-04-01",
                            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/a@1935-04-01",
                        },
                        {
                            "heading": "",
                            "content": "obtain a beardcoin from the Department of Beards",
                            "children": [],
                            "end_date": "2013-07-18",
                            "node": "/test/acts/47/8/2/b",
                            "start_date": "1935-04-01",
                            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/b@1935-04-01",
                        },
                        {
                            "heading": "",
                            "content": "within 14 days of such notice being issued to them.",
                            "children": [],
                            "end_date": "2013-07-18",
                            "node": "/test/acts/47/8/2/b-con",
                            "start_date": "1935-04-01",
                            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/b-con@1935-04-01",
                        },
                    ],
                    "end_date": None,
                    "node": "/test/acts/47/8/2",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2@1935-04-01",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/8",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/8@1935-04-01",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47@1935-04-01",
        },
        "2013-07-18": {
            "heading": "Notice to remedy",
            "content": "",
            "children": [
                {
                    "heading": "",
                    "content": "Where an officer of the Department of Beards, Australian Federal Police, state or territorial police, or military police of the Australian Defence Force finds a person to be wearing a beard within the territory of the Commonwealth of Australia, and that person fails or is unable to produce a beardcoin as proof of holding an exemption under section 6, that officer shall in the first instance issue such person a notice to remedy.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/8/1",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/8/1/",
                },
                {
                    "heading": "",
                    "content": "Any such person issued a notice to remedy under subsection 1 must either:",
                    "children": [
                        {
                            "heading": "",
                            "content": "shave in such a way that they are no longer in breach of section 5, or",
                            "children": [],
                            "end_date": None,
                            "node": "/test/acts/47/8/2/a",
                            "start_date": "1935-04-01",
                            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/a/",
                        },
                        {
                            "heading": "",
                            "content": "remove the beard with electrolysis, or",
                            "children": [],
                            "end_date": None,
                            "node": "/test/acts/47/8/2/b",
                            "start_date": "2013-07-18",
                            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/b/",
                        },
                        {
                            "heading": "",
                            "content": "",
                            "children": [],
                            "end_date": None,
                            "node": "/test/acts/47/8/2/b-con",
                            "start_date": "2013-07-18",
                            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/b-con/",
                        },
                        {
                            "heading": "",
                            "content": "remove the beard with a laser, or",
                            "children": [],
                            "end_date": None,
                            "node": "/test/acts/47/8/2/c",
                            "start_date": "2013-07-18",
                            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/c/",
                        },
                        {
                            "heading": "",
                            "content": "obtain a beardcoin from the Department of Beards",
                            "children": [],
                            "end_date": None,
                            "node": "/test/acts/47/8/2/d",
                            "start_date": "2013-07-18",
                            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/d/",
                        },
                        {
                            "heading": "",
                            "content": "within 14 days of such notice being issued to them.",
                            "children": [],
                            "end_date": None,
                            "node": "/test/acts/47/8/2/d-con",
                            "start_date": "2013-07-18",
                            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/d-con/",
                        },
                    ],
                    "end_date": None,
                    "node": "/test/acts/47/8/2",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/8/2/",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/8",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/8/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        },
    },
    "/test/acts/47/9": {
        "2013-07-18": {
            "heading": "Penalties",
            "content": "",
            "children": [
                {
                    "heading": "",
                    "content": "Any person summarily convicted of a first offence under section 7 of unlawfully wearing a beard within the Commonwealth of Australia shall be liable to a fine not exceeding $200.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/9/1",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/9/1/",
                },
                {
                    "heading": "",
                    "content": "Any person summarily convicted of a second or subsequent offence under section 7 shall be liable to a fine not exceeding $1000, or a period of imprisonment until such time as they no longer are in breach of section 5.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/9/2",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/9/2/",
                },
                {
                    "heading": "",
                    "content": "No penalty shall be applied to any person who, within 14 days of receiving a notice to remedy under section 8(1), takes the action required of them under section 8(2).",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/9/3",
                    "start_date": "1935-04-01",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/9/3/",
                },
                {
                    "heading": "",
                    "content": "",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/9/3-con",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/9/3-con/",
                },
                {
                    "heading": "",
                    "content": "Any person convicted of an offence under section 7A or section 7B(1) shall be liable to a fine not exceeding $5000 and/or a period of imprisonment not exceeding 12 months.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/9/4",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/9/4/",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/9",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/9/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/10": {
        "1935-04-01": {
            "heading": "Purpose of Part 4.—",
            "content": "Part 4 of the Australian Beard Tax (Promotion of Enlightement Values) Act 1934 exists for the purpose of incentivising Australians, and those visiting Australia, to relieve themselves from the burdensome habit of wearing a beard.",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/10",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/10/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/11": {
        "1935-04-01": {
            "heading": "Licensed repurchasers of beardcoin",
            "content": "The Department of Beards may issue licenses to such barbers, hairdressers or other male grooming professionals as they see fit to purchase a beardcoin from a customer whose beard they have removed, and to resell those beardcoins to the Department of Beards.",
            "children": [],
            "end_date": "2013-07-18",
            "node": "/test/acts/47/11",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/11@1935-04-01",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47@1935-04-01",
        },
        "2013-07-18": {
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
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/11/i/",
                },
                {
                    "heading": "",
                    "content": "hairdressers, or",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/11/ii",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/11/ii/",
                },
                {
                    "heading": "",
                    "content": "other male grooming professionals",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/11/iii",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iii/",
                },
                {
                    "heading": "",
                    "content": "as they see fit to purchase a beardcoin from a customer",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/11/iii-con",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iii-con/",
                },
                {
                    "heading": "",
                    "content": "whose beard they have removed,",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/11/iv",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iv/",
                },
                {
                    "heading": "",
                    "content": "and to resell those beardcoins to the Department of Beards.",
                    "children": [],
                    "end_date": None,
                    "node": "/test/acts/47/11/iv-con",
                    "start_date": "2013-07-18",
                    "url": "https://authorityspoke.com/api/v1/test/acts/47/11/iv-con/",
                },
            ],
            "end_date": None,
            "node": "/test/acts/47/11",
            "start_date": "2013-07-18",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/11/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        },
    },
    "/test/acts/47/12": {
        "1935-04-01": {
            "heading": "Rate to be paid to repurchasers of beardcoin",
            "content": "The value to be transfered to licensed repurchasers of beardcoin under section 11 shall be defined by Order in Council by the Minister for Beards under section 6B on a per coin basis.",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/12",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/12/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        }
    },
    "/test/acts/47/13": {
        "1935-04-01": {
            "heading": "Removal of GST from razors and shavers",
            "content": "The items set out in Annexe 1 of this Act shall be exempt from the goods and sales tax provisions of the Taxation Administration Act 1953.",
            "children": [],
            "end_date": "2013-07-18",
            "node": "/test/acts/47/13",
            "start_date": "1935-04-01",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/13@2000-01-01",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47@2000-01-01",
        },
        "2013-07-18": {
            "heading": "",
            "content": "",
            "children": [],
            "end_date": None,
            "node": "/test/acts/47/13",
            "start_date": "2013-07-18",
            "url": "https://authorityspoke.com/api/v1/test/acts/47/13/",
            "parent": "https://authorityspoke.com/api/v1/test/acts/47/",
        },
    },
}

MOCK_USC_CLIENT = JSONRepository(responses=MOCK_USC_RESPONSES)
MOCK_BEARD_ACT_CLIENT = JSONRepository(responses=MOCK_BEARD_ACT_RESPONSES)
