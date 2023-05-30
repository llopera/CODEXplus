from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.resource import Resource


def get_reference(resource):
    if not resource.id:
        raise ResourceWarning(f"{resource} has no id")

    return {"reference": f"{type(resource).__name__}/{resource.id}"}


def get_list_of_references(resource_list):
    return [get_reference(ref) for ref in resource_list]


def get_codeable_reference(resource: Resource, code: [CodeableConcept, None, str] = None):
    if not resource.id:
        raise ResourceWarning(f"{resource} has no id")

    codeable_reference = {"reference": get_reference(resource)}

    if code is not None:
        codeable_reference["concept"] = code

    return codeable_reference