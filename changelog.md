Changelog
=========
dev
-----------------
- add CrossReference class as memo of cited Enactment to download
- add CitingProvisionLocation as memo of citing Enactment to download
- add cross_references attr to Enactment model
- add citations_to method to Client class
- add TextVersionSchema
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