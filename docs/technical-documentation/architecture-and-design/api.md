# API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/submissions/dss` | List all DSS submissions known to the provisioner |
| `GET` | `/submissions/dss/diff` | Submissions in DSS not yet imported into iRODS |
| `POST` | `/submissions/dss/import` | Import a DSS submission as an iRODS project collection |
| `GET` | `/datasets/dss` | List all DSS datasets (`?submission=REF_NAME` to filter) |
| `GET` | `/datasets/dss/diff` | Datasets not yet imported into iRODS |
| `POST` | `/datasets/dss/import` | Import a DSS dataset into `data/raw/{dataset_id}/` |