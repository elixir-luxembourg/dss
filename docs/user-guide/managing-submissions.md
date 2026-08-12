# Managing Submissions

This guide covers the full lifecycle of a submission: creating it, filling in metadata, uploading data, and all the actions available to you along the way.

For a quick reference of which actions are available in each state, see [Submission States](submission-states.md).
For a summary of who can do what, see [Roles](roles.md).

---

## Overview

A submission is the primary unit of work in DSS. It collects:

- **Basic info** — the submitting institution, project, local custodians, and contacts
- **Studies** — one or more studies describing the research
- **Datasets** — one or more datasets linked to studies, with GDPR and scientific metadata
- **Attachments** — supporting files (PDF, TXT, PNG)
- **Messages** — an internal message thread between submitters and Data Stewards

---

## Viewing Submissions

### All submissions (Data Steward)

Data Stewards can see every submission in the system via **Submissions** in the navigation menu (`/submissions`).

### My submissions (Submitter / Recipient)

Regular users see only the submissions they are assigned to, via **My Submissions** (`/my_submissions`).

---

## Creating a Submission

Only **Data Stewards** can create new submissions from scratch.

1. Navigate to **Submissions → New Submission**.
2. Fill in the form:
   - **Institution** — the data provider's institution.
   - **Receiving project** — the internal project receiving the data from this submission.
   - **Recipients** — the internal staff responsible for this data within the receiving project.
   - **Contacts** — at least one contact (the submitter). Additional contacts can be added.
3. Click **Save**. The submission is created in **Initiation** state and a notification is sent to the submitter.

> Any internal user (including submitters) can create a copy of an existing submission — see [Duplicating a Submission](#duplicating-a-submission).

---

## Editing Basic Info

While in **Initiation** or **Metadata Entry** state, the submission's basic info (institution, project, custodians, contacts) can be edited by the Data Steward via the **Edit** button on the submission page.

---

## Adding Studies

Studies are required before the submission can move to Metadata Review. A submission must have at least one study.

1. Open the submission and click **Add Study**.
2. Fill in the study form:
   - Name, acronym, description
   - Study type(s), species, diseases, sample sources
   - Ethics approval details
   - Number of subjects, age range, cohort descriptions
   - Study contacts
3. Save. Repeat to add more studies.

Studies can be edited or deleted while the submission is in **Metadata Entry** state.

---

## Adding Datasets

Each dataset is linked to one of the submission's studies. At least one dataset is required.

1. On the submission page, click **Add Dataset**.
2. Fill in the dataset form:
   - Title and description
   - Scientific data types (e.g. genomics, clinical)
   - GDPR data types (e.g. health, genetic) and whether the data contains personal data
   - Legal basis for collection and sharing
   - Consent status and notes
   - Use restrictions (research scope, geographic, user-specific, publication, etc.)
   - Technical metadata: number of records, file types, data standards, byte size, version
3. Save. Repeat to add more datasets.

Datasets can be edited or deleted while in **Metadata Entry** state. Once the submission moves beyond Metadata Review, datasets become read-only.

---

## Adding Attachments

Supporting documents (PDF, TXT, PNG) can be attached at any point while the submission is in an editable state.

1. On the submission page, click **Add Attachment**.
2. Enter a note describing the attachment.
3. Select one or more files (PDF, TXT, or PNG — other types are rejected).
4. Save.

Attachments can be downloaded by any user with access to the submission, and deleted by the Data Steward or Submitter.

---

## Messaging

Any user with access to a submission can add messages to its internal thread. This is the primary communication channel between submitters and Data Stewards.

1. On the submission page, click **Add Message**.
2. Write your message and save.

When a message is added to an in-progress submission, a notification email is sent to the other parties.

---

## Steering the Submission Forward

Each phase must be explicitly advanced to the next state. This is called "steering".

| From state | Who can steer | Requirements |
|---|---|---|
| Initiation | Data Steward or Submitter | At least one submitter (contact) assigned |
| Metadata Entry | Data Steward or Submitter | At least one study and one dataset present |
| Data Upload | Data Steward or Submitter | Submitter confirms data has been uploaded |

Click the **Steer forward** button on the submission page. Some transitions require confirming a responsibility acknowledgement.

---

## Approving and Rejecting (Data Steward only)

### Metadata Review

After the submission reaches **Metadata Review**, the Data Steward reviews it and either:

- **Approves** — optionally adds a feedback message; submission moves to **Data Upload**.
- **Rejects** — feedback message is required; submission returns to **Metadata Entry**.

### Data Verification

After the submitter confirms data upload, the Data Steward either:

- **Approves** — optionally adds a feedback message; submission moves to **Complete**.
- **Rejects** — feedback message is required; submission returns to **Data Upload**.

---

## Reverting to the Previous State (Data Steward only)

A Data Steward can revert a submission to its previous state at any point (except from **Initiation**, which has no previous state).

Use the **Revert** action on the submission page. Reverting from **Metadata Review** sends the submission back to **Metadata Entry**, and so on.

---

## Cancelling a Submission

Active submissions (in Metadata Entry, Metadata Review, Data Upload, or Data Verification) can be cancelled.

- **Who can cancel:** Data Steward or the submission owner (Submitter).
- **A cancellation reason is required.**

On the submission list page, use the **Cancel** action and enter the reason. The submission moves to **Cancelled** state and a notification is sent to the submitter and recipient. Cancelled submissions cannot be reactivated — create a copy instead.

---

## Deleting a Submission

Submissions can only be deleted while in **Initiation** state (before being steered forward).

- **Who can delete:** Data Steward or Submitter.

Once a submission has been steered past Initiation, use **Cancel** to terminate it instead.

---

## Duplicating a Submission

Any user with access to a submission can create a copy of it via **Create copy** (also called "Clone"). The copy is created in **Initiation** state and includes the basic info, studies, datasets, and contacts from the original. Messages and attachments are not copied.

This is useful when submitting a follow-up study with similar metadata.

---

## Exporting a Submission

A submission can be exported as a **DOCX report** at any stage.

Click **Export DOCX** on the submission page. The file is named `Submission_<ref_name>.docx` and contains all metadata: basic info, contacts, studies, datasets, and use restrictions.

> Export is available to Data Stewards, Submitters, and Recipients.
