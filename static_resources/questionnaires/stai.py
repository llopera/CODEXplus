from connector import FHIRConnector

from fhir.resources.coding import Coding
from fhir.resources.questionnaire import Questionnaire

stai_answers = ["Not at all", "A little bit", "Somewhat", "Very much", "Extremely"]
stai_items = ["I feel at ease", "I feel nervous", "I am jittery", "I am relaxed", "I am worried", "I feel pleasant"]


def generate_link_id(item_number):
    return f"stai_q{item_number+1:02}_{stai_items[item_number]}"


def generate_item(num,item):
    q_item = {"answerOption":
                  [{"valueCoding": Coding(code=code, display=name)} for code, name in enumerate(stai_answers)],
              "text": item,
              "linkId": generate_link_id(num),
              "type": "display"
    }
    return q_item


stai_questionnaire = Questionnaire(
    id="STAI",
    status="active",
    item=[generate_item(num, item) for num, item in enumerate(stai_items)],
)


def crate_stai_questionnaire(server: FHIRConnector):
    server.create(stai_questionnaire)