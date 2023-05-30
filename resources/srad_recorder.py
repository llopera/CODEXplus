from fhir.resources.device import Device
from fhir.resources.devicemetric import DeviceMetric

from static_resources.device_definition.srad_recorder import srad_recorder_definition, srad_recorder_emg_definition, \
    srad_recorder_ekg_definition, srad_recorder_sc_definition, srad_recorder_resp_definition
from utils import get_codeable_reference, get_reference


def __create_ekg(ekg_props, srad_recorder_, resources, channels):
    ekg_props_ = {
        "id": f"{srad_recorder_.id}-ecg",
        "status": "active",
        "definition": get_codeable_reference(srad_recorder_ekg_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 15.5, "unit": "Hz"}}
        ]
    }
    ekg_props_.update(ekg_props)
    ekg_device = __srad_recorder_modality(srad_recorder_, **ekg_props_)
    ekg_device_metric = DeviceMetric(id=f"{ekg_device.id}-dm",
                                     device=get_reference(ekg_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "mV"}]},
                                     type={"coding": [{"code": "Electrocardiogram"}]}
                                     )
    resources.extend([ekg_device, ekg_device_metric])
    channels.append(ekg_device)


def __srad_recorder_modality(parent, **properties):
    defaults_ = {"parent": get_reference(parent)}
    defaults_.update(properties)
    return Device(**defaults_)


def __create_emg(emg_props, srad_recorder_, resources, channels):
    emg_props_ = {
        "id": f"{srad_recorder_.id}-emg",
        "status": "active",
        "definition": get_codeable_reference(srad_recorder_emg_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 15.5, "unit": "Hz"}}
        ]
    }
    emg_props_.update(emg_props)
    emg_device = __srad_recorder_modality(srad_recorder_, **emg_props_)
    emg_device_metric = DeviceMetric(id=f"{emg_device.id}-dm",
                                     device=get_reference(emg_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "mV"}]},
                                     type={"coding": [{"code": "Electromyography Activity"}]}
                                     )
    resources.extend([emg_device, emg_device_metric])
    channels.append(emg_device)

def __create_sc(channel, sc_props, srad_recorder_, resources, channels):
    sc_props_ = {
        "id": f"{srad_recorder_.id}-sc-{channel}",
        "status": "active",
        "definition": get_codeable_reference(srad_recorder_sc_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 15.5, "unit": "Hz"}}
        ]
    }
    sc_props_.update(sc_props)
    sc_device = __srad_recorder_modality(srad_recorder_, **sc_props_)
    sc_device_metric = DeviceMetric(id=f"{sc_device.id}-dm",
                                    device=get_reference(sc_device),
                                    category="measurement",
                                    unit={"coding": [{"code": "µS"}]},
                                    type={"coding": [{"code": "Electrodermal Activity"}]}
                                    )
    resources.extend([sc_device, sc_device_metric])
    channels.append(sc_device)

def __create_sc_1(sc_1_props, srad_recorder_, resources, channels):
    __create_sc(1, sc_1_props, srad_recorder_, resources, channels)


def __create_sc_2(sc_2_props, srad_recorder_, resources, channels):
    __create_sc(2, sc_2_props, srad_recorder_, resources, channels)


def __create_resp(pzt_props, srad_recorder_, resources, channels):
    pzt_props_ = {
        "id": f"{srad_recorder_.id}-resp",
        "status": "active",
        "definition": get_codeable_reference(srad_recorder_resp_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 15.5, "unit": "Hz"}}
        ]
    }
    pzt_props_.update(pzt_props)
    pzt_device = __srad_recorder_modality(srad_recorder_, **pzt_props_)
    pzt_device_metric = DeviceMetric(id=f"{pzt_device.id}-dm",
                                     device=get_reference(pzt_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "%"}]},
                                     type={"coding": [{"code": "Respiration"}]}
                                     )
    resources.extend([pzt_device, pzt_device_metric])
    channels.append(pzt_device)


def srad_recorder(device_properties=None,
                  ekg_props=None,
                  emg_props=None,
                  resp_props=None,
                  sc_1_props=None,
                  sc_2_props=None):
    defaults_ = {"status": "active",
                 "definition": get_codeable_reference(srad_recorder_definition),
                 }

    # Initialize parameters
    ekg_props = ekg_props if ekg_props is not None else {}
    emg_props = emg_props if emg_props is not None else {}
    resp_props = resp_props if resp_props is not None else {}
    sc_1_props = sc_1_props if sc_1_props is not None else {}
    sc_2_props = sc_2_props if sc_2_props is not None else {}

    defaults_.update(device_properties)
    srad_reader = Device(**defaults_)
    resources = []
    channels = []

    __create_ekg(ekg_props, srad_reader, resources, channels)
    __create_emg(emg_props, srad_reader, resources, channels)
    __create_resp(resp_props, srad_reader, resources, channels)
    __create_sc_1(sc_1_props, srad_reader, resources, channels)
    __create_sc_2(sc_2_props, srad_reader, resources, channels)
    __create_sc_2(sc_2_props, srad_reader, resources, channels)

    return srad_reader, resources, channels


