from connector import FHIRConnector

from fhir.resources.coding import Coding
from fhir.resources.questionnaire import Questionnaire

sssq_answers = ["Not at all", "A little bit", "Somewhat", "Very much", "Extremely"]
sssq_items = ["I was committed to attaining my performance goals",
              "I wanted to succeed on the task",
              "I was motivated to do the task",
              "I reflected about myself",
              "I was worried about what other people think of me",
              "I felt concerned about the impression I was making"]


def generate_link_id(item_number):
    return f"sssq_q{item_number+1:02}_{sssq_items[item_number]}"


def generate_item(num, item):
    q_item = {"answerOption":
                  [{"valueCoding": Coding(code=code, display=name)} for code, name in enumerate(sssq_answers)],
              "text": item,
              "linkId": generate_link_id(num),
              "type": "display"
              }
    return q_item


sssq_questionnaire = Questionnaire(
    id="SSSQ",
    status="active",
    item=[generate_item(num, item) for num, item in enumerate(sssq_items)],
)


def crate_sssq_questionnaire(server: FHIRConnector):
    server.create(sssq_questionnaire)
