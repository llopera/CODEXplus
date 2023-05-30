from connector import FHIRConnector
from static_resources.questionnaires import panas, dim, stai, sssq

__questionnaire_directory = {
    "PANAS": panas.generate_link_id,
    "SAM": dim.generate_link_id,
    "STAI": stai.generate_link_id,
    "SSSQ": sssq.generate_link_id
}


def get_link_id(questionnaire, item):
    return __questionnaire_directory[questionnaire](item)


def get_questionnaire_url(questionnaire, connector: FHIRConnector):
    return connector.server.base_uri + f"Questionnaire/{questionnaire}"

