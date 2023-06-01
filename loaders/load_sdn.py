import base64
import os.path
import datetime
import pickle
import tempfile
import pytz
import numpy as np
import pandas as pd
import scipy as scipy

from scipy.signal import find_peaks
from glob import glob
from zipfile import ZipFile

from fhir.resources.resource import Resource
from fhir.resources.bodystructure import BodyStructure
from fhir.resources.deviceassociation import DeviceAssociation
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient
from fhir.resources.period import Period
from fhir.resources.questionnaire import Questionnaire
from fhir.resources.questionnaireresponse import QuestionnaireResponse


from loaders.loader import Loader
from resources.empatica_e4 import empatica_e4, empatica_read_dataframe
from utils import get_reference, get_list_of_references


class SDNLoader(Loader):
    """Implements the loader abstract class to load the stress detection in Nurses (SDN)"""

    def __init__(self, dataset_dir, fhir_server):
        self.device_separator = "E4"
        study_title = "Stress Detection in Nurses"
        study_id = "SDN"
        autor = "Hosseini et al."
        date = "06.2022"
        super().__init__(dataset_dir, fhir_server, study_id, study_title, autor, date)

        self.survey_results_file_name = "SurveyResults.xlsx"
        self.survey_results_sheet = "in"
        self.sensor_data_folder = "Stress_dataset"
        self.survey = self.load_survey_results()
        self.load_questionnaire()

        # Items necessary to compute extracted features. This is part of the information contained in the
        # jupyter notebook available in the dataset's code repository in GitHub.

        self.rolling_window_size = 40
        self.feature_columns = [
            'EDA_Mean', 'EDA_Min', 'EDA_Max', 'EDA_Std',
            'EDA_Kurtosis', 'EDA_Skew', 'EDA_Num_Peaks', 'EDA_Amplitude', 'EDA_Duration',
            'HR_Mean', 'HR_Min', 'HR_Max', 'HR_Std', 'HR_RMS',
            'TEMP_Mean', 'TEMP_Min', 'TEMP_Max', 'TEMP_Std'
        ]

    def generate_item_linkId(self, num):
        return f"{self.study_id}-questionnaire-{num + 1:02}"

    def generate_item(self, num, item):
        q_item = {"answerOption":
                      [{"valueInteger": 0}, {"valueInteger": 1}, {"valueString": "na."}],
                  "text": item,
                  "linkId": self.generate_item_linkId(num),
                  "type": "display"
                  }

        return q_item

    def get_question_headers(self):
        for num, item in enumerate(self.survey["COVID":]):
            yield num, item

    def get_questionnaire_id(self):
        return f"{self.study_id}-stress-entry-qualifier"

    def get_questionnaire_reference(self):
        return f"Questionnaire/{self.get_questionnaire_id()}"

    def load_questionnaire(self):
        study_prerequisites = Questionnaire(
            id=self.get_questionnaire_id(),
            status="active",
            item=[self.generate_item(num, item) for num, item in self.get_question_headers()],
        )

        self.server.create(study_prerequisites)

    def load_survey_results(self):
        survey = pd.read_excel(os.path.join(self.dataset_dir, self.survey_results_file_name), dtype={"ID": str},
                               sheet_name=self.survey_results_sheet).set_index("ID", append=True)
        survey.loc[:, ["Start time", "End time"]] = (survey.loc[:, ["Start time", "End time"]]
                                                     .applymap(datetime.time.isoformat)
                                                     .apply(pd.to_timedelta))
        survey["Start time"] = pd.DatetimeIndex(survey["Start time"] + survey["date"], tz="US/Central")
        survey["End time"] = pd.DatetimeIndex(survey["End time"] + survey["date"], tz="US/Central")
        return survey

    def get_patients(self):
        for patient in next(os.walk(self.dataset_dir))[1]:
            yield Patient(id=f"SDN-{os.path.basename(patient)}")

    def get_empatica_id(self, participant):
        return f"{self.study_id}-{self.device_separator}-{participant.id}"

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

    def read_participant(self, participant):
        for label, sensor_data, questionnaire in self.get_participant_logs(participant):
            observations = self.encode_observation_data(sensor_data, participant)
            (self.device_observations
                .setdefault(participant.id, {})
                .setdefault(self.get_empatica_id(participant), [])
                .extend([o.id for o in observations]))

            questionnaire_response = self.encode_questionnaire_responses(questionnaire, participant)
            self.questionnaire_responses.setdefault(participant.id, []).append([qr.id for qr in questionnaire_response])
            self.upload_data(observations, questionnaire_response)

            estimated_observations = self.compute_features(sensor_data, participant)
            self.estimated_observations.setdefault(participant.id, []).extend([o.id for o in estimated_observations])
            self.link_derived_from(estimated_observations, observations)
            self.upload_data(estimated_observations)

            reference = self.encode_label(label, participant)
            self.reference_observations.setdefault(participant.id, []).append(reference)
            self.link_has_member(reference, observations, questionnaire_response)
            self.upload_data(reference)

            self.link_part_of(reference, questionnaire_response)
            self.upload_data(questionnaire_response)

    def upload_data(self, *data):
        for data_ in data:
            if isinstance(data_, Resource):
                self.server.create(data_)

            else:
                for item_ in data_:
                    self.server.create(item_)

    def get_participant_logs(self, participant):
        data_folder_id = participant.id[-2:]
        data_folder = os.path.join(self.dataset_dir, data_folder_id, "*")
        for zip_file in glob(data_folder):
            date_time = datetime.datetime.fromtimestamp(int(os.path.basename(zip_file)[3:-4]),
                                                        tz=pytz.timezone("US/Central"))
            with ZipFile(zip_file) as zip_io:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_io.extractall(temp_dir)
                    modalities = empatica_read_dataframe(temp_dir, tz="US/Central")
                    for label, sensor_data, questionnaires in self.synchronize_labels_and_sensors(modalities,
                                                                                                  data_folder_id):
                        yield label, sensor_data, questionnaires

    def synchronize_labels_and_sensors(self, modalities, participant_dir):
        labels = self.survey.loc[(slice(None), participant_dir), :]
        chunk_ids = set()
        for mod_name, mod_values in modalities.items():
            if len(mod_values) == 0:
                continue

            mod_values["label"] = -1
            start_time = mod_values.index[0]
            end_time = mod_values.index[-1]
            applicable_labels = (labels["Start time"] > start_time) & (labels["Start time"] < end_time)
            for idx, start, end in labels.loc[applicable_labels, ["Start time", "End time"]].itertuples():
                mod_values.loc[start:end, "label"] = idx[0]

            mod_values["chunk"] = (mod_values["label"].diff().fillna(0) != 0).cumsum()
            chunk_ids.update(mod_values["chunk"])

        for chunk_id in chunk_ids:
            sensor_data = {}
            chunk_label_idx = set()
            start_time = datetime.datetime.now(tz=pytz.timezone("US/Central"))
            end_time = pd.Timestamp(0, tz=pytz.timezone("US/Central"))
            for mod_name, mod_values in modalities.items():
                if len(mod_values) == 0:
                    sensor_data[mod_name] = mod_values
                    continue

                indexer = mod_values["chunk"] == chunk_id
                if not indexer.any():
                    continue

                sensor_data[mod_name] = mod_values[indexer].drop(["label", "chunk"], axis=1)
                chunk_label_idx.update(mod_values[indexer]["label"])
                start_time = min(mod_values[indexer].index[0], start_time)
                end_time = max(mod_values[indexer].index[-1], end_time)

            chunk_label_idx = chunk_label_idx.pop()
            label = {"start_time": start_time, "end_time": end_time, "value": -1}
            if chunk_label_idx == -1:
                yield label, sensor_data, []

            else:
                label["value"] = labels.loc[(chunk_label_idx, participant_dir), "Stress level"]
                questions = labels.loc[(chunk_label_idx, participant_dir), "COVID related":]
                yield label, sensor_data, questions

    def encode_observation_data(self, sensor_data, participant, is_device=True):
        observations = []
        for metric, data in sensor_data.items():
            if len(data) == 0:
                continue

            if isinstance(metric, tuple):
                metric = "-".join(metric)
                metric = metric.replace("_", "-")

            obs = Observation(
                    id=f"{participant.id}-E4-{metric.lower()}-{self.observation_idx:05d}",  # participant.id includes study_id
                    status="final",
                    effectivePeriod=Period(start=data.index[0], end=data.index[-1]),
                    code={"coding": [{"code": f"{metric}"}]},
                    # device={"reference": f"DeviceMetric/{self.study_id}-E4-{participant.id}-{metric.lower()}-dm"},
                    valueAttachment={
                        "contentType": "application/python-pickle",
                        "data": base64.encodebytes(pickle.dumps(data)).decode("utf-8")}
                )

            if is_device:
                obs.device = {"reference": f"DeviceMetric/{self.study_id}-E4-{participant.id}-{metric.lower()}-dm"}

            observations.append(obs)
        return observations

    def encode_questionnaire_responses(self, questionnaire, participant):
        if len(questionnaire) == 0:
            return []

        responses = []
        for q_id, answer in enumerate(questionnaire):
            stuqr = QuestionnaireResponse(
                id=f"{self.study_id}-{participant.id}-{self.observation_idx:05}-qr",
                questionnaire=self.get_questionnaire_reference(),
                status="completed",
                source=get_reference(participant),
                item=[{
                    "linkId": self.generate_item_linkId(q_id),
                    "answer": [{"valueString": answer}]}
                ])

            responses.append(stuqr)

        return responses

    def get_body_structures(self, participant):
        return {"dominant hand":
                    BodyStructure(id=f"{self.study_id}-{participant.id}-dominant-wrist",
                                  patient=get_reference(participant),
                                  includedStructure=[{"structure": {"coding": [{"code": "Dominant Wrist"}]}}],
                                  description="Dominant wrist")}

    def compute_features(self, sensor_data, participant):
        features = pd.concat(sensor_data, axis=1).loc[:, ["EDA", "TEMP", "HR"]]
        features.columns = features.columns.droplevel(1)
        features_selector = ~features.isnull().any(axis=1)
        features = features[features_selector]

        new_features = features.loc[:, ["TEMP", "HR"]].rolling(self.rolling_window_size).agg([
            np.amin,
            np.amax,
            np.mean,
            np.std, ])

        __peaks_cache = {}

        def num_peaks(arr):
            peaks, properties = find_peaks(arr, width=5)
            __peaks_cache.update(properties)
            return len(peaks)

        def amplitude(arr):
            prominences = np.array(__peaks_cache['prominences'])
            amplitude = np.sum(prominences)
            return amplitude

        def duration(arr):
            widths = np.array(__peaks_cache['widths'])
            duration = np.sum(widths)
            return duration

        eda_features = features.loc[:, ["EDA"]].rolling(self.rolling_window_size).agg([
            np.amin,
            np.amax,
            np.mean,
            np.std,
            scipy.stats.kurtosis,
            scipy.stats.skew,
            num_peaks,
            amplitude,
            duration
        ])

        features = pd.concat([eda_features, new_features], axis=1)

        lag_features = pd.concat([features.loc[:, (slice(None), "mean")].copy().shift(i+1) for i in range(10)], axis=1,
                                 keys=[f"shifted_mean_{i:02}" for i in range(10)])
        lag_features.columns = lag_features.columns.droplevel(2).swaplevel(0, 1)

        features = pd.concat([features, lag_features], axis=1)
        return self.encode_observation_data(features, participant, is_device=False)

    def link_derived_from(self, estimated_observations, observations):
        modality_dict = {o.id.split("-")[-2]:o for o in observations}

        for observation in estimated_observations:
            e4_marker = observation.id.index(self.device_separator, len(self.study_id) + 2)
            modality = observation.id[e4_marker+3:].split("-")[0]
            base_observation = modality_dict[modality]
            observation.derivedFrom = [get_reference(base_observation)]

    def encode_label(self, label, participant):
        label_observation = Observation(
                    id=f"{self.study_id}-{participant.id}-{self.observation_idx:05}",
                    status="final",
                    code={"coding": [{"code": f"stress"}]},
                    valueString=str(label["value"]),
                    effectivePeriod=Period(start=label["start_time"], end=label["end_time"]),
                    subject=get_reference(participant))

        return label_observation

    @staticmethod
    def link_has_member(reference, observations, questionnaire_response):
        reference.hasMember = []
        reference.hasMember.extend(get_list_of_references(observations))
        reference.hasMember.extend(get_list_of_references(questionnaire_response))

    @staticmethod
    def link_part_of(reference, questionnaire_response):
        for qr in questionnaire_response:
            qr.partOf = [get_reference(reference)]





