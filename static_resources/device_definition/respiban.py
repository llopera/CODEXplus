from fhir.resources.devicedefinition import DeviceDefinition
from fhir.resources.fhirtypes import DeviceDefinitionHasPartType

from connector import FHIRConnector
from utils import get_reference, get_list_of_references

respiban_acc_definition = DeviceDefinition(
    id="RespiBANAccelerometer",
    **{
        "deviceName": [{
            "name": "Accelerometer",
            "type": "user-friendly-name"
        }],
    }
)

respiban_pzt_definition = DeviceDefinition(
    id="RespiBANPZT",
    **{
        "deviceName": [{
            "name": "Respiration Sensor",
            "type": "user-friendly-name"
        }],
    }
)

respiban_eda_definition = DeviceDefinition(
    id="RespiBANEDA",
    **{
        "deviceName": [{
            "name": "EDA",
            "type": "user-friendly-name"
        }],
    }
)

respiban_temperature_definition = DeviceDefinition(
    id="RespiBANTemperature",
    **{
        "deviceName": [{
            "name": "Temperature",
            "type": "user-friendly-name"
        }],
    }
)

respiban_ecg_definition = DeviceDefinition(
    id="RespiBANECG",
    **{
        "deviceName": [{
            "name": "ECG",
            "type": "user-friendly-name"
        }],
    }
)

respiban_emg_definition = DeviceDefinition(
    id="RespiBANEMG",
    **{
        "deviceName": [{
            "name": "EMG",
            "type": "user-friendly-name"
        }],
    }
)

respiban_definition = DeviceDefinition(
    id="RespiBAN",
    # manufacturer="Empatica",
    modelNumber="Pro",
    hasPart=[DeviceDefinitionHasPartType(reference=part) for part in
             get_list_of_references([respiban_ecg_definition, respiban_eda_definition, respiban_emg_definition,
                                     respiban_temperature_definition, respiban_acc_definition,
                                     respiban_pzt_definition])])


def create_respiban_definitions(server: FHIRConnector):
    for def_ in [respiban_ecg_definition, respiban_eda_definition, respiban_emg_definition,
                 respiban_temperature_definition, respiban_acc_definition, respiban_pzt_definition,
                 respiban_definition]:
        server.create(def_)
