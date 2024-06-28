# ontology-time-machine


### Before building the docker file:

```
git clone https://github.com/abhinavsingh/proxy.py.git
cd proxy.py
make ca-certificates
cp ca-cert.pem ~/ontology-time-machine/ca-cert.pem
cp ca-key.pem ~/ontology-time-machine/ca-key.pem
cp ca-signing-key.pem ~/ontology-time-machine/ca-signing-key.pem
```


### Docker command:
- docker build -t ontology_time_machine:0.1 .
- docker run -d -e PORT=8899 -p 8182:8899 ontology_time_machine:0.1

### Curl tests:
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem http://www.google.com
- curl -x http://0.0.0.0:8899 -H "Accept: text/turtle" --cacert ca-cert.pem http://ontologi.es/days#
- curl -x http://0.0.0.0:8899 -H "Accept: text/turtle" --cacert ca-cert.pem http://linked-web-apis.fit.cvut.cz/ns/core
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem https://www.w3id.org/simulation/ontology/
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem https://www.w3.org/ns/ldt#
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem https://raw.githubusercontent.com/br0ast/simulationontology/main/Ontology/simulationontology.owl
- curl -x http://0.0.0.0:8899 -H "Accept: text/turtle" --cacert ca-cert.pem http://bblfish.net/work/atom-owl/2006-06-06/
- curl -x http://0.0.0.0:8899 -H "Accept: text/turtle" --cacert ca-cert.pem http://purl.org/makolab/caont/


### Not working: 
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem https://vocab.eccenca.com/auth/




from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser, httpParserTypes
from proxy.common.utils import build_http_response
from proxy.http.methods import HttpMethods
from ontologytimemachine.utils.utils import proxy_logic_http, proxy_logic_https
from ontologytimemachine.utils.utils import check_if_archivo_ontology_requested
from ontologytimemachine.utils.utils import get_headers_and_expected_type
from requests.exceptions import SSLError, Timeout, ConnectionError, RequestException
from http.client import responses
import proxy
import sys
import requests
import logging


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OntologyTimeMachinePlugin(HttpProxyBasePlugin):
    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)


    def before_upstream_connection(self, request: HttpParser):
        logger.debug('Before upstream')
        print(request.method)
        scheme = 'https' if request.method == b'CONNECT' else 'http'
        if scheme == 'https':
            logger.debug('The request is HTTPS, forward as it is')
            return request

        ontology_request = check_if_archivo_ontology_requested(request)
        if ontology_request:
            logger.debug('The request is for an ontology')
            try:
                ontology_url = str(request._url)
                headers, _ = get_headers_and_expected_type(request)
                response = requests.get(ontology_url, headers=headers)
                if response.status_code == 502:
                    logger.error('Received 502 Bad Gateway error')
                    response = proxy_logic_http(request)
                    logger.debug('Queue response')
                    self.queue_response(response)
                    return None
                else:
                    logger.debug('The request is correct')
                    return request
            except (SSLError, Timeout, ConnectionError, RequestException) as e:
                logger.error(f'Network-related exception occurred {e}')
                response = proxy_logic_http(request)
                logger.debug('Queue response')
                self.queue_response(response)
                return None
        return request


    def handle_client_request(self, request: HttpParser):
        logger.debug('HTTP call')
        logger.debug(request._url)

        ontology_request = check_if_archivo_ontology_requested(request)
        if not ontology_request:
            logger.info('No ontology is asked, forward original request')
            return request    
        
        response = proxy_logic_http(request)
        self.queue_response(response)

        return None
    

    def handle_upstream_chunk(self, chunk: memoryview):
        logger.info('HTTPS call')

        try:
            # Parse the HTTP response to handle different cases
            parser = HttpParser(httpParserTypes.RESPONSE_PARSER)
            parser.parse(memoryview(chunk))
            code = int(parser.code.decode('utf-8'))
            if code >= 100 and code < 200:
                return chunk
            elif code >= 201 and code <= 204:
                return chunk
            elif code == 451:
                return chunk
            else:
                response = proxy_logic_https(parser)
                logger.debug('Queue response')
                self.queue_response(response)
                return None
        except UnicodeDecodeError:
            logger.warning('Received non-text chunk, cannot decode')
        except Exception as e:
            logger.error(f'Exception occurred while handling upstream chunk: {e}')
        
        return chunk

    def queue_response(self, response):
        self.client.queue(
            build_http_response(
                response.status_code, 
                reason=bytes(responses[response.status_code], 'utf-8'), 
                headers={
                    b'Content-Type': bytes(response.headers.get('Content-Type'), 'utf-8')
                }, 
                body=response.content
            )
        )


if __name__ == '__main__':
    sys.argv += [
        '--ca-key-file', 'ca-key.pem',
        '--ca-cert-file', 'ca-cert.pem',
        '--ca-signing-key-file', 'ca-signing-key.pem',
    ]
    sys.argv += [
        '--hostname', '0.0.0.0',
        '--port', '8899',
        '--plugins', __name__ + '.OntologyTimeMachinePlugin'
    ]
    logger.info("Starting OntologyTimeMachineProxy server...")
    proxy.main()