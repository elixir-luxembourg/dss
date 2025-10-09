 two primary user roles:

## Global roles
- **Admin**: power user managing user and config
- **Data Steward**: Create and manages submissions, and oversees the entire submission process
- **User**: Can create submissions and become Submitter. Can be also added as recipient.

## Submission context roles
User roles assinged within the scope of the submission.
- **Submitter**:  Submitter is defined in the draft stage by user creating the submission.

If regular user creates a submission, it has to be Submitter. Otherwise, the submission cannot be steered further.


## User Roles and Permissions

```mermaid
graph TB
    subgraph "Global User Roles"
        Admin["👤 Admin"]
        DataSteward
        User
    end

    subgraph "Submission user roles"
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

```mermaid
flowchart TD
    Start([Steward Login]) --> MySubmissions[View All Submissions]
    MySubmissions --> ViewSub[Select Submission]
    ViewSub --> CheckPhase{Submission Phase?}

    CheckPhase --> |MetadataSubmission| MetadataPhase[Complete Metadata]

    MetadataPhase --> EditBasic[Edit Basic Info]
    MetadataPhase --> AddStudy[Add/Edit Studies]
    MetadataPhase --> AddDataDec[Add/Edit Data Declarations]
    MetadataPhase --> AddAttach[Add Attachments\nPDF/TXT/PNG]

    AddStudy --> StudyDetails[Study Details:\n- Name, Description\n- Ethics Approval\n- Study Types\n- Study Contacts]

    AddDataDec --> DataDecDetails[Data Declaration:\n- GDPR Data Types\n- Scientific Data Types\n- De-identification\n- Legal Basis\n- Consent Status\n- Access Restrictions]

    EditBasic --> ReadyMeta{Metadata\nComplete?}
    AddStudy --> ReadyMeta
    AddDataDec --> ReadyMeta
    AddAttach --> ReadyMeta

    ReadyMeta --> |Yes| SteerToUpload[Steer to Data Upload]
    ReadyMeta --> |No| MetadataPhase

    CheckPhase --> |Data Upload| UploadPhase[Data Upload Phase]

    UploadPhase --> AddChecksum[Add Upload Info\nFile Checksums]
    UploadPhase --> ContinueEdit[Continue Editing\nMetadata if Needed]
    UploadPhase --> AddMsg[Add Messages\nCommunicate with Stewards]

    AddChecksum --> ReadyComplete{Data\nUploaded?}
    ContinueEdit --> ReadyComplete
    AddMsg --> ReadyComplete

    ReadyComplete --> |Yes| SteerToComplete[Steer to Completion]
    ReadyComplete --> |No| UploadPhase

    SteerToUpload --> EmailSent1[Email Sent to\nData Stewards]
    SteerToComplete --> EmailSent2[Email Sent to\nData Stewards]

    style Start fill:#4ecdc4
    style MySubmissions fill:#ffd93d
    style EmailSent1 fill:#6bcf7f
    style EmailSent2 fill:#6bcf7f
```

### Sumbmitter Capabilities Summary

**Submission Management:**
- ✅ View own submissions (any state)
- ✅ Edit any submission (Draft / MetadataSubmission only)
- ✅ Delete submissions (Draft state only)
- ✅ Steer submissions forward through states (Draft <-> MetadataSubmission -> Approval only)
- ✅ Revert submissions to previous states (Draft <-> MetadataSubmission)
- ✅ Assign data recipient users to submissions (Draft only)

**Content Management:**
- ✅ Add/edit/delete submission contacts (draft / MetadataSubmission only)
- ✅ Add/edit/delete studies (draft / MetadataSubmission only)
- ✅ Add/edit/delete data declarations (draft / MetadataSubmission only)
- ✅ Add/delete attachments (draft / MetadataSubmission only)
- ✅ Add/edit/delete upload info (draft / MetadataSubmission only)
- ✅ Add messages (anytime)

## Recipient permissions
- ✅ View own submissions (any state)

## Admin permissions

**User Management:**
- ✅ View all users
- ✅ Edit user information
- ✅ Assign/modify user global roles

**System Administration:**
- ✅ View all email notifications
- ✅ Resend notifications manually

```mermaid
  Dashboard --> UserMgmt[User Management]
    UserMgmt --> ListUsers[View All Users]
    ListUsers --> EditUser[Edit User Info/Roles]
```

### DataSteward Capabilities Summary

**Submission Management:**


## Data Steward Workflow

```mermaid
flowchart TD
    Start([User Login]) --> Dashboard[View My Submissions]

    Dashboard --> CreateSub[Create New Submission]
    CreateSub --> Duplicate[Copy Submission]
    CreateSub -- become Submitter --> SetTitle[Set Title & Institution]
    SetTitle --> AssignSubmitter[Assign Data Submitter Users]
    AssignSumitterDetails --> AddContacts[Add Submission Contacts]

    Dashboard --> ManageSub{Manage Existing\nSubmission}

    ManageSub --> ViewAll[View/Edit Any Submission]
    ManageSub --> SteerForward[Steer to Next State]
    ManageSub --> SteerBack[Revert to Previous State]
    ManageSub --> DeleteDraft[Delete Draft Submission]

    SteerForward --> CheckState{Current State?}
    CheckState --> |Draft| NotifySubmitter[Notify Data Submitter\nEmail Sent]
    CheckState --> |Study Reg| NotifySteward1[Notify Data Stewards\nfor Upload Link]
    CheckState --> |Data Upload| NotifySteward2[Notify Data Stewards\nfor Verification]

    Dashboard --> NotifMgmt[Email Notifications]
    NotifMgmt --> ViewNotif[View All Notifications]
    ViewNotif --> ResendNotif[Resend Notification]

    Dashboard --> AddMessage[Add Message to Submission]

    style Start fill:#ff6b6b
    style Dashboard fill:#ffd93d
    style NotifySubmitter fill:#6bcf7f
    style NotifySteward1 fill:#6bcf7f
    style NotifySteward2 fill:#6bcf7f
```
Data steward can do what normal users can do and even become submitter.
On top of that, its reponsible for steering submission from Approval -> Data upload


| Permission / Action                        | Admin | Data Steward | Submitter | Recipient |
|--------------------------------------------|:-----:|:------------:|:---------:|:---------:|
| View all users                             |  ✅   |      ❌      |    ❌     |    ❌     |
| Edit user info/roles                       |  ✅   |      ❌      |    ❌     |    ❌     |
| Assign/modify global roles                 |  ✅   |      ❌      |    ❌     |    ❌     |
| View all submissions                       |  ✅   |      ✅      |    ❌     |    ❌     |
| View assigned submissions                  |  ❌   |      ✅      |    ✅     |    ✅     |
| Create submission                          |  ❌   |      ✅      |    ✅      |   ✅      |
| Edit submission (Draft/MetadataSubmission) |  ❌   |      ✅      |    ✅     |    ❌     |
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

 ✅ Any user can create a submission - become submitter.


## Workflow Rules & Constraints

### State Transition Rules

1. **Draft → MetadataSubmission**
   - ✅ Requires: At least one submitter and one recipient assigned, receiving project selected.
   - ✅ Who can trigger:  Submitter only
   - 📧 Notification: Sent to submitter and recipient

2. **MetadataSubmission → Approval Data Upload**
   - ✅ Requires: Metadata should be complete (recommended, not enforced)
   - ✅ Who can trigger: Submitter
   - 📧 Notification: Sent to data stewards
   - 📅 Records `finalised_on` date

3. **Approval -> Data Upload**
    - Requires: Validation by DataSteward
    - Who can trigger: DataSteward
    - Notification: Sent to submitter
    - Records `metadata_approved_on` date

3. **Data Upload → Completion**
   - ✅ Requires: Data uploaded (verified externally)
   - ✅ Who can trigger: DataSteward or Recipient
   - 📧 Notification: Sent to data stewards

4. **Revert (Any State → Previous State)**
   - ✅ Who can trigger: DataSteward only
   - ❌ Cannot revert from Draft (no previous state)

### Deletion Rules

- ✅ Can delete: Submissions in Draft state only
- ❌ Cannot delete: Any submission that has progressed beyond Draft
- ✅ Who can delete: Submitter or DataSteward

### File Upload Constraints

- **Allowed file types**: PDF, TXT, PNG
- **File size**: Controlled by server configuration
- **Storage**: Files stored in `UPLOAD_FOLDER` with UUID-based folder names
