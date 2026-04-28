
# Common scenarios handled by submission system

Following list covers scenarios experienced by LCSB data stewards. Each contain basic description of the scenario, reasoning and suggested workflow.

## Submission from a service clinicians / less involved parties

The provider is willing to upload the data but **metadata submission is seen as annoying**. Provider is either not researcher or has provided data in-kind. Although agreement was concluded, the provider might not have real motivation to go through lengthy submission process.

Full metadata is not needed or not available:
- data not matching standard data model
- data for preliminary analyses

E.g. partial data are uploaded by a clinician as part of a bigger data collection efforts.

LCSB is supporting the submitter as much as possible
- legal agreement template
- sometimes even running the upload commands from provider's environment

Should a recipient (researcher in receiving organization) act as submitter?
- No. The metadata can be provided by recipient but submitter must login to the system and confirm its correct (accept the accountability).

1. A local researcher contacts data steward. Submission is inititated by the data steward, who will add the details about project, submitter and assignes the researcher as recipient.
2. Datasteward with the help of recipient pre-fills the submission.
3. Submitter will log into the platform and confirms the metadata is correct.
4. DS approves the submission.
5. Data is uploaded by the recipient or submitter (both have access to upload instructions)
6. Recipient verifies the data and metadata is ok
7. Recipient marks the submission as complete

## Legal support involvement - metadata collection and a contract negotiation phase
Contracts are being negotiated and an Annex should describe data being submitted to LCSB. 

### A - metadata is collected before the contract is signed (default)
This is not always possible! Metadata collection can take time while legal framework covering other things has to be signed ASAP.

How many submitters do have access to one submission? Multiple people can edit and contribute (DPO, researcher, legal, domain expert, data manager,...) but these all should be from one institution only, no?
WAYS OUT: 

- excel template for import (back to DISH :D)
- multiple submissions 

Can multiple submissions be linked to become part of one contract?
- probably yes as long as the contract is signed by all submitting institutions

1. DS/Submitter selects a receiving project
2. Submitter fills in metadata
3. Submitter steers the status to Approval
4. DS reviews the metadata
5. **Before the actual approval, DS/Linda can export the metadata and attach it to contract.**
6. **Contract is signed and attached or put into DAISY and linked by DS from submission.**
7. Submission is approved.
6. Submission is moved to Data Upload

### B - Metadata is collected after the contract is signed
Metadata is not known or it takes quite some time to provide.
Contract should use a simplified DISH/table to cover basic description of the data. It can be also used later to prefill the submission during initiation.

1. DS selects a project AND contract covering the submission
2. Submitter fills in metadata
3. DS reviews the metadata and approves
4. Data upload link is generated
(the submission export could be uploaded to Contract entity in DAISY)

## Big data hosting projects with many submissions

Data is to be provided before contract or after (see previous scenarios). **The metadata must be detailed.** Goal is to be able to build data catalog increasing findability and allowing compliant redistribution of data.

1. Postdoc creates submission
2. Select receiving project and contract, putting themselves as recipients
3. Metadata is provided
4. **DS verifies the metadata is complete enough to allow secondary use**
5. DS approves
...

## Internal submission
Data is already present at LCSB and it needs to be "formalized" and enriched by metadata, ingested, validated, ...

1. Submission is created by researcher.
2. Provider institution is LCSB, recipient is also the submitter, receiving project is project of origin.
3. Contract is usually not required as the data is already present at the institution. If covering contract can be recovered, it can be linked.
4. Metadata is prefilled. What about Study? Project of origin? Its the same as receiving project :/ 
5. DS approves metadata
...

## ELIXIR sustainability service
This service operates in similar way as big data hosting projects (see above)

1. Submission is created by DS
2. DS becomes recipient
3. Receiving project is ELIXIR Hosting (child project???), HSA is selected
4. Metadata is provided + attachements
5. DS verifies the metadata is complete enough to allow secondary use
