# CODEX+ - Recording datasets with sensor data using FHIR repositories.
This repository contains the code to test the FHIR schema used to upload stress related datasets into a FHIR R5 compatible server.

## Setting up FHIR server

As the FHIR R5 server we used HAPI JPA starter server available [@hapifhir/hapi-fhir-jpaserver-starter](https://github.com/hapifhir/hapi-fhir-jpaserver-starter). This project was tested with version v6.6.0.

We recommend checking out the repository and then using `docker compose up` to compile. Make sure you start the server with version R5 of the FHIR protocol. Please visit [@hapifhir/hapi-fhir-jpaserver-starter](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) for more details on how to start the server.
```sh
git clone https://github.com/hapifhir/hapi-fhir-jpaserver-starter.git
cd hapi-fhir-jpaserver-starter
docker compose build
```
Before starting the container, you need to modify the `docker-compose.yaml` by adding the environment variable  `hapi.fhir.fhir_version: "R5"` to ensure the sever start with version R5 of the FHIR protocol.

```yaml
...
hapi-fhir-jpaserver-start:
    build: .
    container_name: hapi-fhir-jpaserver-start
    restart: on-failure
    ports:
      - "8080:8080"
    environment:
      hapi.fhir.fhir_version: "R5"
...
```

To run the server use the following:
```shell
docker compose up
```
When accessing localhost:8080, the default HAPI FHIR server page should be available. The following version values should be displayed:


| | |
| ------------- | ------------- |
| Server | HAPI FHIR R5 Server |
| Software | HAPI FHIR Server - 6.6.0 |
| FHIR Base	| http://localhost:8080/fhir |

## Setting up the client

We recommend creating a virtual environment and using at least python 3.10

```shell
git clone ssh://github.com/llopera/CODEXplus.git  # setup ssh key access before continuing 
cd CODEXplus
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

run the client as follows:

```shell
python app.py
```
The client will download the required datasets into the datasets folder. Please be advise that the first time this 
will require some time.

## Troubleshooting

If the datasets fail to download automatically please use the following links:


| Dataset                                                                | File type     | URL |
|------------------------------------------------------------------------|---------------| ----    |
| [SRAD](https://physionet.org/content/drivedb/1.0.0/)                   | Dataset       |[ZIP fle](https://physionet.org/static/published-projects/drivedb/stress-recognition-in-automobile-drivers-1.0.0.zip)|
| [SDN](https://datadryad.org/stash/dataset/doi:10.5061/dryad.5hqbzkh6f) | Dataset       | [ZIP file](https://datadryad.org/stash/downloads/file_stream/1022493) |
|                                                                        | Questionnaires |  [XLS File](https://datadryad.<br/>org/stash/downloads/file_stream/1022492)|
| [WESAD](https://archive.ics.uci.edu/ml/datasets/WESAD+%28Wearable+Stress+and+Affect+Detection%29)|  Dataset: | [ZIP File](https://uni-siegen.sciebo.de/s/HGdUkoNlW1Ub0Gx/download) |
| [WSPCP](https://physionet.org/content/wearable-exam-stress/1.0.0/) | Dataset | [ZIP File](https://physionet.org/static/published-projects/wearable-exam-stress/a-wearable-exam-stress-dataset-for-predicting-cognitive-performance-in-real-world-settings-1.0.0.zip)|

To avoid making code changes, please create and store dataset files in the `datasets/{$DATASET}` directory. Where 
`${DATASET}` corresponds to the abbreviations from the previous table, e.g., SRAD. After downloading all files,  the 
dataset directory should have the following structure:

```shell
datasets/
    SDN/
        Stress_dataset.zip
        SurveyResults.xlsx
    
    SRAD/
        stress-recognition-in-automobile-drivers-1.0.0.zip
    
    WESAD/
        WESAD.zip
    
    WSPCP/
        a-wearable-exam-stress-dataset-for-predicting-cognitive-performance-in-real-world-settings-1.0.0.zip
```

Running the `app.py` script will unpack the zip files as needed for the loaders.