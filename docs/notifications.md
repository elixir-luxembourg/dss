## Email Notifications

The system automatically sends email notifications at key workflow transitions, messages and data upload status updates. See the [information on state transition rules](submission-states.md#state-transition-rules) to get more details.

### Notification Types

| Trigger | Recipients | Subject | Purpose |
|---------|-----------|---------|---------|
| Assigned to submission | Assignee | "Submission [REF] you have been assigned as [ROLE]" | Notify there is new submission person should be aware of. |
|  Submission phase change | see submission transition rules | "Submission [REF] [ACTION] | Notification about  |
| New Message Added | Relevant parties | (Context-dependent) | Facilitate communication |
| Ingestion failed | Submitter, Recipient | "Submission [REF] - data ingestion failed for dataset [REF]" | Notify submitter the ingestion process ended with errors -> need to re-upload |

The notification should clearly state whether its only informative or whether there is an action required from the notification recipient.
