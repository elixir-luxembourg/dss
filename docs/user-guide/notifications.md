## Email Notifications

The system automatically sends email notifications at key workflow transitions, messages and data upload status updates. See the [information on state transition rules](submission-states.md#state-transition-rules) to get more details.

### Notification Types

| Trigger | Recipients | Subject | Purpose |
|---------|-----------|---------|---------|
| Assigned to submission | (new) Submitter | "Submission [REF] you have been assigned as [ROLE]" | Submitter is notified about new permissions and responsabilities |
| Submission phase change | see submission transition rules | "Submission [REF] [ACTION] | Involved users are notified about progress |
| New Message Added | Submitter, Recipient | "Submission [REF] - new message" | Notify about non-standard action or inquiry on the submission level |
| Ingestion failed | Submitter, Recipient | "Submission [REF] - data ingestion failed for dataset [REF]" | Notify submitter the ingestion process ended with errors -> need to re-upload |

The notification clearly state whether its only informative or whether there is an action required from the notification adressee.
