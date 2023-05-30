import base64
import os
import pickle
from datetime import date

import wfdb
from fhir.resources.bodystructure import BodyStructure
from fhir.resources.deviceassociation import DeviceAssociation
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient

from loaders.loader import Loader
from resources.srad_recorder import srad_recorder
from utils import get_reference


class SRADLoader(Loader):
    def __init__(self, dataset_dir, fhir_server):
        self.body_locations = ["chest", "left shoulder", "diaphragm", "left foot", "left hand"]
        self.device_separator = "Recorder"
        study_id = "SRAD"
        title = "Detecting Stress During Real-World Driving Tasks Using Physiological Sensors"
        super().__init__(dataset_dir, fhir_server, study_id, title, "Healey and Picard", date(day=16, month=6, year=2005))

    def get_patients(self):
        with open(os.path.join(self.dataset_dir, "RECORDS")) as records:
            for record in records.readlines():
                yield Patient(id=f"{record.strip()}")

    def register_devices(self, patient):

        device, resources, channels = srad_recorder({"id": self.get_srad_recorder_id(patient)})

        device_associations = []
        for channel, body_location in zip(channels, self.body_locations):
            da = DeviceAssociation(
                **{"status": {"coding": [{"code": "completed"}]},
                   "subject": get_reference(patient),
                   "device": get_reference(device),
                   "bodyStructure": get_reference(self.device_body_structures[patient.id][body_location])
                   })
            device_associations.append(da)

        return [device], [resources], device_associations

    def get_body_structures(self, participant):
        return {"left hand":
                    BodyStructure(id=f"{self.study_id}-{participant.id}-left-hand",
                                  patient=get_reference(participant),
                                  includedStructure=[{"structure": {"coding": [{"code": "left hand"}]}}],
                                  description="Left Hand"),
                "chest":
                    BodyStructure(id=f"{self.study_id}-{participant.id}-chest",
                                  patient=get_reference(participant),
                                  includedStructure=[{"structure": {"coding": [{"code": "chest"}]}}],
                                  description="Chest"),
                "diaphragm":
                    BodyStructure(id=f"{self.study_id}-{participant.id}-diaphragm",
                                  patient=get_reference(participant),
                                  includedStructure=[{"structure": {"coding": [{"code": "diaphragm"}]}}],
                                  description="Chest around the diaphragm"),

                "left shoulder":
                    BodyStructure(id=f"{self.study_id}-{participant.id}-left-shoulder",
                                  patient=get_reference(participant),
                                  includedStructure=[{"structure": {"coding": [{"code": "left shoulder"}]}}],
                                  description="Left Shoulder"),
                "left foot":
                    BodyStructure(id=f"{self.study_id}-{participant.id}-left-foot",
                                  patient=get_reference(participant),
                                  includedStructure=[{"structure": {"coding": [{"code": "left foot"}]}}],
                                  description="Left Foot")
                }

    def read_dataset(self):
        for participant in self.patients:
            self.read_participant(participant)

        return

    def read_participant(self, participant):
        record = wfdb.rdrecord(os.path.join(self.dataset_dir, participant.id)).to_dataframe()
        observations = []
        for metric in record.columns:
            modality_df = record[metric]
            if "foot" in metric.lower():
                metric = "sc-1"

            if "hand" in metric.lower():
                metric = "sc-2"

            if "marker" in metric:
                metric = "EMG"

            if metric == "HR":
                # HR is a derived TODO
                continue

            obs = Observation(
                id=f"{self.study_id}-{participant.id}-{self.observation_idx:05}-{metric.lower()}",
                status="final",
                code={"coding": [{"code": f"drive exercise"}]},
                device={"reference": f"DeviceMetric/{self.get_srad_recorder_id(participant)}-{metric.lower()}-dm"},
                valueAttachment={
                    "contentType": "application/python-pickle",
                    "data": base64.encodebytes(pickle.dumps(modality_df)).decode("utf-8")}
            )

            observations.append(obs)

        for obs in observations:
            self.server.create(obs)

    def get_srad_recorder_id(self, participant):
        return f"{self.study_id}-{self.device_separator}-{participant.id}"
