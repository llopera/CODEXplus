import os
from glob import glob

import pandas as pd
from fhir.resources.device import Device
from fhir.resources.devicemetric import DeviceMetric

from static_resources.device_definition.empatica_e4 import empatica_e4_definition, empatica_e4_acc_definition, \
    empatica_e4_bvp_definition, empatica_e4_eda_definition, empatica_e4_temperature_definition, \
    empatica_e4_ibi_definition, empatica_e4_hr_definition, empatica_e4_tags_definition
from utils import get_reference, get_codeable_reference


def empatica_e4(device_properties=None, acc_props=None, bvp_props=None, eda_props=None,
                temp_props=None, ibi_props=None, hr_props=None):
    defaults_ = {"status": "active",
                 "definition": get_codeable_reference(empatica_e4_definition),
                 }

    # Initialize parameters
    acc_props = acc_props if acc_props is not None else {}
    bvp_props = bvp_props if bvp_props is not None else {}
    eda_props = eda_props if eda_props is not None else {}
    temp_props = temp_props if temp_props is not None else {}
    ibi_props = ibi_props if ibi_props is not None else {}
    hr_props = hr_props if hr_props is not None else {}

    defaults_.update(device_properties)
    empatica = Device(**defaults_)
    resources = []

    __create_accelerometer(acc_props, empatica, resources)
    __create_bvp(bvp_props, empatica, resources)
    __create_eda(eda_props, empatica, resources)
    __create_temperature(temp_props, empatica, resources)
    __create_ibi(ibi_props, empatica, resources)
    __create_hr(hr_props, empatica, resources)
    __create_tags(empatica, resources)

    return empatica, resources


def __create_bvp(bvp_props, empatica, resources):
    bvp_props_ = {
        "id": f"{empatica.id}-bvp",
        "status": "active",
        "definition": get_codeable_reference(empatica_e4_bvp_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 64, "unit": "Hz"}}
        ]
    }
    bvp_props_.update(bvp_props)
    bvp_device = __empatica_e4_modality(empatica, **bvp_props_)
    bvp_device_metric = DeviceMetric(id=f"{bvp_device.id}-dm",
                                     device=get_reference(bvp_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "ADC Code"}]},
                                     type={"coding": [{"code": "PPG"}]}
                                     )
    resources.extend([bvp_device, bvp_device_metric])


def __create_eda(eda_props, empatica, resources):
    eda_props_ = {
        "id": f"{empatica.id}-eda",
        "status": "active",
        "definition": get_codeable_reference(empatica_e4_eda_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 4, "unit": "Hz"}}
        ]
    }
    eda_props_.update(eda_props)
    eda_device = __empatica_e4_modality(empatica, **eda_props_)
    eda_device_metric = DeviceMetric(id=f"{eda_device.id}-dm",
                                     device=get_reference(eda_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "µS"}]},
                                     type={"coding": [{"code": "Electrodermal Activity"}]}
                                     )
    resources.extend([eda_device, eda_device_metric])


def __create_temperature(temp_props, empatica, resources):
    temp_props_ = {
        "id": f"{empatica.id}-temp",
        "status": "active",
        "definition": get_codeable_reference(empatica_e4_temperature_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 4, "unit": "Hz"}}
        ]
    }
    temp_props_.update(temp_props)
    temp_device = __empatica_e4_modality(empatica, **temp_props_)
    temp_device_metric = DeviceMetric(id=f"{temp_device.id}-dm",
                                      device=get_reference(temp_device),
                                      category="measurement",
                                      unit={"coding": [{"code": "°C"}]},
                                      type={"coding": [{"code": "Skin Temperature"}]}
                                      )
    resources.extend([temp_device, temp_device_metric])


def __create_accelerometer(acc_props, empatica, resources):
    acc_props_ = {
        "id": f"{empatica.id}-acc",
        "status": "active",
        "definition": get_codeable_reference(empatica_e4_acc_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 32, "unit": "Hz"}},
            {"type": {"coding": [{"code": "resolution"}]},
             "valueQuantity": {"value": 1 / 64, "unit": "g"}}
        ]
    }
    # reminder: Shallow update
    acc_props_.update(acc_props)
    acc_device = __empatica_e4_modality(empatica, **acc_props_)
    acc_device_metric = DeviceMetric(id=f"{acc_device.id}-dm",
                                     device=get_reference(acc_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "g"}]},
                                     type={"coding": [{"code": "accelerometer"}]})

    resources.extend([acc_device, acc_device_metric])


def __create_ibi(ibi_props, empatica, resources):
    ibi_props_ = {
        "id": f"{empatica.id}-ibi",
        "status": "active",
        "definition": get_codeable_reference(empatica_e4_ibi_definition),
    }
    ibi_props_.update(ibi_props)
    ibi_device = __empatica_e4_modality(empatica, **ibi_props_)
    ibi_device_metric = DeviceMetric(id=f"{ibi_device.id}-dm",
                                     device=get_reference(ibi_device),
                                     category="measurement",
                                     unit={"coding": [{"code": "s"}]},
                                     type={"coding": [{"code": "Inter Beat Interval"}]}
                                     )
    resources.extend([ibi_device, ibi_device_metric])


def __create_tags(empatica, resources):
    tags_props_ = {
        "id": f"{empatica.id}-tags",
        "status": "active",
        "definition": get_codeable_reference(empatica_e4_tags_definition),
    }

    tags_device = __empatica_e4_modality(empatica, **tags_props_)
    tags_device_metric = DeviceMetric(id=f"{tags_device.id}-dm",
                                      device=get_reference(tags_device),
                                      category="measurement",
                                      unit={"coding": [{"code": "timestamp"}]},
                                      type={"coding": [{"code": "Button Press"}]}
                                      )
    resources.extend([tags_device, tags_device_metric])


def __create_hr(hr_props, empatica, resources):
    hr_props_ = {
        "id": f"{empatica.id}-hr",
        "status": "active",
        "definition": get_codeable_reference(empatica_e4_hr_definition),
        "property": [
            {"type": {"coding": [{"code": "sampling rate"}]},
             "valueQuantity": {"value": 1, "unit": "Hz"}}
        ]
    }
    hr_props_.update(hr_props)
    hr_device = __empatica_e4_modality(empatica, **hr_props_)
    hr_device_metric = DeviceMetric(id=f"{hr_device.id}-dm",
                                    device=get_reference(hr_device),
                                    category="measurement",
                                    unit={"coding": [{"code": "bpm"}]},
                                    type={"coding": [{"code": "Heart Rate"}]}
                                    )
    resources.extend([hr_device, hr_device_metric])


def empatica_read_dataframe(data_dir, tz=None):
    """Reads csv files from an empatica data dir. It returns a dictionary with key value pairs set to the modality
    and the dataframe respectively. The dataframe contains time indexed values."""
    modalities = {}
    utc = True
    if tz is None:
        utc = False

    for modality_path in glob(f"{data_dir}/*.csv"):
        metric = os.path.basename(modality_path)[:-4]
        try:
            data = pd.read_csv(modality_path, header=None)

        except pd.errors.EmptyDataError:
            data = pd.DataFrame()
            modalities[metric] = data
            continue

        timestamp = pd.to_datetime(data.iloc[0, 0], unit="s",  utc=utc)
        if metric == "IBI":  # distance in seconds, ergo it is a diff

            if (data[1][1:] == " IBI").any():
                # Participant F5 has a malformed file with 31 rows repeated.
                data = data.loc[data[1][1:][data[1][1:] == " IBI"].index[0]:, :].reset_index(drop=True)

            data.iloc[1:, 0] = pd.to_timedelta(data.iloc[1:, 0], unit="s") + timestamp
            data.iloc[0, :] = timestamp, 0.
            data[0] = data[0].infer_objects()
            data[1] = pd.to_timedelta(data[1].astype(float), unit="s")
            data.set_index(0, drop=True, inplace=True)
            if not data.index.is_unique:
                data = data.loc[~data.index.duplicated()]

        elif metric == "tags":
            data.index = pd.to_datetime(data.values.ravel(), unit="s", utc=utc)

        else:
            frequency = data.iloc[1, 0]
            data = data.iloc[2:, :].infer_objects()
            data.index = pd.to_timedelta(data.index / frequency, unit="s") + timestamp

        modalities[metric] = data.tz_convert(tz)

    return modalities



def __empatica_e4_modality(parent, **properties):
    defaults_ = {"parent": get_reference(parent)}
    defaults_.update(properties)
    return Device(**defaults_)
