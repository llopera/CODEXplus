from fhir.resources.devicedefinition import DeviceDefinition
from fhir.resources.fhirtypes import DeviceDefinitionHasPartType

from connector import FHIRConnector
from utils import get_list_of_references

srad_recorder_ekg_definition = DeviceDefinition(
    id="SradRecorderEKG",
    **{
        "deviceName": [{
            "name": "Electrocardiogram",
            "type": "user-friendly-name"
        }],
    }
)

srad_recorder_emg_definition = DeviceDefinition(
    id="SradRecorderEMG",
    **{
        "deviceName": [{
            "name": "Electromyography",
            "type": "user-friendly-name"
        }],
    }
)
srad_recorder_resp_definition = DeviceDefinition(
    id="SradRecorderResp",
    **{
        "deviceName": [{
            "name": "Respiration Sensor",
            "type": "user-friendly-name"
        }],
    }
)
srad_recorder_sc_definition = DeviceDefinition(
    id="SradRecorderGSR",
    **{
        "deviceName": [{
            "name": "Skin conductivity",
            "type": "user-friendly-name"
        }],
    }
)
srad_recorder_definition = DeviceDefinition(
    id="SradRecorder",

    modelNumber="Srad",
    hasPart=[DeviceDefinitionHasPartType(reference=part) for part in get_list_of_references([
        srad_recorder_ekg_definition,
        srad_recorder_emg_definition,
        srad_recorder_resp_definition,
        srad_recorder_sc_definition,
        srad_recorder_sc_definition])])


def create_srad_recorder_definitions(server: FHIRConnector):
    for def_ in [srad_recorder_ekg_definition,
                 srad_recorder_emg_definition,
                 srad_recorder_resp_definition,
                 srad_recorder_sc_definition,
                 srad_recorder_definition
                 ]:
        server.create(def_)
