import json
import os
import re
from io import StringIO

from elixir_dss import app, db
from elixir_dss.forms.submissions_forms import Contact, DatasetForm
from elixir_dss.models.submission import Submission, SubmissionDataset


class SubmissionExporter:
    def __init__(self, objects=None):
        """
        objects would be Submission objects
        i.e.:
        objects = Submission.query.all()
        objects = Submission.query.filter(title='Submission title')
        """
        if objects is not None:
            self.objects = objects
        else:
            self.objects = None

    # def set_objects(objects):
    #     self.objects = objects

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
                # if verbose:
                #     import traceback
                #     ex = traceback.format_exception(*sys.exc_info())
                #     logger.error('\n'.join([e for e in ex]))
                # if stop_on_error:
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
            # submission_attachments = SubmissionAttachment.query.filter_by(submission_id=submission.id).all()
            # for attachment in submission_attachments:
            #
            #     try:
            #         path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], attachment.folder_name)
            #         attachment_folder_name = os.path.join(export_directory, attachment.folder_name)
            #         if not os.path.exists(attachment_folder_name):
            #             os.makedirs(attachment_folder_name)
            #         attachment_file = os.path.join(path_on_server, attachment.file_names)
            #         os.popen('cp ' + attachment_file + ' ' + attachment_folder_name)
            #
            #     except OSError as err:
            #         err.extend(err.args[0])

            # shutil.make_archive(export_directory, 'zip', export_directory)
            # app.logger.info("Created zip file")
        return buffer

    def export_submission(self, sub: Submission) -> dict:
        # TODO: this method could be actually just Submission.to_dict() call
        sub_info = {}

        # sub_info['external_id'] = sub.ref_name
        sub_info["source"] = "https://elixir-dcp.lcsb.uni.lu/"
        sub_info["contacts"] = []
        for contact in sub.submission_contacts:
            contact_info = self.export_contact(sub, contact)
            sub_info["contacts"].append(contact_info)
        sub_info["name"] = sub.ref_name
        sub_info["title"] = sub.title
        sub_info["submission_scope_code"] = sub.submission_scope_code
        sub_info["submitting_institution_accession"] = sub.institution_accession
        sub_info["submitting_institution_name"] = sub.provider_institute_name()
        sub_info["submitting_institution_address"] = sub.provider_institute_address()

        sub_info["created_on"] = sub.created_on.strftime("%Y-%m-%d")
        if sub.finalised_on:
            sub_info["finalised_on"] = sub.finalised_on.strftime("%Y-%m-%d")
        sub_info["submission_scope_code"] = sub.submission_scope.code
        sub_info["submission_scope_label"] = sub.submission_scope.label
        if sub.local_custodians_json:
            sub_info["local_custodians"] = sub.local_custodians()
        if sub.local_project_name:
            sub_info["local_project"] = sub.local_project_name

        submitters = []
        for access in sub.submission_accesses:
            provider_info = {}
            provider_info["institution"] = access.user.institution_accession
            provider_info["email"] = access.user.email
            provider_info["first_name"] = access.user.first_name
            provider_info["last_name"] = access.user.last_name
            provider_info["phone_no"] = access.user.phone_no

            if access.user.addr_line1 or access.user.addr_line2:
                provider_info["address"] = (
                    (access.user.addr_line1 or "")
                    + " "
                    + (access.user.addr_line2 or "")
                )

            provider_info["role"] = "Data_Manager"
            submitters.append(provider_info)

        sub_info["data_providers"] = submitters

        sub_info["studies"] = self.export_studies(sub)

        sub_info["data_declarations"] = self.export_datasets(sub)

        sub_info["legal_bases"] = self.export_legal_bases(sub)

        sub_info["attachments"] = self.export_attachment_info(sub)

        return sub_info

    def export_datasets(self, sub: Submission):
        dataset_list = []

        for dataset in sub.datasets:
            dataset_info = {}

            dataset_info["title"] = dataset.title

            dataset_info["use_restrictions"] = self.export_dataset_restrictions(dataset)

            if dataset.restriction_ts_lcsb:
                dataset_info["storage_end_date"] = dataset.restriction_ts_lcsb_notes

            dataset_info["source_study"] = dataset.study.name
            dataset_info["legal_basis_data_collection_std"] = (
                dataset.legal_basis_collection_std.label
            )
            dataset_info["legal_basis_data_sharing_std"] = (
                dataset.legal_basis_sharing_std.label
            )
            dataset_info["legal_basis_data_collection_spec"] = (
                dataset.legal_basis_collection_std.label
            )
            dataset_info["legal_basis_data_sharing_spec"] = (
                dataset.legal_basis_sharing_std.label
            )
            dataset_info["legal_basis_notes"] = dataset.legal_basis_notes

            if dataset.dac_approval_required:
                if dataset.access_form_required:
                    dataset_info["access_category"] = "open-access"
                    dataset_info["access_procedure"] = (
                        "No additional form is needed to request access."
                    )
                else:
                    dataset_info["access_category"] = "registered-access"
                    dataset_info["access_procedure"] = (
                        "Additional form is needed to request access."
                    )
            else:
                dataset_info["access_category"] = "controlled-access"
                dataset_info["access_procedure"] = dataset.dac_approval_notes

            dataset_info["data_types"] = dataset.sci_data_type_names()
            dataset_info["gdpr_datatypes"] = dataset.gdpr_data_type_names()
            dataset_info["gdpr_datatypes_notes"] = dataset.gdpr_datatypes_notes

            if dataset.sci_datatypes_notes:
                dataset_info["sci_datatypes_notes"] = dataset.sci_datatypes_notes

            dataset_info["has_special_subjects"] = dataset.has_special_subjects
            dataset_info["special_subject_notes"] = dataset.special_subjects_notes

            if dataset.has_samples:
                dataset_info["data_types"].append("Samples")
                if dataset.sci_datatypes_notes:
                    dataset_info["data_types_notes"] = (
                        dataset_info.get("data_types_notes", "")
                        + " Notes on samples: "
                        + dataset.sci_datatypes_notes
                    )

            dataset_info["consent_status"] = dataset.consent_status.label.lower()
            if dataset.consent_notes:
                dataset_info["consent_notes"] = dataset.consent_notes
            dataset_info["de_identification"] = (
                dataset.de_identification_type.label.lower()
            )
            dataset_info["subject_categories"] = dataset.subject_category.label.lower()
            # use_restrictions = []
            # for duc_instance in dataset.duc_codes:
            #     use_restrictions.append({'ga4gh_code': duc_instance.ga4gh_code,
            #                              'note': duc_instance.note})
            # if use_restrictions:
            #     dataset_info['use_restrictions'] = use_restrictions
            dataset_list.append(dataset_info)
        return dataset_list

    @staticmethod
    def export_legal_bases(sub: Submission):
        def parse_label(legal_basis_label: str):
            return re.search(r"([0-9].*)\)", legal_basis_label).group(1)

        legal_bases = []

        dataset_form = DatasetForm()

        for dataset in sub.datasets:
            legal_base_info_collection_std = {}
            legal_base_info_collection_std["data_declarations"] = dataset.title
            legal_base_info_collection_std["legal_basis_codes"] = parse_label(
                dataset.legal_basis_collection_std.label
            )
            legal_base_info_collection_std["personal_data_codes"] = "Standard"
            legal_base_info_collection_std["legal_basis_notes"] = (
                dataset_form.legal_basis_collection_std_code.label.text
            )

            legal_bases.append(legal_base_info_collection_std)

            legal_base_info_collection_spec = {}
            legal_base_info_collection_spec["data_declarations"] = dataset.title
            legal_base_info_collection_spec["legal_basis_codes"] = parse_label(
                dataset.legal_basis_collection_spec.label
            )
            legal_base_info_collection_spec["personal_data_codes"] = "Special"
            legal_base_info_collection_spec["legal_basis_notes"] = (
                dataset_form.legal_basis_collection_spec_code.label.text
            )

            legal_bases.append(legal_base_info_collection_spec)

            legal_base_info_sharing_std = {}
            legal_base_info_sharing_std["data_declarations"] = dataset.title
            legal_base_info_sharing_std["legal_basis_codes"] = parse_label(
                dataset.legal_basis_sharing_std.label
            )
            legal_base_info_sharing_std["personal_data_codes"] = "Standard"
            legal_base_info_sharing_std["legal_basis_notes"] = (
                dataset_form.legal_basis_sharing_std_code.label.text
            )

            legal_bases.append(legal_base_info_sharing_std)

            legal_base_info_sharing_spec = {}
            legal_base_info_sharing_spec["data_declarations"] = dataset.title
            legal_base_info_sharing_spec["legal_basis_codes"] = parse_label(
                dataset.legal_basis_sharing_spec.label
            )
            legal_base_info_sharing_spec["personal_data_codes"] = "Special"
            legal_base_info_sharing_spec["legal_basis_notes"] = (
                dataset_form.legal_basis_sharing_spec_code.label.text
            )

            legal_bases.append(legal_base_info_sharing_spec)

        return legal_bases

    @staticmethod
    def export_dataset_restrictions(dataset: SubmissionDataset) -> list[dict]:
        restriction_list = []

        restriction_codes = {
            "rs": "RS-[XX]",
            "gs": "GS-[XX]",
            "us": "US",
            "pub": "PUB",
            "rtn": "RTN",
            "ip": "IP",
            "ps": "PS",
            "ts_lcsb": "TS-[XX]",
            "ts": "TS-[XX]",
        }
        dataset_form = DatasetForm()
        for field_prefix, restriction_code in restriction_codes.items():
            restriction_dict = {}
            restriction_dict["use_class"] = restriction_code
            restriction_dict["use_restriction_rule"] = (
                "CONSTRAINT"
                if getattr(dataset, f"restriction_{field_prefix}")
                else "NO CONSTRAINT"
            )
            restriction_dict["use_class_note"] = getattr(
                dataset_form, f"restriction_{field_prefix}"
            ).label.text
            restriction_dict["use_restriction_note"] = getattr(
                dataset, f"restriction_{field_prefix}_notes"
            )

            restriction_list.append(restriction_dict)

        if dataset.restriction_other_notes:
            restriction_other_dict = {}
            restriction_other_dict["use_class"] = "Other"
            restriction_other_dict["use_restriction_rule"] = "CONSTRAINT"
            restriction_other_dict["use_class_note"] = (
                dataset_form.restriction_other_notes.description
            )
            restriction_other_dict["use_restriction_note"] = (
                dataset.restriction_other_notes
            )
            restriction_list.append(restriction_other_dict)

        return restriction_list

    @staticmethod
    def export_attachment_info(sub: Submission):
        attachment_list = []
        for att in sub.attachments:
            att_info = {}
            att_info["description"] = att.note
            files_list = []
            names = att.file_names.strip(" \t\n\r").split(" ")
            for name in names:
                files_list.append({"$ref": os.path.join(att.folder_name, name)})
            att_info["files"] = files_list
            attachment_list.append(att_info)
        return attachment_list

    def export_studies(self, sub: Submission):
        study_list = []
        for stdy in sub.studies:
            study_info = {}
            study_info["title"] = stdy.name
            study_info["description"] = stdy.description
            study_info["ethics_approval_no"] = stdy.ethics_approval_no
            study_info["ethics_approval_exists"] = stdy.ethics_approval_exists
            study_info["study_types"] = stdy.study_feature_names()
            contacts = []
            for contact in stdy.study_contacts:
                contact_info = self.export_contact(sub, contact)
                contacts.append(contact_info)
            study_info["contacts"] = contacts
            study_list.append(study_info)
        return study_list

    @staticmethod
    def export_contact(sub: Submission, contact: Contact):
        contact_info = contact.to_dict()
        contact_info["affiliations"] = [sub.institution_accession]
        return contact_info
