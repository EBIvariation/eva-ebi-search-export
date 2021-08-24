#!/usr/bin/env python
import json
from argparse import ArgumentParser
from functools import cached_property

import requests

from ebi_eva_common_pyutils.metadata_utils import get_metadata_connection_handle
from ebi_eva_common_pyutils.pg_utils import get_all_results_for_query


class StudyExport:
    """Abstract class to provide basic function for exporting studies to the JSON format"""
    @staticmethod
    def get_fields(all_fields):
        return [
            {'name': f, 'value': all_fields[f]} for f in all_fields
        ]

    @staticmethod
    def set_values_to_entry(fields, cross_references=None, hierarchical_field=None):
        entry = {}
        if fields:
            entry['fields'] = fields
        if cross_references:
            entry['cross_references'] = cross_references
        if hierarchical_field:
            entry['hierarchical_field'] = hierarchical_field
        return entry

    @staticmethod
    def json_document(entries):
        return {
            'name': 'EVA studies',
            'entry_count': len(entries),
            'entries': entries
        }

    def json_dump(self):
        raise NotImplementedError


class StudyExportFromDB(StudyExport):
    """Class that extract studies from the database and provide them in a JSON document."""

    def __init__(self, properties_file, profile='production'):
        self.properties_file = properties_file
        self.profile = profile

    @cached_property
    def db_connect(self):
        return get_metadata_connection_handle(self.profile, self.properties_file)

    def json_dump(self):
        query = (
            'SELECT p.project_accession, p.title, p.description, a.vcf_reference_accession, sa.taxonomy_id FROM project p '
            'JOIN project_analysis pa ON p.project_accession=pa.project_accession '
            'JOIN analysis a ON pa.analysis_accession=a.analysis_accession '
            'JOIN assembly_set sa ON sa.assembly_set_id=a.assembly_set_id'
        )
        rows = get_all_results_for_query(self.db_connect, query)
        entries = []
        for project_accession, title, description, vcf_reference_accession, taxonomy_id in rows:
            fields = self.get_fields({
                'id': project_accession,
                'title': title,
                'description': description,
                'genome_accession': vcf_reference_accession,
                'taxonomy_id': taxonomy_id
            })
            entries.append({'fields': fields})
        return json.dumps(self.json_document(entries), indent=4)


class StudyExportFromAPI(StudyExport):
    """Class that extract studies from the API and provide them in a JSON document."""

    def json_dump(self):
        url = 'https://www.ebi.ac.uk/eva/webservices/rest/v1/meta/studies/all'
        response = requests.get(url)
        data = response.json()
        entries = []

        for study in data['response'][0]['result']:
            fields = self.get_fields({
                'id': study['id'],
                'title': study['name'],
                'description': study['description'],
                'genome_accession': study['assemblyAccession'],
                'taxonomy_id': study['taxonomyId'][0],
                'scientific_name': study['speciesScientificName'],
                'number_samples': study['numSamples']
            })
            cross_reference = []
            for publication in study['publications']:
                if publication and publication != '-':
                    cross_reference.append({'dbname': 'PUBMED', 'dbkey': str(publication)})
            cross_reference.append({'dbname': 'ENA', 'dbkey': study['id']})
            entries.append(self.set_values_to_entry(fields, cross_reference))
        return json.dumps(self.json_document(entries), indent=4)


def main():
    parser = ArgumentParser(description='Export the study data from EVA metadata endpoint to json')
    parser.add_argument('--output_file', type=str, help='file where the data should be written', required=True)
    args = parser.parse_args()
    with open(args.output_file, 'w') as open_file:
        print(StudyExportFromAPI().json_dump(), file=open_file)


if __name__ == "__main__":
    main()
