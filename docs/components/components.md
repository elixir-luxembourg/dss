# External components

Following diagram shows external components and their relationship 

![components](./dss_components.drawio.png)

## Keycloak / OIDC 
- Authentication of users

## Data transfer tool
- The tool provides data upload links for each dataset registered in submission system.
- In our case LFT.
- Based on the size of the files, specific tool can be chosen...

## Insformation system

System providing list of existing active (running) projects.
The data gets ingested into the respective project space. 

This system can also provide:
- contracts under which submission is to happen
- membership/role of internal personnel in the project (e.g. data manager role) acting as recipients

### Database of partners
- either ROR.org
- or API call to the database of partners (can be the same system as the project database)

## ORCID
e.g. for selecting Authors of a dataset
This would require integration with Keycloak as well - even identities not coming from ORCID could have ORCID ID assigned.

## Arbitrary field integration (API)

This can be used for validation of metadata upon input. E.g. ontology lookup or any curated resource (ror.org, fairsharing.org, ...)

## Project flow diagram

```mermaid
flowchart TD
    A[Project Funded] --> B[Project Record Created in Project Database]
    B --> C[Define PI & Internal Personnel]
    C --> R
    R --> T{Contract needed?}
    T -- No --> V[Create copy]
    V --> K
    T -- Yes --> D[Contract Negotiation]
    D --> E[Contract Signed]
    E --> R
    R[Provision Assets] -- external data --> F[Open Submission in DSS]
    F --> G[Data Upload]
    K --> H1{Is it first dataset?}
    H1 -- Yes --> H[Create Project Collection in iRODS]
    H1 -- No --> J
    H --> I[Grant Read Access to Project Users]
    H --> J[Store Dataset Existence in Project Database]
    G --> P
    K[Ingestion] --> H

    %% Samples received by post
    R -- external samples --> L
    L[Samples Received] --> M[Project Entity Created in ELN]
    M --> N[Lab Experiment]
    N --> O[Dataset Generated]
    O --> P[Dataset Picked Up by Ingestion Module]
    P --> K

    %% Data re-used from other projectß
    R -- internal re-use --> Q
    Q[Request Access to Data/Samples from Original Project] --> S{Approved?}
    S -- Yes --> T
    S -- No --> U[Access Denied]

    %% Data from platforms
    L --> W
    W[Processing by platform] --> F
```

