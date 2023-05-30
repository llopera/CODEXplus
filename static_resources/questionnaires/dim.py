from connector import FHIRConnector

from fhir.resources.coding import Coding
from fhir.resources.questionnaire import Questionnaire

sam_answers = ["low", " ", " ", " ", "med", " ", " ", " ", "high"]
sam_items = ["Valence", "Arousal"]


def generate_link_id(item_number):
    return f"sam_q{item_number+1:02}_{sam_items[item_number]}"


def generate_item(num, item):
    q_item = {"answerOption":
                  [{"valueCoding": Coding(code=code, display=name)} for code, name in enumerate(sam_answers)],
              "text": item,
              "linkId": generate_link_id(num),
              "type": "display"
              }
    return q_item


sam_questionnaire = Questionnaire(
    id="SAM",
    status="active",
    item=[generate_item(num, item) for num, item in enumerate(sam_items)],
)


def crate_sam_questionnaire(server: FHIRConnector):
    server.create(sam_questionnaire)