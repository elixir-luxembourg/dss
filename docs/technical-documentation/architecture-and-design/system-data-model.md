## Data Model Key Entities

### Contact

### Recipient

### Receiving project

### Submitter

### Submission
- `ref_name`: Unique identifier (e.g., ELX_LU_SUB-1)
- `title`: Submission title
- `current_status`: Draft, Study Registration, Data Upload, or Completion
- `institution_accession`: Institution identifier
- `created_on`: Creation date
- `finalised_on`: Date moved to Data Upload phase

### Study (SubmissionStudy)
- Study name, description, website
- Ethics approval details
- Study types/features (JSON)
- Study contacts

This can refer to the originating experiment or cohort or publication.


### Dataset (SubmissionDataset)
- GDPR data types (JSON)
- Scientific data types (JSON)
- De-identification type
- Legal basis for collection/sharing
- Subject category
- Consent status
- Access restrictions
- Samples information

### Attachment (SubmissionAttachment)
- Uploaded files (PDF, TXT, PNG)
- Notes/descriptions
- Files stay in the system (or they are stored in DAISY?)

### Landing zone
- URL
- password

### Message (SubmissionMessage)
- Communication between admins and data providers
- Sender user
- Message text
- Creation date


#TODO: 
Harmonize the metadata with downstream systems (DAISY, DATS, DC, DCAT, ...)
Include basic metadata from Dublin Core, etc. - how come we do not have "authors" field!??
