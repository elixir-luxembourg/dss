from elixir_dcp.models.submission import Submission, SubmissionStudy, SubmissionDataDeclaration
from typing import List, Dict
from elixir_dcp.forms.submissions_forms import DatadecForm, Contact
from elixir_dcp import db, app
from io import StringIO
import os
import json

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

    def set_objects(objects):
        self.objects = objects

    def export_to_file(self, file_handle, stop_on_error=False, verbose=False):
        result = True
        try:
            buffer = self.export_to_buffer(StringIO())
            print(buffer.getvalue(), file=file_handle)
        except Exception as e:
            app.logger.error('Submission export failed')
            app.logger.error(str(e))
            result = False
        app.logger.info(f'Submission export complete see file: {file_handle}')
        return result

    def export_to_buffer(self, buffer, stop_on_error=False, verbose=False):
        for submission in self.objects:
            submission_ref_name = submission.ref_name
            app.logger.info(f' * Exporting submission: "{submission_ref_name}"...')
            try:
                submission_dict = self.export_submission(submission)
            except Exception as e:
                app.logger.error(f'Export failed for submission {submission_ref_name}')
                app.logger.error(str(e))
                # if verbose:
                #     import traceback
                #     ex = traceback.format_exception(*sys.exc_info())
                #     logger.error('\n'.join([e for e in ex]))
                # if stop_on_error:
                raise e
            json.dump({
                    "$schema": "https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/elu-dataset.json",
                    "items": [submission_dict]}, buffer, indent=4)
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
        
    def export_submission(self, sub: Submission) -> Dict:
        #TODO: this method could be actually just Submission.to_dict() call
        sub_info = {}

        #sub_info['elu_accession'] = sub.ref_name
        sub_info['source'] = 'https://elixir-dcp.lcsb.uni.lu/'
        sub_info['contacts'] = []
        for contact in sub.submission_contacts:
                contact_info = self.export_contact(sub, contact)
                sub_info['contacts'].append(contact_info)
        sub_info['name'] = sub.ref_name
        sub_info['title'] = sub.title
        sub_info['submission_scope_code'] = sub.submission_scope_code
        sub_info['submitting_institution_accession'] = sub.institution_accession
        sub_info['submitting_institution_name'] = sub.provider_institute_name()
        sub_info['submitting_institution_address'] = sub.provider_institute_address()

        sub_info['created_on'] = sub.created_on.strftime("%Y-%m-%d")
        if sub.finalised_on:
            sub_info['finalised_on'] = sub.finalised_on.strftime("%Y-%m-%d")
        sub_info['submission_scope_code'] = sub.submission_scope.code
        sub_info['submission_scope_label'] = sub.submission_scope.label
        if sub.local_custodians_json:
            sub_info['local_custodians'] = sub.local_custodians()
        if sub.local_project_name:
            sub_info['local_project'] = sub.local_project_name

        submitters = []
        for access in sub.submission_accesses:
            provider_info = {}
            provider_info['institution'] = access.user.institution_accession
            provider_info['email'] = access.user.email
            provider_info['first_name'] = access.user.first_name
            provider_info['last_name'] = access.user.last_name
            provider_info['phone_no'] = access.user.phone_no

            if access.user.addr_line1 or access.user.addr_line2:
                provider_info['address'] = (access.user.addr_line1 or '') + ' ' + (access.user.addr_line2 or '')

            provider_info['role'] = 'Data_Manager'
            submitters.append(provider_info)

        sub_info['data_providers'] = submitters

        sub_info['studies'] = self.export_studies(sub)

        sub_info['data_declarations'] = self.export_datadecs(sub)

        sub_info['legal_bases'] = self.export_legal_bases(sub)

        sub_info['attachments'] = self.export_attachment_info(sub)

        return sub_info

    def export_datadecs(self, sub: Submission):
        datadec_list = []

        for datadec in sub.datadecs:
            datadec_info = {}
            
            datadec_info['title'] = datadec.title
            
            datadec_info['use_restrictions'] = self.export_datadec_restrictions(datadec)
            
            if datadec.restriction_ts_lcsb:
                datadec_info['storage_end_date'] = datadec.restriction_ts_lcsb_notes
            
            datadec_info['source_study'] = datadec.study.name
            datadec_info['legal_basis_data_collection_std'] = datadec.legal_basis_collection_std.label
            datadec_info['legal_basis_data_sharing_std'] = datadec.legal_basis_sharing_std.label
            datadec_info['legal_basis_data_collection_spec'] = datadec.legal_basis_collection_std.label
            datadec_info['legal_basis_data_sharing_spec'] = datadec.legal_basis_sharing_std.label
            datadec_info['legal_basis_notes'] = datadec.legal_basis_notes

            if datadec.dac_approval_required:
                if datadec.access_form_required:
                    datadec_info["access_category"] = "open-access"
                    datadec_info["access_procedure"] = "No additional form is needed to request access."
                else:
                    datadec_info["access_category"] = "registered-access" 
                    datadec_info["access_procedure"] = "Additional form is needed to request access."
            else:
                datadec_info["access_category"] = "controlled-access"
                datadec_info["access_procedure"] = datadec.dac_approval_notes
        
            datadec_info['data_types'] = datadec.sci_data_type_names()
            datadec_info['gdpr_datatypes'] = datadec.gdpr_data_type_names()
            datadec_info['gdpr_datatypes_notes'] = datadec.gdpr_datatypes_notes

            if datadec.sci_datatypes_notes:
                datadec_info['sci_datatypes_notes'] = datadec.sci_datatypes_notes
            
            datadec_info['has_special_subjects'] = datadec.has_special_subjects
            datadec_info['special_subject_notes'] = datadec.special_subjects_notes

            if datadec.has_samples:
                datadec_info['data_types'].append("Samples")
                if datadec.sci_datatypes_notes:
                    datadec_info['data_types_notes'] =  datadec_info.get('data_types_notes','') + " Notes on samples: " + datadec.sci_datatypes_notes

            datadec_info['consent_status'] = datadec.consent_status.label.lower()
            if datadec.consent_notes: datadec_info['consent_notes'] = datadec.consent_notes
            datadec_info['de_identification'] = datadec.de_identification_type.label.lower()
            datadec_info['subject_categories'] = datadec.subject_category.label.lower()
            # use_restrictions = []
            # for duc_instance in datadec.duc_codes:
            #     use_restrictions.append({'ga4gh_code': duc_instance.ga4gh_code,
            #                              'note': duc_instance.note})
            # if use_restrictions:
            #     datadec_info['use_restrictions'] = use_restrictions
            datadec_list.append(datadec_info)
        return datadec_list

    @staticmethod
    def export_legal_bases(sub: Submission):
        legal_bases=[]
        for datadec in sub.datadecs:
            legal_base_info_collection_std = {}

            legal_base_info_collection_std['data_declarations'] = datadec.title
            legal_base_info_collection_std['legal_basis_codes'] = datadec.legal_basis_collection_std.label #regex
            legal_base_info_collection_std['personal_data_codes'] = 'Standard'
        
            
            legal_base_info_collection_std['legal_basis_notes'] = 'What is the legal basis according to Art. 6.1 GDPR for the collection of standard (non-sensitive) personal data?'

            #datadec_info['sci_datatypes'] = datadec.sci_data_type_names()
            #legal_base_info['gdpr_datatypes'] = datadec.gdpr_data_type_names()
            #legal_base_info['gdpr_datatypes_notes'] = datadec.gdpr_datatypes_notes
            #legal_bases.append(legal_base_info)
            #legal_base_info_collection_spec = {}
            #legal_base_info['data_declarations'] = datadec.title
            #legal_base_info['legal_basis_codes'] = datadec.legal_basis_collection_spec.label #regex
            #legal_base_info['personal_data_codes'] = 'Special'
        
            
            #legal_base_info['legal_basis_notes'] = 'What is the legal basis according to Art. 6.1 GDPR for the collection of standard (non-sensitive) personal data?'
            legal_bases.append(legal_base_info_collection_std)
        return legal_bases
        
    @staticmethod
    def export_datadec_restrictions(datadec: SubmissionDataDeclaration) -> List[Dict]:
        restriction_list = []
        
        restriction_codes = {
            'rs': "RS-[XX]",
            'gs': "GS-[XX]",
            'us': "US",
            'pub': "PUB",
            'rtn': "RTN",
            'ip': "IP",
            'ps': "PS",
            'ts_lcsb': 'TS-[XX]',
            'ts': 'TS-[XX]'
        }
        datadec_form = DatadecForm()
        for prefix, restriction_code in enumerate(restriction_codes):
            restriction_dict = {}
            restriction_dict['use_class'] = restriction_code
            restriction_dict['use_restriction_rule'] = 'CONSTRAINT' if getattr(datadec, f'restriction_{restriction_code}') else 'NO CONSTRAINT'
            restriction_dict['use_class_note'] = getattr(datadec_form, f'restriction_{restriction_code}').label.text
            restriction_dict['use_restriction_note'] = getattr(datadec, f'restriction_{restriction_code}_notes')
            restriction_list.append(restriction_dict)
            
        if datadec.restriction_other_notes:
            restriction_other_dict = {}
            restriction_other_dict['use_class'] = "Other"
            restriction_other_dict['use_restriction_rule'] = 'CONSTRAINT'
            restriction_other_dict['use_class_note'] = getattr(datadec_form, f'restriction_other_notes').description
            restriction_other_dict['use_restriction_note'] = getattr(datadec, f'restriction_{restriction_code}_notes')
            restriction_list.append(restriction_other_dict)

        return restriction_list
        
    @staticmethod
    def export_attachment_info(sub: Submission):
        attachment_list = []
        for att in sub.attachments:
            att_info = {}
            att_info['description'] = att.note
            files_list = []
            names = att.file_names.strip(' \t\n\r').split(" ")
            for name in names:
                files_list.append({"$ref": os.path.join(att.folder_name, name)})
            att_info['files'] = files_list
            attachment_list.append(att_info)
        return attachment_list

    def export_studies(self, sub: Submission):
        study_list = []
        for stdy in sub.studies:
            study_info = {}
            study_info['title'] = stdy.name
            study_info['description'] = stdy.description
            study_info['ethics_approval_no'] = stdy.ethics_approval_no
            study_info['ethics_approval_exists'] = stdy.ethics_approval_exists
            study_info['study_types'] = stdy.study_feature_names()
            contacts = []
            for contact in stdy.study_contacts:
                contact_info = self.export_contact(sub, contact)
                contacts.append(contact_info)
            study_info['contacts'] = contacts
            study_list.append(study_info)
        return study_list
    
    @staticmethod
    def export_contact(sub: Submission, contact: Contact):
        contact_info = contact.to_dict()
        contact_info['affiliations'] = [sub.institution_accession]
        return contact_info
