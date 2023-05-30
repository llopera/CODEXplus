import base64
import os
import pickle
from datetime import datetime, date
from glob import glob

import pandas as pd
from fhir.resources.bodystructure import BodyStructure
from fhir.resources.deviceassociation import DeviceAssociation
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient

from loaders.loader import Loader
from resources.empatica_e4 import empatica_e4
from utils import get_reference, get_list_of_references


class WSPCPLoader(Loader):
    """Implements the Loader abstract class to load the WSPCP dataset."""

    def __init__(self, dataset_dir, fhir_server):
        title = "Wearable Stress and Affect Detection"
        study_id = "WSPCPL"
        super().__init__(dataset_dir, fhir_server, study_id, title, "Rafiul et al.",
                         date(day=10, month=3, year=2022))

        self.exams = ["Final", "Midterm 1", "Midterm 2"]
        self.grades = {}
        self.load_grades()

    def load_grades(self):
        """Source StudentGrades.txt"""
        self.grades.update({
            "Midterm 1": dict(
                S1=.78, S2=.82, S3=.77, S4=.75, S5=.67, S6=.71, S7=.64, S8=.92, S9=.80, S10=.89),
            "Midterm 2": dict(
                S1=.82, S2=.85, S3=.90, S4=.77, S5=.77, S6=.64, S7=.33, S8=.88, S9=.39, S10=.64),
            "Final": dict(
                S1=182/200, S2=180/200, S3=188/200, S4=149/200, S5=157/200, S6=175/200,
                S7=110/200, S8=184/200, S9=126/200, S10=116/200)})

    def get_patients(self):
        cd, patients, files_ = next(os.walk(f"{self.dataset_dir}/Data"))
        for patient_id in patients:
            patient = Patient(id=patient_id)
            yield patient

    def get_empatica_id(self, participant):
        return f"{self.study_id}-E4-{participant.id}"

    def register_devices(self, patient):
        device, resources = empatica_e4({"id": self.get_empatica_id(patient)})
        device_association = DeviceAssociation(
            **{"status": {"coding": [{"code": "completed"}]},
               "subject": get_reference(patient),
               "device": get_reference(device),
               "bodyStructure": get_reference(self.device_body_structures[patient.id]["dominant hand"])
               })

        return [device], [resources], [device_association]

    def read_dataset(self):
        for participant in self.patients:
            self.read_participant(participant)

        return

    def get_body_structures(self, participant):
        return {"dominant hand":
                    BodyStructure(id=f"{self.study_id}-{participant.id}-dominant-wrist",
                                  patient=get_reference(participant),
                                  includedStructure=[{"structure": {"coding": [{"code": "Dominant Wrist"}]}}],
                                  description="Dominant wrist")}

    def read_participant(self, participant):
        for exam in self.exams:
            observation_members = []
            modalities = glob(f"{self.dataset_dir}/Data/{participant.id}/{exam}/*.csv")
            for modality_path in modalities:
                metric = os.path.basename(modality_path)[:-4]
                try:
                    data = pd.read_csv(modality_path, header=None)
                except pd.errors.EmptyDataError:
                    continue

                if metric == "tags":
                    for idx, timestamp in pd.to_datetime(data[0]).items():
                          observation_members.append(Observation(
                            id=f"{self.study_id}-{participant.id}-{exam.replace(' ','-')}-E4-{metric.lower()}-{idx:04}",
                            status="final",
                            effectiveDateTime=timestamp,
                            code={"coding": [{"code": f"{exam}"}]},
                            valueBoolean=True,
                            device={"reference": f"DeviceMetric/{self.study_id}-E4-{participant.id}-{metric.lower()}-dm"},
                          ))

                    continue

                timestamp = data.iloc[0, 0]
                if metric == "IBI":
                    data = data.iloc[1:, :]

                else:
                    data = data.iloc[2:, :]

                observation_members.append(Observation(
                    id=f"{self.study_id}-{participant.id}-{exam.replace(' ','-')}-E4-{metric.lower()}",
                    status="final",
                    effectiveDateTime=timestamp,
                    code={"coding": [{"code": f"{exam}"},
                                     {"code": f"{self.grades[exam][participant.id]}"}
                                     ]},
                    device={"reference": f"DeviceMetric/{self.study_id}-E4-{participant.id}-{metric.lower()}-dm"},
                    valueAttachment={
                        "contentType": "application/python-pickle",
                        "data": base64.encodebytes(pickle.dumps(data)).decode("utf-8")}
                ))

            parent_ = Observation(
                id=f"{participant.id}-{exam.replace(' ', '-')}",
                status="final",
                code={"coding": [{"code": f"{exam}"}]},
                valueQuantity={"value": self.grades[exam][participant.id], "unit": "percentage"},
                hasMember=get_list_of_references(observation_members),
                subject=get_reference(participant))

            for obs in observation_members:
                self.device_observations[participant.id].setdefault(self.get_empatica_id(participant), []).append(obs.id)
                self.server.create(obs)

            self.reference_observations[participant.id].append(parent_.id)
            self.server.create(parent_)







