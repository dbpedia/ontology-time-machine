import pytest
import requests
import time
import subprocess
from ontologytimemachine.custom_proxy import IP, PORT


PROXY = f'{IP}:{PORT}'
HTTP_PROXY = f'http://{PROXY}'
HTTPS_PROXY = f'http://{PROXY}'
PROXIES = {
    "http": HTTP_PROXY,
    "https": HTTPS_PROXY
}
CA_CERT_PATH = "ca-cert.pem"


@pytest.fixture(scope="module", autouse=True)
def start_proxy_server():
    # Start the proxy server in a subprocess
    process = subprocess.Popen(
        [
            'python3', '-m', 'proxy', 
            '--ca-key-file', 'ca-key.pem',
            '--ca-cert-file', 'ca-cert.pem',
            '--ca-signing-key-file', 'ca-signing-key.pem',
            '--hostname', IP, 
            '--port', PORT, 
            '--plugins', 'ontologytimemachine.custom_proxy.OntologyTimeMachinePlugin'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait a bit to ensure the server starts
    time.sleep(5)
    
    yield
    "http://0.0.0.0:8899"
    # Terminate the proxy server after tests
    process.terminate()
    process.wait()


def test_babelnet():
    iri = 'http://babelnet.org/rdf/'
    generic_test(iri, 'text/turtle')


def test_bag_basisregistraties():
    iri = 'http://bag.basisregistraties.overheid.nl/def/bag'
    generic_test(iri, 'text/turtle')


def test_bblfish():
    iri = 'http://bblfish.net/work/atom-owl/2006-06-06/'
    generic_test(iri, 'text/turtle')


def test_brk_basisregistraties():
    iri = 'http://brk.basisregistraties.overheid.nl/def/brk'
    generic_test(iri, 'text/turtle')


def test_brt_basisregistraties():
    iri = 'http://brt.basisregistraties.overheid.nl/def/top10nl'
    generic_test(iri, 'text/turtle')


def test_brt_basisregistraties_begrippenkader():
    iri = 'http://brt.basisregistraties.overheid.nl/id/begrippenkader/top10nl'
    generic_test(iri, 'text/turtle')


def test_buzzword():
    iri = 'http://buzzword.org.uk/rdf/personal-link-types#'
    generic_test(iri, 'text/turtle')


def test_catalogus_professorum():
    iri = 'http://catalogus-professorum.org/cpm/2/'
    generic_test(iri, 'text/turtle')


def test_data_gov():
    iri = 'http://data-gov.tw.rpi.edu/2009/data-gov-twc.rdf'
    generic_test(iri, 'text/turtle')


def test_data_bigdatagrapes():
    iri = 'http://data.bigdatagrapes.eu/resource/ontology/'
    generic_test(iri, 'text/turtle')


def test_data_europa_esco():
    iri = 'http://data.europa.eu/esco/flow'
    generic_test(iri, 'text/turtle')


def test_data_globalchange():
    iri = 'http://data.globalchange.gov/gcis.owl'
    generic_test(iri, 'text/turtle')


def test_data_ontotext():
    iri = 'http://data.ontotext.com/resource/leak/'
    generic_test(iri, 'text/turtle')


def test_data_opendiscoveryspace():
    iri = 'http://data.opendiscoveryspace.eu/lom_ontology_ods.owl#'
    generic_test(iri, 'text/turtle')


def test_data_ordnancesurvey_50kGazetteer():
    iri = 'http://data.ordnancesurvey.co.uk/ontology/50kGazetteer/'
    generic_test(iri, 'text/turtle')


def test_data_ordnancesurvey_50kGazetteer():
    iri = 'http://dbpedia.org/ontology/Person'
    generic_test(iri, 'text/turtle')


def test_linked_web_apis():
    iri = 'http://linked-web-apis.fit.cvut.cz/ns/core'
    generic_test(iri, 'text/turtle')


#def test_ontologi_es():
#    iri = 'http://ontologi.es/days#'
#    generic_test(iri, 'text/turtle')


def test_https():
    iri = "https://www.w3id.org/simulation/ontology/"
    generic_test(iri, 'text/plain; charset=utf-8')


def test_https():
    iri = "https://vocab.eccenca.com/auth/"
    generic_test(iri, 'text/plain; charset=utf-8')


def not_test_all_iris():
    with open('tests/archivo_ontologies_test.txt', 'r') as file:
        for line in file:
            iri = line.strip()
            if iri:  # Ensure it's not an empty line
                iri_generic_test(iri)


def generic_test(iri, content_type):
    response = requests.get(iri, proxies=PROXIES, verify=CA_CERT_PATH)
    assert response.status_code == 200
    assert iri in response.content.decode('utf-8')


def iri_generic_test(iri):
    try:
        response = requests.get(iri, proxies=PROXIES, verify=CA_CERT_PATH)
        assert response.status_code == 200
        assert iri in response.content.decode('utf-8')
        print(f"Test passed for IRI: {iri}")
    except AssertionError:
        print(f"Test failed for IRI: {iri}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed for IRI: {iri}, Error: {e}")


if __name__ == '__main__':
    pytest.main()
