from connector import FHIRConnector

from fhir.resources.coding import Coding
from fhir.resources.questionnaire import Questionnaire

panas_answers = ["Not at all", "A little bit", "Somewhat", "Very much", "Extremely"]
panas_items = ["Active", "Distressed", "Interested", "Inspired", "Annoyed", "Strong", "Guilty", "Scared", "Hostile",
               "Excited", "Proud", "Irritable", "Enthusiastic", "Ashamed", "Alert", "Nervous", "Determined",
               "Attentive", "Jittery", "Afraid", "Stressed", "Frustrated", "Happy", "(Angry)", "(Irritated)", "Sad" ]


def generate_link_id(item_number):
    return f"panas_q{item_number+1:02}_{panas_items[item_number]}"


def generate_item(num,item):
    q_item = {"answerOption":
                  [{"valueCoding": Coding(code=code, display=name)} for code, name in enumerate(panas_answers)],
              "text": item,
              "linkId": generate_link_id(num),
              "type": "display"
    }
    return q_item


panas_questionnaire = Questionnaire(
    id="PANAS",
    status="active",
    item=[generate_item(num, item) for num, item in enumerate(panas_items)],
)


def crate_panas_questionnaire(server: FHIRConnector):
    server.create(panas_questionnaire)
