Changelog
=========
dev
-----------------
- add Citation class
- remove mock Clients and replace them with pytest-vcr cached requests
- add Citation Style Language JSON serializer methods

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
