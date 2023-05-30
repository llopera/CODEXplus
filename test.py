import json

from fhirclient import client
import fhirclient.models.observation as obs


def main():
    ekg_observation = obs.Observation(
        json.load(open("examples/ekg_observation_example.json"))
    )
    print(ekg_observation)


if __name__ == "__main__":
    main()
