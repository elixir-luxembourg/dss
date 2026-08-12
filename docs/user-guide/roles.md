There are two primary groups of roles in the system based on the context in which they are defined.

## Global roles

- **Admin**: power user managing user and config
- **Data Steward**: Create and manages submissions, and oversees the entire submission process
- **User**: Can create submissions and become Submitter. Can be also added as recipient.

## Submission roles
User roles assigned within the scope of the submission.

- **Submitter**: Submitter is defined in the draft stage by user creating the submission.
- **Recipient**: Person receiving data on our side. It can be same user as submitter. The recipient must be defined as project member.

If regular user creates a submission, they get submitter role.

---

## Submitter Workflow

Submitter is defined in scope of a submission so the workflow starts after the Initiation phase.

The submitter's responsibilities are:

- Fill in metadata (studies, datasets, contacts, attachments) during **Metadata Entry**
- Steer the submission to **Metadata Review** once metadata is complete
- Upload data to the landing zone during **Data Upload**
- Confirm that data upload is complete to trigger **Data Verification**

See [Managing Submissions](managing-submissions.md) for a step-by-step walkthrough, and [Submission States](submission-states.md) for the full state diagram.

## Data Steward Workflow

The Data Steward initiates submissions, reviews metadata and uploaded data, and controls all lifecycle transitions. They have full visibility over all submissions in the system.

See [Submission States](submission-states.md) for the full state diagram and transition rules.

## Recipient workflow

Recipient is assinged to a submission with receiving project. They get notifications about the progress, can read all submission metadata and download the attachments.

Downstream ingestion pipeline (not part of the submission system) can use this information to inform user about failed ingestions or assign the recipient a dataset specific role (e.g. dataset custodian).

## Permissions

 ✅ Any internal user can create a submission and also become submitter.


| Permission / Action                        | Admin | Data Steward | Submitter | Recipient |
|--------------------------------------------|:-----:|:------------:|:---------:|:---------:|
| View all users                             |  ✅   |      ❌      |    ❌     |    ❌     |
| Edit user info/roles                       |  ✅   |      ❌      |    ❌     |    ❌     |
| Assign/modify global roles                 |  ✅   |      ❌      |    ❌     |    ❌     |
| View all submissions                       |  ✅   |      ✅      |    ❌     |    ❌     |
| View assigned submissions                  |  ❌   |      ✅      |    ✅     |    ✅     |
| Create submission (including "Create copy")|  ❌   |      ✅      |    ✅      |   ❌     |
| Edit submission (Draft/MetadataSubmission) |  ❌   |      ✅      |    ✅     |    ❌     |
| Export submission as PDF / JSON            | ❌    |      ✅      |    ✅.    |    ✅.    |
| Download attachments                       |  ❌   |      ✅      |    ✅     |    ✅     |
| Delete submission (Draft only)             |  ❌   |      ✅      |    ✅     |    ❌     |
| Steer submission forward                   |  ❌   |      ✅      |   from Draft and MetadataSubmission     |    ❌     |
| Revert submission to previous state        |  ❌   |      ✅      |    ❌     |    ❌     |
| Assign recipient to submission.            |  ❌   |      ✅      |    ✅     |    ❌     |
| Add/edit/delete metadata                   |  ❌   |      Draft, MetadataSubmission      |   Draft,MetadataSubmission     |    ❌     |
| Add/delete attachments                     |  ❌   |      ✅      |    Draft,MetadataSubmission     |    ❌     |
| Add/edit/delete upload info                |  ❌   |      Data Upload      |    Data Upload     |    ❌     |
| Add messages                               |  ❌   |      ✅      |    ✅     |    ❌     |
| View notifications                         |  ✅   |      ✅      |    ❌     |    ❌     |
| Resend notifications                       |  ✅   |      ✅      |    ❌     |    ❌     |
