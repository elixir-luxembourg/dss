There are two primary groups of roles in the system based on the context in which they are defined.

## Global roles
- **Admin**: power user managing user and config
- **Data Steward**: Create and manages submissions, and oversees the entire submission process
- **User**: Can create submissions and become Submitter. Can be also added as recipient.

## Submission roles
User roles assinged within the scope of the submission.
- **Submitter**:  Submitter is defined in the draft stage by user creating the submission.
- **Recipient**: Person recieving data on our side. It can be same user as submitter. The recipient must be defined as project member.

If regular user creates a submission, they get submitter role.


## User Roles and Permissions

```mermaid
graph TB
    subgraph "Global User Roles"
        Admin["👤 Admin"]
        DataSteward
    end

    subgraph "Submission User Roles"
        Submitter
        Recipient
    end


    subgraph "Permissions"
        Admin --> | Manage | Users[User Management]
        DataSteward --> |Full Access| AllSubmissions[All Submissions]
        DataSteward --> |Control| Lifecycle[Submission Lifecycle]
        DataSteward --> |View| Notifications[Email Notifications]

        User --> | Add | CreateSubmission 

        Submitter --> |Limited Access| AssignedSubmissions
        Submitter --> |Edit| Metadata[Metadata & Data]
        Submitter --> |Add| Messages[Messages]

        Recipient --> |Limited Access| AssignedSubmissions
        Recipient --> |Add| Messages[Messages]
    end

    style DataSteward fill:#ff6b6b
    style Submitter fill:#4ecdc4
```


## Submitter Workflow

Submitter is define in scope of a submission so the workflow starts after Draft phase.


```mermaid
flowchart TD
    Start([Login]) --> MySubmissions[View My Submissions]
    MySubmissions --> ViewSub[Select Submission]
    MySubmissions --> IsInternalUser
    CreateSubOrDuplicate --> CheckPhase
    ViewSub --> CheckPhase

    IsInternalUser --> |Yes| CreateSubOrDuplicate[Create or duplicate submission]
    ViewSub --> IsInternalUser

    CheckPhase --> |Draft| Draft[Initiate submission]
    Draft --> SelectProject
    Draft --> SelectRecipient
    Draft --> AssingSubmitter

    CheckPhase --> |MetadataSubmission| MetadataPhase[Complete Metadata]


    MetadataPhase --> EditBasic[Edit Basic Info]
    MetadataPhase --> AddStudy[Add/Edit Studies]
    MetadataPhase --> AddData[Add/Edit Data]
    MetadataPhase --> AddAttach[Add Attachments\nPDF/TXT/PNG]

    AddData --> ReadyMeta

    EditBasic --> ReadyMeta{Metadata Complete?}
    AddStudy --> ReadyMeta
    AddDataDec --> ReadyMeta
    AddAttach --> ReadyMeta

    ReadyMeta --> |Yes| SteerToApproval[Steer to Approval]
    ReadyMeta --> |No| MetadataPhase

    CheckPhase --> |Data Upload| UploadPhase[Data Upload Phase]

    UploadPhase --> GetUploadLink[Get link to upload data]
    UploadPhase --> AddMsg[Add Messages\nCommunicate with Stewards]
    GetUploadLink --> ConfirmDataUploadOver
    UploadPhase --> ConfirmDataUploadOver[Confirm that data was uploaded to landing zone]
    ConfirmDataUploadOver --> ReadyComplete[All data uploaded?]
    AddMsg --> ReadyComplete

    ReadyComplete --> |Yes| SteerToComplete[Steer to Completion]
    ReadyComplete --> |No| UploadPhase

    style Start fill:#4ecdc4
    style MySubmissions fill:#ffd93d
```

## Data Steward Workflow

Data steward either initiates submission or/and approves all submissions before dataUpload phase

Data steward can do what normal users can do and even become submitter.
On top of that, its reponsible for steering submission from Approval -> Data upload

## Permissions

 ✅ Any internal user can create a submission and also become submitter.


| Permission / Action                        | Admin | Data Steward | Submitter | Recipient |
|--------------------------------------------|:-----:|:------------:|:---------:|:---------:|
| View all users                             |  ✅   |      ❌      |    ❌     |    ❌     |
| Edit user info/roles                       |  ✅   |      ❌      |    ❌     |    ❌     |
| Assign/modify global roles                 |  ✅   |      ❌      |    ❌     |    ❌     |
| View all submissions                       |  ✅   |      ✅      |    ❌     |    ❌     |
| View assigned submissions                  |  ❌   |      ✅      |    ✅     |    ✅     |
| Create submission (including "Create copy")|  ❌   |      ✅      |    ✅      |   ✅     |
| Edit submission (Draft/MetadataSubmission) |  ❌   |      ✅      |    ✅     |    ❌     |
| Export submission as PDF / JSON            | ❌    |      ✅      |    ✅.    |    ✅.    |
| Delete submission (Draft only)             |  ❌   |      ✅      |    ✅     |    ❌     |
| Steer submission forward                   |  ❌   |      ✅      |   from Draft and MetadataSubmission     |    ❌     |
| Revert submission to previous state        |  ❌   |      ✅      |    ❌     |    ❌     |
| Assign recipient to submission.            |  ❌   |      ✅      |    ✅     |    ❌     |
| Add/edit/delete metadata                   |  ❌   |      Draft, MetadataSubmission      |   Draft,MetadataSubmission     |    ❌     |
| Add/delete attachments                     |  ❌   |      ✅      |    Draft,MetadataSubmission     |    ❌     |
| Add/edit/delete upload info                |  ❌   |      Data Upload      |    Data Upload     |    ❌     |
| Add messages                               |  ❌   |      ✅      |    ✅     |    ✅     |
| View notifications                         |  ✅   |      ✅      |    ❌     |    ❌     |
| Resend notifications                       |  ✅   |      ✅      |    ❌     |    ❌     |
