#!/usr/bin/env python
import argparse
import datetime
import hashlib
import json
import os
import pymongo

from ebi_eva_common_pyutils.mongo_utils import get_mongo_uri_for_eva_profile
from pymongo import MongoClient
from pymongo.read_concern import ReadConcern
from pymongo.read_preferences import ReadPreference
from typing import List


timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

BATCH_SIZE = 1000
ACCESSIONING_DATABASE_NAME = "eva_accession_sharded"
RELEASE_RECORD_COLLECTION_NAME = "releaseRecordEntity"


# See https://stackoverflow.com/a/57802672
def _as_batch(cursor, batch_size=BATCH_SIZE):
    # iterate over something (pymongo cursor, generator, ...) by batch.
    # Note: the last batch may contain less than batch_size elements.
    batch = []
    try:
        while True:
            for _ in range(batch_size):
                batch.append(next(cursor))
            yield batch
            batch = []
    except StopIteration:
        if len(batch):
            yield batch


def get_search_json_entry(release_record: dict) -> dict:
    search_index_entries_per_allele = []
    for ssInfo in release_record["ssInfo"]:
        search_index_entry = {
            "fields": [
                {
                    "name": "id",
                    "value": ssInfo['accession']
                },
                {
                    "name": "rs",
                    "value": f'rs{release_record["accession"]}'
                },
                {
                    "name": "chromosome",
                    "value": release_record["contig"]
                },
                {
                    "name": "start",
                    "value": release_record["start"]
                },
                {
                    "name": "variant_type",
                    "value": release_record["type"]
                },
                {
                    "name": "study",
                    "value": ssInfo['study']
                },
                {
                    "name": "reference",
                    "value": f"{ssInfo['refWithCtxBase']}"
                },
                {
                    "name": "alternate",
                    "value": f"{ssInfo['altWithCtxBase']}"
                }
            ],
            "cross_references": [{"dbname": "ENA", "dbkey": ssInfo['study']}]
        }

        search_index_entries_per_allele.append(search_index_entry)

    return search_index_entries_per_allele


def write_batch_to_output_dir(release_records: List[dict], json_output_file_name: str):
    with open(json_output_file_name, "w") as json_output_file_handle:
        search_json_entries = []
        for release_record in release_records:
            search_json_entries.extend(get_search_json_entry(release_record))
        json_output_for_batch = {
            "name": "Covid-19 data portal - Variants",
            "entry_count": len(search_json_entries),
            "entries": search_json_entries
        }
        print(json.dumps(json_output_for_batch, indent=4), file=json_output_file_handle)


def covid19_rsid_export(assembly_accession: str, mongo_handle: pymongo.MongoClient, batch_size: int,
                        json_output_dir: str):
    release_collection_handle = mongo_handle[ACCESSIONING_DATABASE_NAME].get_collection(
        name=RELEASE_RECORD_COLLECTION_NAME, read_preference=ReadPreference.SECONDARY_PREFERRED,
        read_concern=ReadConcern('majority'))
    regex_to_find = {"$regex": f"{assembly_accession}_*"}
    with release_collection_handle.find({"_id": regex_to_find}, sort=[('_id', pymongo.ASCENDING)],
                                        no_cursor_timeout=True) as cursor:
        for batch_index, release_records in enumerate(_as_batch(cursor, batch_size)):
            output_file_name = os.path.join(json_output_dir,
                                            f"covid19_rsid_export_{timestamp}_batch_{batch_index}.json")
            write_batch_to_output_dir(release_records, output_file_name)


def main():
    parser = argparse.ArgumentParser(description='Export Covid-19 RS ID data to EBI search JSON format')
    parser.add_argument('--assembly-accession', type=str, help="ex: Covid-19 assembly accession (ex: GCA_009858895.3)",
                        default="GCA_009858895.3", required=False)
    parser.add_argument('--private-config-xml-file', type=str, help="ex: /path/to/eva-maven-settings.xml",
                        required=True)
    parser.add_argument('--mongo-profile', type=str, help='MongoDB profile to use (ex: development, production etc.,) ',
                        default="production", required=False)
    parser.add_argument('--json-output-dir', type=str, help='JSON output directory (ex: /path/to/rsid_export_dir)',
                        required=True)
    args = parser.parse_args()
    with MongoClient(get_mongo_uri_for_eva_profile(eva_profile_name=args.mongo_profile,
                                                   settings_xml_file=args.private_config_xml_file)) as mongo_handle:
        covid19_rsid_export(args.assembly_accession, mongo_handle, BATCH_SIZE, args.json_output_dir)


if __name__ == "__main__":
    main()
