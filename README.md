# LCSB Data Submission System (DSS)
[![CI](https://github.com/elixir-luxembourg/dss/actions/workflows/main.yml/badge.svg)](https://github.com/elixir-luxembourg/dss/actions/workflows/main.yml)

The [Data Submission System (DSS)](https://datasubmission.lcsb.uni.lu/about) is an open-source collaborative platform designed to streamline the submission of biomedical data and associated information to your infrastructure.
It supports submitters, recipients, and data stewards through a guided multi-step workflow including metadata collection, file transfer, review and validation, communication, and completion.

The DSS is ideal for research organizations, biomedical facilities, and data stewards managing data transfers and facing challenges such as lack of provenance, incomplete metadata, and departmental misalignment. The platform supports internal submissions as well as submissions from external collaborators and institutions, ensuring that data and associated metadata are captured in a structured, traceable, and harmonised manner. By incorporating validation mechanisms, the tool helps ensure that data and metadata are complete, accurate, and consistent while streamlining the overall process of data transfer. This strengthens data quality while providing full tracking of data provenance.

The system is currently used by [ELIXIR Luxembourg](https://elixir-luxembourg.org) for submissions under data sustainability services and by the [Luxembourg Centre for Systems Biomedicine (LCSB)](https://www.uni.lu/lcsb-en/) for general submissions in projects with restricted data access.

## Instances

Currently, the software runs as a [single instance at LCSB](https://datasubmission.lcsb.uni.lu/).

## Documentation

Full documentation including user guide is available **[here](https://elixir-luxembourg.github.io/dss/)**

## Quick Start

```bash
# First time setup (creates venv, installs deps, builds CSS, initializes DB)
./setup_dev.sh

# Start the development server
./run_dev.sh
```

Application runs at **http://127.0.0.1:5000**

**Demo Login Credentials:**
- Admin: `steward1@uni.lu` / `steward1`
- Data Provider: `submitter1@some.edu` / `submitter1`

See the [Development Guide](https://elixir-luxembourg.github.io/dss/development/development/) for manual setup, testing, migrations, and release instructions.

## Acknowledgements

This work was supported by [ELIXIR Luxembourg](https://elixir-luxembourg.org).

## License

This software is licensed under the [GNU Affero General Public License v3.0 (AGPL‑3.0)](https://www.gnu.org/licenses/agpl-3.0.en.html).
