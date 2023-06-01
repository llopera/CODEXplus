import os
from urllib.parse import urlparse, unquote
from zipfile import ZipFile

import requests

from loaders import WESADLoader
from connector import FHIRConnector
from loaders.load_sdn import SDNLoader
from loaders.load_srad import SRADLoader
from loaders.load_wspcp import WSPCPLoader
from static_resources.device_definition.empatica_e4 import crate_empatica_definitions
from static_resources.device_definition.respiban import create_respiban_definitions
from static_resources.device_definition.srad_recorder import create_srad_recorder_definitions
from static_resources.questionnaires.dim import crate_sam_questionnaire
from static_resources.questionnaires.panas import crate_panas_questionnaire
from static_resources.questionnaires.sssq import crate_sssq_questionnaire
from static_resources.questionnaires.stai import crate_stai_questionnaire
from utils import get_file_name


def init_fhir_server():
    smart = FHIRConnector('http://localhost:8080/fhir')
    return smart


def load_static_resources(server):
    crate_empatica_definitions(server)
    create_respiban_definitions(server)
    create_srad_recorder_definitions(server)
    crate_panas_questionnaire(server)
    crate_stai_questionnaire(server)
    crate_sssq_questionnaire(server)
    crate_sam_questionnaire(server)


def get_datasets(datasets_base_path):
    os.makedirs(datasets_base_path, exist_ok=True)

    urls = dict(SDN=("https://datadryad.org/stash/downloads/file_stream/1022493",
                     "https://datadryad.org/stash/downloads/file_stream/1022492"),
                SRAD=("https://physionet.org/static/published-projects/" \
                      "drivedb/stress-recognition-in-automobile-drivers-1.0.0.zip",),
                WESAD=("https://uni-siegen.sciebo.de/s/HGdUkoNlW1Ub0Gx/download",),
                WSPCP=("https://physionet.org/static/published-projects/wearable-exam-stress/"
                       "a-wearable-exam-stress-dataset-for-predicting-cognitive-performance-in-real-world-settings-1.0.0.zip",))

    for dataset, url in urls.items():
        dataset_path = os.path.join(datasets_base_path, dataset)
        if not os.path.exists(dataset_path):
            print(f"Creating dataset path: {dataset_path}")
            os.mkdir(dataset_path)

        for u in url:
            r = requests.get(u, allow_redirects=True, stream=True)
            content_disposition = r.headers.get("content-disposition")
            content_type = r.headers.get("content-type")
            content_length = int(r.headers.get("content-length"))
            file_name = urlparse(r.request.url).path.split("/")[-1]
            if content_disposition is not None:
                file_name = get_file_name(content_disposition)

            file_name = os.path.join(dataset_path, f"{file_name}")
            if not os.path.exists(file_name):
                print(f"Downloading {file_name}:", end="")
                with open(file_name, "wb") as zip_file:
                    for chunk in r.iter_content(chunk_size=content_length//20):
                        zip_file.write(chunk)
                        print(".", end="")

                print()

            if content_type == "application/zip":
                tale = os.path.join(dataset_path, "unzipped")
                if os.path.exists(tale):
                    continue

                print(f"Unzipping {os.path.basename(file_name)}")
                with ZipFile(file_name) as zip_io:
                    zip_io.extractall(dataset_path)

                with open(tale, "w") as file:
                    file.write(f"{file_name}\n")


def main():
    smart = init_fhir_server()
    get_datasets("./datasets")
    dataset_loaders = [
        WESADLoader("datasets/WESAD", smart),
        WSPCPLoader("datasets/WSPCP", smart),
        SDNLoader("datasets/SDN", smart),
        SRADLoader("datasets/SRAD", smart)
    ]

    load_static_resources(smart)
    for data_loader in dataset_loaders:
        data_loader.load_dataset()


if __name__ == '__main__':
    main()
