import covid19_rsid_export
import glob
import json
import os
import pymongo
import shutil

from __init__ import base_dir
from covid19_rsid_export import covid19_rsid_export, RELEASE_RECORD_COLLECTION_NAME, ACCESSIONING_DATABASE_NAME
from unittest import TestCase


class TestCovid19RSIDExport(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCovid19RSIDExport, self).__init__(*args, **kwargs)
        self.resources_folder = os.path.join(base_dir, 'tests', 'resources')
        self.processing_folder = os.path.join(self.resources_folder, 'processing')
        self.json_to_be_loaded_to_mongo = os.path.join(self.resources_folder, 'covid19_release_record_test_data.json')

    def setUp(self) -> None:
        os.makedirs(self.processing_folder, exist_ok=True)
        self.mongo_handle = pymongo.MongoClient()
        self.cleanupDB()
        with open(self.json_to_be_loaded_to_mongo) as json_file_handle:
            json_documents = json.load(json_file_handle)
            # Insert 23 records
            self.mongo_handle[ACCESSIONING_DATABASE_NAME][RELEASE_RECORD_COLLECTION_NAME]\
                .insert_many(json_documents)

    def tearDown(self) -> None:
        self.cleanupDB()
        shutil.rmtree(self.processing_folder, ignore_errors=True)

    def cleanupDB(self):
        self.mongo_handle.drop_database(ACCESSIONING_DATABASE_NAME)
        self.mongo_handle.close()

    def test_export(self):
        covid19_rsid_export("GCA_009858895.3", self.mongo_handle, batch_size=10,
                            json_output_dir=self.processing_folder)
        # With a batch size of 10, ensure that the 46 index records generated for the 23 records in the database
        # are split across 3 files, 2 each with 20 index records and another with 6 index records
        # (each db record is generating 2 index records based on ref/alt combination)
        self.assertEqual(3, len(os.listdir(self.processing_folder)))
        first_batch_json = json.load(open(glob.glob(f"{self.processing_folder}/*_batch_0.json")[0]))
        second_batch_json = json.load(open(glob.glob(f"{self.processing_folder}/*_batch_1.json")[0]))
        third_batch_json = json.load(open(glob.glob(f"{self.processing_folder}/*_batch_2.json")[0]))
        self.assertEqual(20, first_batch_json["entry_count"])
        self.assertEqual(20, second_batch_json["entry_count"])
        self.assertEqual(6, third_batch_json["entry_count"])
        
        first_batch_json_first_entry_fields = first_batch_json["entries"][0]["fields"]
        first_batch_json_first_entry_xref = first_batch_json["entries"][0]["cross_references"]
        self.assertEqual("id", first_batch_json_first_entry_fields[0]["name"])
        self.assertEqual("rs3161500004", first_batch_json_first_entry_fields[0]["value"])

        self.assertEqual("chromosome", first_batch_json_first_entry_fields[1]["name"])
        self.assertEqual("MN908947.3", first_batch_json_first_entry_fields[1]["value"])

        self.assertEqual("start", first_batch_json_first_entry_fields[2]["name"])
        self.assertEqual(1780, first_batch_json_first_entry_fields[2]["value"])

        self.assertEqual("variant_type", first_batch_json_first_entry_fields[3]["name"])
        self.assertEqual("SNV", first_batch_json_first_entry_fields[3]["value"])

        self.assertEqual("alleles", first_batch_json_first_entry_fields[4]["name"])
        self.assertEqual("Study: PRJEB43947, Reference/Alternate: C/T", first_batch_json_first_entry_fields[4]["value"])

        first_batch_json_second_entry_fields = first_batch_json["entries"][1]["fields"]
        self.assertEqual("alleles", first_batch_json_second_entry_fields[4]["name"])
        self.assertEqual("Study: PRJEB43947, Reference/Alternate: C/A", first_batch_json_second_entry_fields[4]["value"])

        self.assertEqual(1, len(first_batch_json_first_entry_xref))
        self.assertEqual("ENA", first_batch_json_first_entry_xref[0]["dbname"])
        self.assertEqual("PRJEB43947", first_batch_json_first_entry_xref[0]["dbkey"])
