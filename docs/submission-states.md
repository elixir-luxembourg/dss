
## Submission Lifecycle

### State Flow Diagram

```mermaid
stateDiagram-v2
    [*] --> Draft: User creates submission (Owner)
    Draft --> X: Delete
    Draft --> MetadataSubmission: Steer Forward\n(requires Submitter)
    MetadataSubmission --> Draft: Owner Revert

    MetadataSubmission --> Approval: Steer Forward\n(metadata complete)
    Approval --> DataUpload: DataSteward approves
    
    Approval --> MetadataSubmission: DataSteward Revert

    DataUpload --> Completion: Steer Forward\n(data uploaded)
    Completion --> DataUpload: DataSteward Revert

    MetadataSubmission --> Cancelled
    DataUpload --> Cancelled
    Approval --> Cancelled

    note right of Draft
        Only deletable state
        DataSteward only
    end note

    note right of MetadataSubmission
        Submitter completes:
        - Studies, Data, Attachments
    end note

    note right of Approval
        DataSteward:
        - Verifies all metadata is ok
    end note

    note right of DataUpload
        Submitter:
        - Uploads data to landing zone
    end note

    note right of Completion
        Data StewarDataSteward verify
        Final state
    end note
```


### State Details

| State                  | Label                | Description                       | Visible To                                 | Editable metadata         |
|------------------------|---------------------|-----------------------------------|--------------------------------------------|--------------------------|
| `draft`                | Draft               | Initial state, submission setup   | Data Steward, Submitter (owner)            | Data Steward, Submitter (owner)        |
| `MetadataSubmission` | MetadataSubmission  | Metadata collection phase         | Data Steward, Submitter, Recipient         | Data Steward, Submitter  |
| `Approval` | Approval            | Approval of metadata              | Data Steward, Submitter, Recipient         | Data Steward             |
| `DataUpload`     | Data Upload         | Data upload phase                 | Data Steward, Submitter, Recipient         | Submitter (only upload status)  |
| `Completion`            | Completion          | Final verification phase          | Data Steward, Submitter, Recipient         | No                       |
| `Cancelled` | Cancelled | Final phase when things go wrong | Visible to Data Steward, Submitter, Recipient | No |


## Workflow Rules & Constraints

### State Transition Rules

1. **Draft → MetadataSubmission**
   - ✅ Requires: At least one submitter and one recipient assigned, receiving project selected.
   - ✅ Who can trigger:  Submitter only
   - 📧 Notification: Sent to submitter and recipient

2. **MetadataSubmission → Approval**
   - ✅ Requires: Metadata should be complete (recommended, not enforced)
   - ✅ Who can trigger: Submitter
   - 📧 Notification: Sent to data stewards
   - 📅 Records `finalised_on` date

3. **Approval -> DataUpload**
    - Requires: Validation by DataSteward
    - Who can trigger: DataSteward
    - Notification: Sent to submitter
    - Records `metadata_approved_on` date

3. **Data Upload → Completion**
   - ✅ Requires: Data uploaded (verified externally)
   - ✅ Who can trigger: DataSteward or Recipient
   - 📧 Notification: Sent to data stewards

3. **Any phase -> Cancelled**
   - Requires: Cancellation message
   - Who can trigger: DataSteward
   - Notification: Submitter, Recipient
   
4. **Revert (Any State → Previous State)**
   - ✅ Who can trigger: DataSteward only
   - ❌ Cannot revert from Draft (no previous state)

### Deletion Rules

- ✅ Can delete: Submissions in Draft state only
- ❌ Cannot delete: Any submission that has progressed beyond Draft
- ✅ Who can delete: Submitter or DataSteward
