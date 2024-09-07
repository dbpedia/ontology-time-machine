import pytest
import requests
import time
import subprocess
import itertools
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
            'python3', 'ontologytimemachine/custom_proxy.py', 
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


# def test_babelnet():
#     iri = 'http://babelnet.org/rdf/'
#     generic_test(iri, 'text/turtle')


# def test_bag_basisregistraties():
#     iri = 'http://bag.basisregistraties.overheid.nl/def/bag'
#     generic_test(iri, 'text/turtle')


# def test_bblfish():
#     iri = 'http://bblfish.net/work/atom-owl/2006-06-06/'
#     generic_test(iri, 'text/turtle')


# def test_brk_basisregistraties():
#     iri = 'http://brk.basisregistraties.overheid.nl/def/brk'
#     generic_test(iri, 'text/turtle')


# def test_brt_basisregistraties():
#     iri = 'http://brt.basisregistraties.overheid.nl/def/top10nl'
#     generic_test(iri, 'text/turtle')


# def test_brt_basisregistraties_begrippenkader():
#     iri = 'http://brt.basisregistraties.overheid.nl/id/begrippenkader/top10nl'
#     generic_test(iri, 'text/turtle')


# def test_buzzword():
#     iri = 'http://buzzword.org.uk/rdf/personal-link-types#'
#     generic_test(iri, 'text/turtle')


# def test_catalogus_professorum():
#     iri = 'http://catalogus-professorum.org/cpm/2/'
#     generic_test(iri, 'text/turtle')


# def test_data_gov():
#     iri = 'http://data-gov.tw.rpi.edu/2009/data-gov-twc.rdf'
#     generic_test(iri, 'text/turtle')


# def test_data_bigdatagrapes():
#     iri = 'http://data.bigdatagrapes.eu/resource/ontology/'
#     generic_test(iri, 'text/turtle')


# def test_data_europa_esco():
#     iri = 'http://data.europa.eu/esco/flow'
#     generic_test(iri, 'text/turtle')


# def test_data_globalchange():
#     iri = 'http://data.globalchange.gov/gcis.owl'
#     generic_test(iri, 'text/turtle')


def test_data_ontotext():
    iri = 'http://data.ontotext.com/resource/leak/'
    generic_test(iri, 'text/turtle')


# def test_data_ordnancesurvey_50kGazetteer():
#     iri = 'http://dbpedia.org/ontology/Person'
#     generic_test(iri, 'text/turtle')


def test_linked_web_apis():
    iri = 'http://linked-web-apis.fit.cvut.cz/ns/core'
    generic_test(iri, 'text/turtle')


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


def get_parameter_combinations():
#       Define the possible values for each parameter
        ontoFormat = ['turtle', 'ntriples', 'rdfxml', 'htmldocu']
        ontoPrecedence = ['default', 'enforcedPriority', 'always']
        patchAcceptUpstream = [True, False]
        ontoVersion = ['original', 'originalFailoverLive', 'originalFailoverArchivoMonitor', 
                       'latestArchive', 'timestampArchive', 'dependencyManifest']
        onlyOntologies = [True, False]
        httpsIntercept = [True, False]
        inspectRedirects = [True, False]
        forwardHeaders = [True, False]
        subjectBinarySearchThreshold = [1, 2, 3, 4, 5, 10, 25, 50, 100]

        combinations = list(itertools.product(ontoFormat, ontoPrecedence, patchAcceptUpstream, ontoVersion,
                                              onlyOntologies, httpsIntercept, inspectRedirects,
                                              forwardHeaders, subjectBinarySearchThreshold))
        return combinations


if __name__ == '__main__':
    
    pytest.main()
