from abc import ABCMeta, abstractmethod

from fhir.resources.evidencereport import EvidenceReport
from fhir.resources.group import Group
from fhir.resources.practitioner import Practitioner
from fhir.resources.researchstudy import ResearchStudy

from connector import FHIRConnector
from utils import get_reference, get_list_of_references


class Loader(metaclass=ABCMeta):
    def __init__(self, dataset_dir: str, fhir_server: FHIRConnector, study_id, study_title, autor, date):
        self.date = date
        self.author = autor
        self.study_title = study_title
        self.study_id = study_id
        self.server = fhir_server
        self.dataset_dir = dataset_dir

        # Schema Components
        self.research_study = None
        self.evidence_report = None
        self.group = None
        self.patients = []

        self.device_metrics = []
        self.devices = []
        self.device_definitions = []

        self.device_body_structures = {}
        self.device_associations = {}
        self.questionnaire_responses = {}
        self.patient_observations = {}
        self.reference_observations = {}
        self.device_observations = {}
        self.estimated_observations = {}

        # Helper structures
        self.__participant_index = {}
        self.__device_index = {}
        self.__patient_devices = {}

        self.__observation_idx = 0

    def load_dataset(self):
        self.load_author()
        self.load_patients()
        self.load_body_structures()
        self.__create_patient_index()
        self.load_devices()
        self.__create_device_index()
        self.load_group()
        self.read_dataset()
        self.load_evidence_report()
        self.load_research_study()

    @property
    def observation_idx(self):
        self.__observation_idx += 1
        return self.__observation_idx - 1

    @abstractmethod
    def get_patients(self):
        pass

    @abstractmethod
    def register_devices(self, patient):
        pass

    @abstractmethod
    def get_body_structures(self, patient):
        pass

    @abstractmethod
    def read_dataset(self):
        """To avoid large object references, the implementation of `read_dataset` should directly link and send
        `Observations` and `QuestionnaireResponses to the FHIR server. In addition, this method should populate the
        following dictionaries: self.questionnaire_responses, self.patient_observations, self.reference_observations,
        self.device_observations, self.estimated_observations.

        The dictionaries follow the {patient_id: [observation_id, ...]} or
           {patient_id: [questionnaire_responses_id, ...]} pattern. In the case of self.device_observations
        """

        pass

    def load_patients(self):
        for patient in self.get_patients():
            self.patients.append(patient)
            self.init_patient_structures(patient)
            self.server.create(patient)

    def load_body_structures(self):
        for patient in self.patients:
            body_structures = self.get_body_structures(patient)
            self.device_body_structures.setdefault(patient.id, {}).update(body_structures)
            for bs in body_structures.values():
                self.server.create(bs)

    def load_devices(self):
        for patient in self.patients:
            devices, sub_devices, device_associations = self.register_devices(patient)
            self.__patient_devices[patient.id] = devices
            self.devices.extend(devices)
            self.devices.extend([sd for sds in sub_devices for sd in sds])
            self.devices.extend(device_associations)

            self.device_associations.setdefault(patient.id, []).extend([da.id for da in device_associations])

        for device in self.devices:
            self.server.create(device)

    def load_group(self):
        self.group = Group(id=f"{self.study_id}-group",
                           membership="definitional",
                           member=[{"entity": get_reference(pat)} for pat in self.patients],
                           type="person")
        self.server.create(self.group)

    def create_study_data_section(self):
        study_data = []
        for patient in self.patients:
            study_data.append(self.create_participant_section(patient.id))

        study_data_section = {"title": f"Study Data",
                              "section": study_data}

        return study_data_section

    def create_participant_section(self, participant_id):
        subsections = [
            self.create_questionnaire_section(participant_id),
            self.create_reference_data_section(participant_id),
            self.create_estimated_data_section(participant_id)
        ]
        section_entries = []
        for obs_id in self.patient_observations[participant_id]:
            section_entries.append({"reference": f"Observation/{obs_id}"})

        section = {"title": f"Participant {participant_id}",
                   "entryReference": section_entries,
                   "section": subsections}

        return section

    def create_questionnaire_section(self, participant_id):
        section_entries = []
        for ref_id in self.questionnaire_responses[participant_id]:
            section_entries.append({"reference": f"QuestionnaireResponse/{ref_id}"})

        return {"title": "Questionnaires", "entryReference": section_entries}

    def create_reference_data_section(self, participant_id):
        section_entries = []
        for obs_id in self.reference_observations[participant_id]:
            section_entries.append({"reference": f"Observation/{obs_id}"})

        return {"title": "Reference Data", "entryReference": section_entries}

    def create_device_data_section(self, participant_id, device_id):
        section_entries = []
        for obs_id in self.device_observations[participant_id][device_id]:
            section_entries.append({"reference": f"Observation/{obs_id}"})

        return {"title": f"Device {device_id}", "entryReference": section_entries}

    def create_estimated_data_section(self, participant_id):
        section_entries = []
        for obs_id in self.estimated_observations[participant_id]:
            section_entries.append({"reference": f"Observation/{obs_id}"})

        return {"title": "Estimated Data", "entryReference": section_entries}

    def create_participant_device_association_section(self, participant_id):
        section_entries = []
        for obs_id in self.device_associations[participant_id]:
            section_entries.append({"reference": f"Observation/{obs_id}"})

        return {"title": "Study devices", "entryReference": section_entries}

    def create_device_association_section(self):
        study_data = []
        for patient in self.patients:
            study_data.append(self.create_participant_device_association_section(patient.id))

        study_data_section = {"title": f"Study Data",
                              "section": study_data}

        return study_data_section

    def load_evidence_report(self):
        study_data_section = self.create_study_data_section()
        study_devices_section = self.create_device_association_section()
        self.evidence_report = EvidenceReport(id=f"{self.study_id}-results",
                                              status="active",
                                              subject={"note": [{"text": "Stress Detection"}]},
                                              section=[study_devices_section, study_data_section])
        self.server.create(self.evidence_report)

    def load_research_study(self):
        self.research_study = ResearchStudy(
            id=self.study_id,
            title=self.study_title,
            status="active",
            result=[get_reference(self.evidence_report)]
        )
        self.server.create(self.research_study)

    def load_author(self):
        self.author = Practitioner(id=f"{self.study_id}-author", name=[{
            "use": "usual", "text": self.author}])
        self.server.create(self.author)

    def get_participant(self, participant_id):
        return self.__participant_index[participant_id]

    def get_device(self, device_id):
        return self.__device_index[device_id]

    def __create_device_index(self):
        for device in self.devices:
            self.__device_index[device.id] = device

    def __create_patient_index(self):
        for patient in self.patients:
            self.__participant_index[patient.id] = patient

    def init_patient_structures(self, patient):
        self.questionnaire_responses.setdefault(patient.id, [])
        self.patient_observations.setdefault(patient.id, [])
        self.reference_observations.setdefault(patient.id, [])
        self.device_observations.setdefault(patient.id, {})
        self.estimated_observations.setdefault(patient.id, [])
