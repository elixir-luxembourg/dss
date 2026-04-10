import json
from io import StringIO

from elixir_dss import app, db
from elixir_dss.models.submission import Submission


class SubmissionExporter:
    def __init__(self, objects=None):
        """
        objects would be Submission objects
        i.e.:
        objects = db.session.scalars(db.select(Submission)).all()
        objects = db.session.scalars(
            db.select(Submission).filter_by(ref_name="ELX_LU_SUB-123")
        ).all()
        """
        if objects is not None:
            self.objects = objects
        else:
            self.objects = None

    def export_to_file(self, file_handle, stop_on_error=False, verbose=False):
        result = True
        try:
            buffer = self.export_to_buffer(StringIO())
            print(buffer.getvalue(), file=file_handle)
        except Exception as e:
            app.logger.error("Submission export failed")
            app.logger.error(str(e))
            result = False
        app.logger.info(f"Submission export complete see file: {file_handle}")
        return result

    def export_to_buffer(self, buffer, stop_on_error=False, verbose=False):
        for submission in self.objects:
            submission_ref_name = submission.ref_name
            app.logger.info(f' * Exporting submission: "{submission_ref_name}"...')
            try:
                submission_dict = self.export_submission(submission)
            except Exception as e:
                app.logger.error(f"Export failed for submission {submission_ref_name}")
                app.logger.error(str(e))
                raise e
            json.dump(
                {
                    "$schema": "https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/elu-dataset.json",
                    "items": [submission_dict],
                },
                buffer,
                indent=4,
            )
            submission.exported = True
            db.session.add(submission)
            db.session.commit()
        return buffer

    def export_submission(self, sub: Submission) -> dict:
        studies = self.export_studies(sub)
        datasets = self.export_datasets(sub)

        for study in studies:
            study["datasets"] = [ds for ds in datasets if ds["study"] == study["title"]]

        return {
            "submission": {
                "submission_id": normalize(sub.ref_name),
                "created_on": normalize(sub.created_on),
                "finalised_on": normalize(sub.finalised_on),
                "status": normalize(
                    sub.current_status.value if sub.current_status else None
                ),
                "local_project_name": normalize(sub.local_project_name),
                "local_custodians_json": normalize(sub.local_custodians_json),
                "institution_accession": normalize(sub.institution_accession),
                "providers": normalize(sub.provider_user_names()),
            },
            "studies": studies,
        }

    @staticmethod
    def export_datasets(sub: Submission):
        dataset_list = []

        for ds in sub.datasets:
            dataset_info = {
                "dataset_id": normalize(ds.internal_id),
                "title": normalize(ds.title),
                "description": normalize(ds.description),
                "study": normalize(ds.study.name if ds.study else None),
                "external_id": normalize(ds.external_identifiers),
                "gdpr_data_types": normalize(ds.gdpr_data_type_names()),
                "scientific_data_types": normalize(ds.sci_data_type_names()),
                "contains_personal_data": normalize(ds.contains_personal_data),
                "data_processing_type": normalize(ds.data_processing_type),
                "special_category_data": normalize(ds.is_special_category_data),
                "special_subjects": normalize(ds.has_special_subjects),
                "consent_status": normalize(
                    ds.consent_status.label if ds.consent_status else None
                ),
                "legal_basis_collection": normalize(
                    ds.legal_basis_collection_std.label
                    if ds.legal_basis_collection_std
                    else None
                ),
                "legal_basis_sharing": normalize(
                    ds.legal_basis_sharing_std.label
                    if ds.legal_basis_sharing_std
                    else None
                ),
                "records": normalize(ds.number_of_records),
                "dataset_version": normalize(ds.dataset_version),
                "creation_date": normalize(ds.creation_date),
                "last_update_date": normalize(ds.last_update_date),
                "file_types": normalize(ds.file_type_names()),
                "data_standards": normalize(ds.data_standard_names()),
                "size_bytes": normalize(ds.byte_size),
                # Use conditions
                "uc_project_limited": normalize(ds.use_restriction_project),
                "uc_research_use_limited": normalize(ds.use_restriction_research_use),
                "uc_research_area_restriction": normalize(ds.restriction_rs),
                "uc_research_area_notes": "| " + normalize(ds.restriction_rs_notes)
                if ds.restriction_rs_notes
                else "",
                "uc_geographic_restriction": normalize(ds.restriction_gs),
                "uc_geographic_notes": "| " + normalize(ds.restriction_gs_notes)
                if ds.restriction_gs_notes
                else "",
                "uc_recipient_type_restriction": normalize(
                    ds.restriction_user_specific
                ),
                "uc_recipient_type_notes": "| "
                + normalize(ds.restriction_user_specific_notes)
                if ds.restriction_user_specific_notes
                else "",
                "uc_user_restriction": normalize(ds.restriction_us),
                "uc_user_notes": "| " + normalize(ds.restriction_us_notes)
                if ds.restriction_us_notes
                else "",
                "uc_publication_restriction": normalize(ds.restriction_pub),
                "uc_publication_notes": "| " + normalize(ds.restriction_pub_notes)
                if ds.restriction_pub_notes
                else "",
                "uc_time_restriction": normalize(ds.restriction_ts),
                "uc_time_notes": "| " + normalize(ds.restriction_ts_notes)
                if ds.restriction_ts_notes
                else "",
                "uc_lcsb_time_restriction": normalize(ds.restriction_ts_lcsb),
                "uc_lcsb_time_date": "| Until: "
                + normalize(ds.restriction_ts_lcsb_date)
                if ds.restriction_ts_lcsb_date
                else "",
                "uc_return_requirement": normalize(ds.restriction_rtn),
                "uc_return_notes": "| " + normalize(ds.restriction_rtn_notes)
                if ds.restriction_rtn_notes
                else "",
                "uc_ip_restriction": normalize(ds.restriction_ip),
                "uc_ip_notes": "| " + normalize(ds.restriction_ip_notes)
                if ds.restriction_ip_notes
                else "",
                "uc_dac_required": normalize(ds.dac_approval_required),
                "uc_dac_notes": "| " + normalize(ds.dac_approval_notes)
                if ds.dac_approval_notes
                else "",
                "uc_access_form_required": normalize(ds.access_form_required),
                "uc_other_notes": normalize(ds.restriction_other_notes),
            }

            dataset_list.append(dataset_info)
        return dataset_list

    @staticmethod
    def export_studies(sub: Submission):
        study_list = []
        for stdy in sub.studies:
            study_info = {
                "title": normalize(stdy.name),
                "description": normalize(stdy.description),
                "ethics_approval_no": normalize(stdy.ethics_approval_no),
                "ethics_approval_exists": normalize(
                    "Yes" if stdy.ethics_approval_exists else "No"
                ),
                "study_types": normalize(stdy.study_feature_names),
                "multi_center_study": normalize(stdy.multi_center_study),
                "species_json": normalize(stdy.species_json),
                "diseases_json": normalize(stdy.diseases_json),
                "number_of_subjects": normalize(stdy.number_of_subjects),
                "sample_sources_json": normalize(stdy.sample_sources_json),
                "informed_consent_given": normalize(stdy.informed_consent_given),
                "external_id": normalize(stdy.external_identifiers_json),
            }
            study_list.append(study_info)
        return study_list


def _parse_json_string(value: str):
    stripped = value.strip()
    if not (
        (stripped.startswith("[") and stripped.endswith("]"))
        or (stripped.startswith("{") and stripped.endswith("}"))
    ):
        return None

    try:
        parsed = json.loads(stripped)
    except Exception:
        return None

    if isinstance(parsed, list):
        return ", ".join(str(v) for v in parsed) if parsed else "-"

    if isinstance(parsed, dict):
        return ", ".join(f"{k}: {v}" for k, v in parsed.items()) if parsed else "-"

    return None


def normalize(value):
    if value in (None, "", [], {}):
        return "-"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "-"

    if hasattr(value, "isoformat"):
        return value.isoformat()

    if isinstance(value, str):
        result = _parse_json_string(value)
        if result is not None:
            return result
        return value.strip()

    return value
