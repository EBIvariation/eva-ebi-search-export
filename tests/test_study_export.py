import json
from unittest import TestCase

from study_export import StudyExportFromAPI


class TestStudyExporFromAPI(TestCase):

    def test_dump_from_api(self):
        json_text = StudyExportFromAPI().json_dump()
        json_data = json.loads(json_text)
        assert json_data['name'] == 'EVA studies'
        assert json_data['entry_count'] >= 404
        assert json_data['entry_count'] == len(json_data['entries'])
