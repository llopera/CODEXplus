import base64
import os
import pickle
import re
from collections import OrderedDict
from datetime import date

import numpy as np
from fhir.resources.bodystructure import BodyStructure
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.deviceassociation import DeviceAssociation
from fhir.resources.narrative import Narrative

from fhir.resources.observation import Observation
from fhir.resources.patient import Patient
from fhir.resources.quantity import Quantity
from fhir.resources.questionnaire import Questionnaire
from fhir.resources.questionnaireresponse import QuestionnaireResponse
from fhir.resources.range import Range

from loaders.loader import Loader
from resources.empatica_e4 import empatica_e4
from resources.respiban_pro import respiban_pro
from static_resources.questionnaires import get_link_id, get_questionnaire_url
from utils import get_reference, get_list_of_references


def generate_item(num, item):
    q_item = {"answerOption":
                  [{"valueString": "YES"}, {"valueString": "NO"}],
              "text": item,
              "linkId": f"WASAD-study-prerequisite-question-{num + 1:02}",
              "type": "display"
              }

    return q_item


class WESADLoader(Loader):
    """Implements the Loader abstract class to load the WESAD dataset."""

    def __init__(self, dataset_dir, fhir_server):
        study_id = "WESAD"
        title = "Wearable Stress and Affect Detection"
        super().__init__(dataset_dir, fhir_server, study_id, title, "Schmidt et al.", date(day=16, month=10, year=2018))

        self.sessions = {}
        self.questionnaires = ["PANAS", "SAM", "STAI", "SSSQ"]
        self.stress_session_label = "stress"
        self.label_codes = {
            0: "not defined / transient",
            1: "baseline",
            2: "stress",
            3: "amusement",
            4: "meditation",
            5: "ignore-1",
            6: "ignore-2",
            7: "ignore-3"
        }

        self.signal_freq = {
            "bvp": 64,
            "acc": 32,
            "eda": 4,
            "temp": 4,
        }

        self.session_times = {}
        self.transient_session = {}
        self.label_f = 700
        self.participant_data = None

        self.prerequisite_questions = [
            "Did you drink coffee today?",
            "Did you drink coffee within the last hour?",
            "Did you do any sports today?",
            "Are you a smoker?",
            "Did you smoke within the last hour?",
            "Do you feel ill today?"
        ]
        self.load_study_prerequisites_questionnaire()



    def resample_labels(self, labels, metric):
        idx = np.round(np.arange(0, len(labels) * 1 / self.label_f, 1 / self.signal_freq[metric.lower()]) / (
                1 / self.label_f)).astype(int)
        return labels[idx]

    def resample_indices_range(self, range, metric):
        low, high = range
        low = int((low / self.label_f) * self.signal_freq[metric.lower()])
        high = int((high / self.label_f) * self.signal_freq[metric.lower()])

        return low, high

    def read_dataset(self):
        for participant in self.patients:
            self.read_participant(participant)

        return

    def read_participant(self, participant):
        self.load_readme_file(participant)
        self.load_sessions(participant)
        for questionnaire in self.questionnaires:
            self.load_questionnaire_answers(questionnaire, participant)

        self.participant_data = pickle.load(open(f"{self.dataset_dir}/{participant.id}/{participant.id}.pkl", "br"),
                                            encoding='latin1')

        current_session = self.transient_session[participant.id]
        session_times = self.session_times[participant.id]
        sessions = iter(self.sessions[participant.id])
        for block in zip(session_times[:-1], session_times[1:]):
            label = self.participant_data["label"][slice(*block)]
            label_blocks = np.concatenate(([0], np.abs(np.diff(label)).cumsum()))
            block_ids = set(label_blocks)
            for bid in block_ids:
                observation_members = []
                observation_members.extend(
                    self.load_empatica_observations(block, bid, label, label_blocks, participant))

                selector = (label_blocks == bid)
                observation_members.extend(self.read_raspiban_observations(block, label, participant, selector))

                parent_ = Observation(
                    id=f"WESAD-{participant.id}-{self.observation_idx:05}",
                    status="final",
                    code={"coding": [{"code": f"{self.label_codes[label[selector][0]]}"}]},
                    valueInteger=label[selector][0],
                    hasMember=get_list_of_references(observation_members),
                    subject=get_reference(participant))

                self.reference_observations[participant.id].append(parent_.id)
                current_session.hasMember.append(get_reference(parent_))

                for obs in observation_members:
                    self.server.create(obs)

                self.server.create(parent_)

            if current_session == self.transient_session[participant.id]:
                current_session = self.sessions[participant.id][next(sessions)]
            else:
                current_session = self.transient_session[participant.id]

        self.load_session_observations(participant)

    def read_raspiban_observations(self, block, label, participant, selector):
        observation_members = []
        respiban_data = self.participant_data["signal"]["chest"]
        device_data = self.device_observations[participant.id][self.get_respiban_id(participant.id)] = []
        for metric in respiban_data.keys():
            data = respiban_data[metric][slice(*block)]
            obs = Observation(
                id=f"WESAD-{participant.id}-{self.observation_idx:05}-RespiBAN-{metric.lower()}",
                status="final",
                code={"coding": [{"code": f"{self.label_codes[label[selector][0]]}"}]},
                device={"reference": f"DeviceMetric/WESAD-RespiBAN-{participant.id}-{metric.lower()}-dm"},
                valueAttachment={
                    "contentType": "application/python-pickle",
                    "data": base64.encodebytes(pickle.dumps(data[selector, :])).decode("utf-8")}
            )
            observation_members.append(obs)
            device_data.append(obs.id)
        return observation_members

    def load_empatica_observations(self, block, bid, label, label_blocks, participant):
        observation_members = []
        empatica_data = self.participant_data["signal"]["wrist"]
        device_data = (self.device_observations
                       .setdefault(participant.id, {})
                       .setdefault(self.get_empatica_id(participant.id), []))
        for metric in empatica_data.keys():
            resampled_block = self.resample_indices_range(block, metric)
            data = empatica_data[metric][slice(*resampled_block)]

            resampled_labels = self.resample_labels(label, metric)
            resampled_blocks = self.resample_labels(label_blocks, metric)
            selector = (resampled_blocks == bid)

            obs = Observation(
                id=f"WESAD-{participant.id}-{self.observation_idx:05}-E4-{metric.lower()}",
                status="final",
                code={"coding": [{"code": f"{self.label_codes[resampled_labels[selector][0]]}"}]},
                device={"reference": f"DeviceMetric/WESAD-E4-{participant.id}-{metric.lower()}-dm"},
                valueAttachment={
                    "contentType": "application/python-pickle",
                    "data": base64.encodebytes(pickle.dumps(data[selector, :])).decode("utf-8")}
            )
            observation_members.append(obs)
            device_data.append(obs.id)
        return observation_members

    def get_patients(self):
        cd, participants, files_ = next(os.walk(self.dataset_dir))
        for participant_id in participants:
            participant = Patient(id=participant_id,
                                  )
            yield participant

    def register_devices(self, participant):
        devices = []
        sub_devices = []
        device_associations = []
        device, resources = empatica_e4({"id": self.get_empatica_id(participant.id)})
        device_associations.append(DeviceAssociation(
            **{"status": {"coding": [{"code": "completed"}]},
               "subject": get_reference(participant),
               "device": get_reference(device),
               "bodyStructure": get_reference(self.device_body_structures[participant.id]["dominant hand"])
               }))

        devices.append(device)
        sub_devices.append(resources)

        device, resources = respiban_pro({"id": self.get_respiban_id(participant.id)})
        device_associations.append(DeviceAssociation(
            **{"status": {"coding": [{"code": "completed"}]},
               "subject": get_reference(participant),
               "device": get_reference(device),
               "bodyStructure": get_reference(self.device_body_structures[participant.id]["chest"])
               }))

        devices.append(device)
        sub_devices.append(resources)

        return devices, sub_devices, device_associations

    def get_body_structures(self, participant):
        return {"dominant hand":
                    BodyStructure(id=f"{self.study_id}-{participant.id}-dominant-wrist",
                                  patient=get_reference(participant),
                                  includedStructure=[{"structure": {"coding": [{"code": "Dominant Wrist"}]}}],
                                  description="Dominant wrist"),
                "chest":
                    BodyStructure(id=f"{self.study_id}-{participant.id}-chest",
                                  patient=get_reference(participant),
                                  includedStructure=[{"structure": {"coding": [{"code": "chest"}]}}],
                                  description="Chest")
                }

    def get_empatica_id(self, participant_id):
        return f"{self.study_id}-E4-{participant_id}"

    def get_respiban_id(self, participant_id):
        return f"{self.study_id}-RespiBAN-{participant_id}"

    def load_questionnaire_answers(self, questionnaire, participant):
        questionnaire_lines = self.__read_participant_answers_from_file(participant, questionnaire)
        sessions = self.sessions[participant.id].keys()
        for session, q_line in zip(sessions, questionnaire_lines):
            if questionnaire == "sssq":
                """Unlike other questionnaires, SSSQ is only administered once after the stress session."""
                session = self.stress_session_label

            session_observation = self.sessions[participant.id][session]
            answers = []
            for item, c in enumerate(q_line.split(";")[1:-1]):
                try:
                    int(c)
                except ValueError:
                    if c == "":
                        continue

                    print(f"Inconsistent answer {c} to question {item} from {questionnaire} questionnaie ")
                    continue

                if questionnaire == "PANAS" and session != self.stress_session_label and item == 23:
                    """Correct Item ID since 23 and 24 are only asked during stress conditions"""
                    item += 2

                qr = QuestionnaireResponse(
                    id=f"WESAD-{participant.id}-{self.observation_idx:05}-questionnaire-response",
                    questionnaire=get_questionnaire_url(questionnaire, self.server),
                    status="completed",
                    source=get_reference(participant),
                    partOf=[get_reference(session_observation)],
                    item=[{
                        "linkId": get_link_id(questionnaire, item),
                        "answer": [{"valueCoding": Coding(code=int(c))}]}
                    ])

                session_observation.hasMember.append(get_reference(qr))
                self.questionnaire_responses[participant.id].append(qr.id)
                self.server.create(qr)

    def __read_participant_answers_from_file(self, participant, questionnaire):
        file_name = os.path.join(self.dataset_dir, participant.id, f"{participant.id}_quest.csv")
        questionnaire_lines = []
        with open(file_name) as answers_file:
            for line in answers_file:
                if questionnaire not in line:
                    continue

                questionnaire_lines.append(line)
        return questionnaire_lines

    def load_sessions(self, participant):
        def convert_times(time):
            if "." in time:
                minutes, seconds = time.split(".")
            else:
                minutes, seconds = time, "0"

            seconds = int(minutes) * 60 + int(seconds)
            return Quantity(value=700 * seconds, unit="1/700 s")

        file_name = os.path.join(self.dataset_dir, participant.id, f"{participant.id}_quest.csv")
        with open(file_name) as answers_file:
            lines = answers_file.readlines()[:4]

        sessions = lines[1].split(";")[1:6]
        starts = [convert_times(item) for item in lines[2].split(";")[1:6]]
        ends = [convert_times(item) for item in lines[3].split(";")[1:6]]
        self.transient_session[participant.id] = Observation(
            status="final",
            id=f"WESAD-{participant.id}-TRANSIENT",
            hasMember=[],
            code=CodeableConcept(coding=[Coding(code="transient", display="transient")],
                                 text=f"Session name: Transient"),
            text=Narrative(status="generated",
                           div=f"Theis session catches all observations that are between actual sessions"),
        )
        self.reference_observations.setdefault(participant.id, []).append(self.transient_session[participant.id].id)

        for session, start, end in zip(sessions, starts, ends):
            session_dic = self.sessions.setdefault(participant.id, OrderedDict())
            session_dic[session] = Observation(
                status="final",
                id=f"WESAD-{participant.id}-{session.replace(' ', '-').upper()}",
                hasMember=[],
                code=CodeableConcept(coding=[Coding(code=session, display=session)], text=f"Session name: {session}"),
                text=Narrative(status="generated",
                               div=f"The session {session} duration, expressed as the start and end time in reference "
                                   "to the beginning of the recording, has been encoded as a Range rather than a "
                                   "Period.  The range values are converted form the original minute.seconds to the "
                                   "corresponding index position of the 700Hz resampled vectors."),
                valueRange=Range(low=start, high=end)
            )
            self.session_times.setdefault(participant.id, [0]).extend([int(start.value), int(end.value)])

        self.reference_observations.setdefault(participant.id, []).extend(
            [ses.id for ses in self.sessions[participant.id].values()])
        self.load_session_observations(participant)

    def load_session_observations(self, participant):
        self.server.create(self.transient_session[participant.id])
        for session_observation in self.sessions[participant.id].values():
            self.server.create(session_observation)

    def load_study_prerequisites_questionnaire(self):
        study_prerequisites = Questionnaire(
            id="WASAD-study-prerequisites",
            status="active",
            item=[generate_item(num, item) for num, item in enumerate(self.prerequisite_questions)],
        )

        self.server.create(study_prerequisites)

    def load_readme_file(self, participant):
        personal_information, study_pre_requisites, additional_notes = self.parse_readme_file(participant)
        self.load_personal_information(participant, personal_information)
        self.load_study_prerequisites_questionnaire_responses(participant, study_pre_requisites)
        self.load_additional_notes(participant, additional_notes)

    def parse_readme_file(self, participant):
        filename = f"{self.dataset_dir}/{participant.id}/{participant.id}_readme.txt"
        personal_information = []
        study_pre_requisites = []
        additional_notes = []
        current_list = personal_information
        with open(filename) as readme_file:
            for line in readme_file:
                if "Personal" in line:
                    current_list = personal_information
                    continue

                if "Study" in line:
                    current_list = study_pre_requisites
                    continue

                if "Additional" in line:
                    current_list = additional_notes
                    continue

                if line.strip() == "":
                    continue

                current_list.append(line)

        return personal_information, study_pre_requisites, additional_notes

    def load_personal_information(self, participant, personal_information):
        codings = {
            "Age": {"code": "30525",
                    "system": "https://loinc.org",
                    "display": "Age"},
            "Height": {"code": "8303-0",
                       "system": "https://loinc.org",
                       "display": "Body height"},
            "Weight": {"code": "3142-7-0",
                       "system": "https://loinc.org",
                       "display": "Body weight stated"},
            "Gender": {"code": "72143-1",
                       "system": "https://loinc.org",
                       "display": "Sex"},
            "Dominant hand": {"code": "66042-3",
                              "system": "https://loinc.org",
                              "display": "Dominant hand"},
        }
        value_types = {
            "Age": "valueQuantity",
            "Height": "valueQuantity",
            "Weight": "valueQuantity",
            "Gender": "valueString",
            "Dominant hand": "valueString"}

        value_units = {
            "Age": "years"
        }

        for info_line in personal_information:
            key, unit, value = re.match(r"([a-zA-Z ]*)(|[()a-z]*): ([a-zA-Z\d.]*)", info_line).groups()
            key = key.strip()
            value_type = value_types[key]
            value = Quantity(value=value, unit=value_units.get(key, unit)) if value_type == "valueQuantity" else value
            obs = Observation(
                id=f"WESAD-{participant.id}-{self.observation_idx:05}",
                status="final",
                code={"coding": [codings[key]]},
                subject=get_reference(participant),
                **{value_types[key]: value}
            )

            self.patient_observations[participant.id].append(obs.id)
            self.server.create(obs)

    def load_study_prerequisites_questionnaire_responses(self, participant, study_pre_requisites):
        for question_line in study_pre_requisites:
            question, answer = re.match(r"([a-zA-Z\s]*\?)\s*([a-zA-Z]*)", question_line).groups()
            question_id = self.prerequisite_questions.index(question)

            stuqr = QuestionnaireResponse(
                id=f"WESAD-{participant.id}-{self.observation_idx:05}-study-prerequisite",
                questionnaire="Questionnaire/WASAD-study-prerequisites",
                status="completed",
                source=get_reference(participant),
                item=[{
                    "linkId": f"WASAD-study-prerequisite-question-{question_id + 1:02}",
                    "answer": [{"valueString": answer}]}
                ])

            self.patient_observations[participant.id].append(stuqr.id)
            self.server.create(stuqr)

    def load_additional_notes(self, participant, additional_notes):
        obs = Observation(
            id=f"WESAD-{participant.id}-{self.observation_idx:05}",
            status="final",
            code={"coding": [{"code": "48767-8",
                              "system": "https://loinc.org",
                              "display": "Annotation"}]},
            subject=get_reference(participant),
            valueString="".join(additional_notes)
        )
        self.patient_observations[participant.id].append(obs.id)
        self.server.create(obs)
