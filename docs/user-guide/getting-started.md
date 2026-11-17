# Getting Started

## Video Tutorial

<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
  <iframe
    src="https://player.vimeo.com/video/1191817703"
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;"
    allow="autoplay; fullscreen; picture-in-picture"
    allowfullscreen
    title="DSS Tutorial">
  </iframe>
</div>

---

## Accessing the System

DSS is a web application. Access it via your browser at the URL provided by your institution.

For the LCSB instance: [https://datasubmission.lcsb.uni.lu](https://datasubmission.lcsb.uni.lu)

### Logging In

**OIDC / Institutional login (production):**
Click **Sign in** and authenticate with your institutional account via the OIDC provider (e.g. Keycloak). On your first login, you will be prompted to complete a short registration form.

**Local login (development / demo):**
Use one of the built-in demo accounts:

| Email | Password | Role |
|-------|----------|------|
| `steward1@uni.lu` | `steward1` | Admin (Data Steward) |
| `submitter1@some.edu` | `submitter1` | Data Provider |
| `submitter2@some.edu` | `submitter2` | Data Provider |

---

## Starting a Submission

Submissions are initiated by a **Data Steward**, not by the submitter directly.

1. Contact your Data Steward to open a new submission.
2. The steward creates a submission, assigns you as a **Submitter**, and sets a recipient project.
3. You will receive an email notification with a link to the submission.

See [Managing Submissions](managing-submissions.md) for a full walkthrough of each phase.

---

## Running a Local Development Instance

If you want to run DSS locally for development or evaluation, see the [Development Guide](../development/development.md).
