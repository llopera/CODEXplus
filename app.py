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


def main():
    smart = init_fhir_server()
    dataset_loaders = [
        WESADLoader("./datasets/WESAD", smart),
        WSPCPLoader("datasets/WSPCP", smart),
        SDNLoader("datasets/Stress-Detection-in-Nurses-main", smart),
        SRADLoader("datasets/stress-recognition-in-automobile-drivers-1.0.0", smart)
    ]

    load_static_resources(smart)
    for data_loader in dataset_loaders:
        data_loader.load_dataset()


if __name__ == '__main__':
    main()
