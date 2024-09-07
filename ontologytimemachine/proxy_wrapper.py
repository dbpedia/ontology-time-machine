from abc import ABC, abstractmethod
from proxy.http.parser import HttpParser
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AbstractRequestWrapper(ABC):
    def __init__(self, request):
        self.request = request

    @abstractmethod
    def is_get_request(self) -> bool:
        pass

    @abstractmethod
    def is_connect_request(self) -> bool:
        pass

    @abstractmethod
    def is_head_request(self) -> bool:
        pass

    @abstractmethod
    def is_https_request(self) -> bool:
        pass

    @abstractmethod
    def get_request(self):
        pass

    @abstractmethod
    def get_request_headers(self):
        pass

    @abstractmethod
    def get_request_accept_header(self):
        pass

    @abstractmethod
    def set_request_accept_header(self, mime_type):
        pass

    @abstractmethod
    def get_ontology_from_request(self):
        pass


class HttpRequestWrapper(AbstractRequestWrapper):
    def __init__(self, request: HttpParser):
        super().__init__(request)

    def is_get_request(self) -> bool:
        return self.request.method == b'GET'

    def is_connect_request(self):
        return self.request.method == b'CONNECT'

    def is_head_request(self):
        return self.request.method == b'HEAD'

    def is_https_request(self):
        return self.request.method == b'CONNECT' or self.request.headers.get(b'Host', b'').startswith(b'https')

    def get_request(self):
        return self.request

    def get_request_headers(self):
        headers = {}
        for k, v in self.request.headers.items():
            headers[v[0].decode('utf-8')] = v[1].decode('utf-8')
        return headers

    def get_request_accept_header(self):
        logger.info('Wrapper - get_request_accept_header')
        return self.request.headers[b'accept'][1].decode('utf-8')
    
    def set_request_accept_header(self, mime_type):
        self.request.headers[b'accept'] = (b'Accept', mime_type.encode('utf-8'))
        logger.info(f'Accept header set to: {self.request.headers[b"accept"][1]}')
    
    def get_ontology_from_request(self):
        logger.info('Get ontology from request')
        print(f'Request protocol: {self.request.protocol}')
        print(f'Request host: {self.request.host}')
        print(f'Request _url: {self.request._url}')
        print(f'Request path: {self.request.path}')
        if (self.request.method == b'GET' or self.request.method == b'HEAD') and not self.request.host:
            for k, v in self.request.headers.items():
                if v[0].decode('utf-8') == 'Host':
                    host = v[1].decode('utf-8')
                    path = self.request.path.decode('utf-8')
            ontology = 'https://' + host + path
        else:
            host = self.request.host.decode('utf-8')
            path = self.request.path.decode('utf-8')
            ontology = str(self.request._url)
        logger.info(f'Ontology: {ontology}')
        return ontology, host, path