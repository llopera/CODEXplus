from fhir.resources.device import Device
from fhir.resources.devicemetric import DeviceMetric

from static_resources.device_definition.respiban import respiban_definition, respiban_acc_definition, \
    respiban_pzt_definition, respiban_eda_definition, respiban_temperature_definition, respiban_ecg_definition, \
    respiban_emg_definition
from utils import get_reference, get_codeable_reference


def respiban_pro(device_properties=None, acc_props=None, pzt_props=None, eda_props=None, temp_props=None,
             emg_props=None, ecg_props=None):
    defaults_ = {"status": "active",
                 "definition": get_codeable_reference(respiban_definition),
                 }

    # Initialize parameters
    acc_props = acc_props if acc_props is not None else {}
    pzt_props = pzt_props if pzt_props is not None else {}
    eda_props = eda_props if eda_props is not None else {}
    temp_props = temp_props if temp_props is not None else {}
    emg_props = emg_props if emg_props is not None else {}
    ecg_props = ecg_props if ecg_props is not None else {}
    defaults_.update(device_properties)
    respiban = Device(**defaults_)
    resources = []

    __create_accelerometer(acc_props, respiban, resources)
    __create_pzt(pzt_props, respiban, resources)
    __create_eda(eda_props, respiban, resources)
    __create_temperature(temp_props, respiban, resources)
    __create_ecg(ecg_props, respiban, resources)
    __create_emg(emg_props, respiban, resources)
    
    return respiban, resources


def __create_pzt(pzt_props, respiban, resources):
    pzt_props_ = {
        "id": f"{respiban.id}-resp",
        "status": "active",
        "definition": get_codeable_reference(respiban_pzt_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 700, "unit": "Hz"}}
        ]
    }
    pzt_props_.update(pzt_props)
    pzt_device = __respiban_modality(respiban, **pzt_props_)
    pzt_device_metric = DeviceMetric(id=f"{pzt_device.id}-dm",
                                     device=get_reference(pzt_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "%"}]},
                                     type={"coding": [{"code": "Respiration"}]}
                                     )
    resources.extend([pzt_device, pzt_device_metric])


def __create_eda(eda_props, respiban, resources):
    eda_props_ = {
        "id": f"{respiban.id}-eda",
        "status": "active",
        "definition": get_codeable_reference(respiban_eda_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 700, "unit": "Hz"}}
        ]
    }
    eda_props_.update(eda_props)
    eda_device = __respiban_modality(respiban, **eda_props_)
    eda_device_metric = DeviceMetric(id=f"{eda_device.id}-dm",
                                     device=get_reference(eda_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "µS"}]},
                                     type={"coding": [{"code": "Electrodermal Activity"}]}
                                     )
    resources.extend([eda_device, eda_device_metric])
    

def __create_ecg(ecg_props, respiban, resources):
    ecg_props_ = {
        "id": f"{respiban.id}-ecg",
        "status": "active",
        "definition": get_codeable_reference(respiban_ecg_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 700, "unit": "Hz"}}
        ]
    }
    ecg_props_.update(ecg_props)
    ecg_device = __respiban_modality(respiban, **ecg_props_)
    ecg_device_metric = DeviceMetric(id=f"{ecg_device.id}-dm",
                                     device=get_reference(ecg_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "mV"}]},
                                     type={"coding": [{"code": "Electrocardiogram"}]}
                                     )
    resources.extend([ecg_device, ecg_device_metric])
    
    
def __create_emg(emg_props, respiban, resources):
    emg_props_ = {
        "id": f"{respiban.id}-emg",
        "status": "active",
        "definition": get_codeable_reference(respiban_emg_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 700, "unit": "Hz"}}
        ]
    }
    emg_props_.update(emg_props)
    emg_device = __respiban_modality(respiban, **emg_props_)
    emg_device_metric = DeviceMetric(id=f"{emg_device.id}-dm",
                                     device=get_reference(emg_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "mV"}]},
                                     type={"coding": [{"code": "Electromyography Activity"}]}
                                     )
    resources.extend([emg_device, emg_device_metric])


def __create_temperature(temp_props, respiban, resources):
    temp_props_ = {
        "id": f"{respiban.id}-temp",
        "status": "active",
        "definition": get_codeable_reference(respiban_temperature_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 700, "unit": "Hz"}}
        ]
    }
    temp_props_.update(temp_props)
    temp_device = __respiban_modality(respiban, **temp_props_)
    temp_device_metric = DeviceMetric(id=f"{temp_device.id}-dm",
                                      device=get_reference(temp_device),
                                      category="measurement",
                                      unit={"coding": [{"code": "°C"}]},
                                      type={"coding": [{"code": "Skin Temperature"}]}
                                      )
    resources.extend([temp_device, temp_device_metric])


def __create_accelerometer(acc_props, respiban, resources):
    acc_props_ = {
        "id": f"{respiban.id}-acc",
        "status": "active",
        "definition": get_codeable_reference(respiban_acc_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 700, "unit": "Hz"}}
        ]
    }
    # reminder: Shallow update
    acc_props_.update(acc_props)
    acc_device = __respiban_modality(respiban, **acc_props_)
    acc_device_metric = DeviceMetric(id=f"{acc_device.id}-dm",
                                     device=get_reference(acc_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "g"}]},
                                     type={"coding": [{"code": "accelerometer"}]})

    resources.extend([acc_device, acc_device_metric])


def __respiban_modality(parent, **properties):
    defaults_ = {"parent": get_reference(parent)}
    defaults_.update(properties)
    return Device(**defaults_)
