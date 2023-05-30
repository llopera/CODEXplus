from fhir.resources.devicedefinition import DeviceDefinition
from fhir.resources.fhirtypes import DeviceDefinitionHasPartType

from connector import FHIRConnector
from utils import get_list_of_references

empatica_e4_acc_definition = DeviceDefinition(
    id="EmpaticaE4Accelerometer",
    **{
        "deviceName": [{
            "name": "Accelerometer",
            "type": "user-friendly-name"
        }],
    }
)

empatica_e4_bvp_definition = DeviceDefinition(
    id="EmpaticaE4BVP",
    **{
        "deviceName": [{
            "name": "BVP",
            "type": "user-friendly-name"
        }],
    }
)

empatica_e4_eda_definition = DeviceDefinition(
    id="EmpaticaE4EDA",
    **{
        "deviceName": [{
            "name": "EDA",
            "type": "user-friendly-name"
        }],
    }
)

empatica_e4_temperature_definition = DeviceDefinition(
    id="EmpaticaE4Temperature",
    **{
        "deviceName": [{
            "name": "Temperature",
            "type": "user-friendly-name"
        }],
    }
)

empatica_e4_ibi_definition = DeviceDefinition(
    id="EmpaticaE4IBI",
    **{
        "deviceName": [{
            "name": "Inter-beat Interval",
            "type": "user-friendly-name"
        }],
    }
)

empatica_e4_hr_definition = DeviceDefinition(
    id="EmpaticaE4HR",
    **{
        "deviceName": [{
            "name": "Heart Rate",
            "type": "user-friendly-name"
        }],
    }
)

empatica_e4_tags_definition = DeviceDefinition(
    id="EmpaticaE4Tags",
    **{"deviceName": [{
        "name": "Tags",
        "type": "user-friendly-name"
    }, {
        "name": "Button Presses",
        "type": "user-friendly-name"
    }]
    }
)

empatica_e4_definition = DeviceDefinition(
    id="EmpaticaE4",
    # manufacturer="Empatica",
    modelNumber="E4",
    hasPart=[DeviceDefinitionHasPartType(reference=part) for part in get_list_of_references([empatica_e4_acc_definition,
                                    empatica_e4_bvp_definition,
                                    empatica_e4_eda_definition,
                                    empatica_e4_temperature_definition,
                                    empatica_e4_ibi_definition,
                                    empatica_e4_hr_definition,
                                    empatica_e4_tags_definition])])


def crate_empatica_definitions(server: FHIRConnector):
    for def_ in [empatica_e4_acc_definition,
                 empatica_e4_bvp_definition,
                 empatica_e4_eda_definition,
                 empatica_e4_temperature_definition,
                 empatica_e4_ibi_definition,
                 empatica_e4_hr_definition,
                 empatica_e4_tags_definition,
                 empatica_e4_definition]:
        server.create(def_)
