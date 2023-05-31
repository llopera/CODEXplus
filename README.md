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

run the cleint as follows:

```shell
python app.py
```
The client will download the required datasets into the datasets folder. Please be advise that the first time this 
will require some time.