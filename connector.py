import json
from pprint import pprint

from fhir.resources import FHIRAbstractModel
from fhir.resources.resource import Resource
from fhirclient.server import FHIRServer
from requests import HTTPError


class FHIRConnector:
    def __init__(self, url):
        """FHIRConnector decouples server operations from FHIR static_resources (The current approach from fhirclient). It
        uses `fhirclient.FHIRServer` to communicate with the remote FHIR server. But uses `fhir.static_resources` to enable
        FHIR R5 descriptions."""

        self.server = FHIRServer(None, url)

    @staticmethod
    def resource_to_json(resource: FHIRAbstractModel):
        """Given a FHIR resource, `resource_to_json` returns a json string compatible with FHIRServer PUT and POST
        operations."""
        return json.loads(resource.json())

    def create(self, resource: Resource):
        if not hasattr(resource, "id") or resource.id is None or not resource.id:
            url = resource.resource_type
            try:
                response = self.server.post_json(url, self.resource_to_json(resource))
            except HTTPError as e:
                raise HTTPError(str(e) + e.response.text)

            json_response = json.loads(response.content)
            resource.id = json_response["id"]

        else:
            url = "/".join([resource.resource_type, resource.id])

            try:
                self.server.put_json(url, self.resource_to_json(resource))
            except HTTPError as e:
                pprint(self.resource_to_json(resource))
                raise HTTPError(str(e) + e.response.text)

        print(f"Created {type(resource).__name__}: {resource.id}")

    def update(self, resource: Resource):
        if not hasattr(resource, "id") or resource.id is None or not resource.id:
            raise RuntimeError("Resource needs an id")

        url = "/".join([resource.resource_type, resource.id])
        try:
            self.server.post_json(url, self.resource_to_json(resource))
        except HTTPError as e:
            raise HTTPError(str(e) + e.response.text)



