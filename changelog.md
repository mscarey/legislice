Changelog
=========

0.8.1 (2025-01-25)
------------------
- add py.typed
- bump anchorpoint==0.8.2

0.8.0 (2024-05-18)
------------------
- change CI flag name to record-mode
- limit supported python versions to 3.11 and 3.12

0.7.1 (2023-12-02)
------------------
- support Pydantic 2
- replace pytest-vcr with pytest-recording

0.7.0 (2021-10-21)
------------------
- replace Marshmallow schemas with Pydantic models
- add `types` module for type annotations of TypedDict API responses
- add MANIFEST.in (to include readme.md on Python Package Index)

0.6.0 (2021-09-20)
------------------
- add EnactmentPassage class
- select_from_text_positions_without_nesting doesn't accept RangeSet
- Enactment.limit_selection.start must be an int
- no separate LinkedEnactment class for Enactments with URL links as children
- remove BaseEnactment parent class

0.5.2 (2021-05-20)
------------------
- sort EnactmentGroups by level
- add California to KNOWN_CODES

0.5.1 (2021-05-08)
------------------
- separate schemas for YAML and JSON input
- flag determines if read_from_json uses text expansion
- change InboundReference to dataclass

0.5.0 (2021-03-26)
------------------

- add EnactmentGroup class
- drop Python 3.7 support
- import Citation and Client at top level of library
- Client.fetch_cross_reference no longer will ignore "date" param
- EnactmentGroup init method can accept None as "enactments" param
- remove "text expansion" module and functions
- remove ExpandableSchema class

0.4.1 (2020-12-31)
------------------

- fix bug: Client made API request requiring 301 redirect

0.4.0 (2020-12-29)
------------------

- add Citation class
- add Citation Style Language JSON serializer methods
- remove mock Clients by migrating tests to pytest-vcr

0.3.1 (2020-12-12)
------------------

- order fields in serialized Enactment JSON output format for readability
- remove include_start and include_end from serialized Enactment JSON output
- fix bug: Enactment.select_all created zero length selectors

0.3.0 (2020-11-17)
------------------

- add CrossReference class as memo of cited Enactment to download
- add CitingProvisionLocation as memo of citing Enactment to download
- add cross_references attr to Enactment model
- add citations_to method to Client class
- EnactmentSchema's content field is moved to a new nested model called TextVersionSchema
- add ability to pass CitingProvisionLocation to Client.read
- add ability to pass InboundReference to Client.read

0.2.0 (2020-08-30)
------------------
- don't add ellipsis to selected_text for node with no text
- accept list of strings to generate anchorpoint TextPositionSet
- combine selected text passages within 3 characters of each other

0.1.1 (2020-08-23)
------------------
- initial release
