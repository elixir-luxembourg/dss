from flask_script import Command, Manager, Option
from elixir_dcp.importer.importer_utils import schedule_submission_export
from elixir_dcp import app
from typing import List

class ExportSubmissionsCommand(Command):
    "Exports submissions into JSON files"

    option_list = [
            Option('--destination', '-d',
             default = app.config.get('SUBMISSION_EXPORT_FOLDER'),
             dest='path_to_json_directory',
             help="Path to the destination folder. Default destination is:" + app.config.get('SUBMISSION_EXPORT_FOLDER')),
             
            Option('--all', '-a',
            action="store_true",
            dest='export_all_submissions',
            help="Export also submissions which have been already exported in the past. This will overwrite existing JSON files."),
            
            Option('--submissionID', '-i',
            default=[],
            nargs='*',
            dest="submissions_to_export",
            help="List of submissionIDs to export.")
    ]

    def run(self, path_to_json_directory: str, export_all_submissions: bool, submissions_to_export: List[str]):
        schedule_submission_export(path_to_json_directory, export_all_submissions, submissions_to_export)

