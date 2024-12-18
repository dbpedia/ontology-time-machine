# ontology-time-machine

A time machine proxy. This proxy enables access to specific historical versions of ontologies, ensuring that they can be retrieved even if no longer available at their original source.


## Configuration options

### defaultOntoVersion (default: `originalFailoverLive`)

- **original**
  - Intercepts requests but serves the original upstream ontology response. 

- **originalFailoverLiveLatest**
  - The proxy tries to determine the live status during the request. If there is an accessibility failure, it hands over to Archivo to serve the latest version from there in case a failure is detected.

- **latestArchived**
  - Proxy always serves the latest version of an ontology directly from Archivo (if it is contained in it). 
  - This is considered the most robust mode in terms of accessibility (can be useful if the original hosted version has syntax errors in RDF, as partially recovered files are served from Archivo).

- **timestampArchived `<timestamp>`**
  - Proxy always serves the version of an ontology directly from Archivo (if it is contained in it).


### ontoFormat 

- **Arguments**: 2 required + 1 optional (default is `ntriples,enforcedPriority,false`)
  - **format**: Desired representation of the (ontology) resource, one of:
    - `"turtle"`
    - `"ntriples"`
    - `"rdfxml"`
    - `"htmldocu"`
  
  - **precedence**: Controls how the desired format interacts with the client's `Accept` headers:
    - **default**: The format is used as the default fallback if no format is specified in the `Accept` header by the client.
    - **enforcedPriority**: Boosts the priority of the specified format as highest, even if the client specifies other formats with higher priority.
      - **Example**: 
        - If `enforcedPriority ntriples`:
        - Client sends: turtle only → no change to `Accept` header.
        - Client sends: turtle, ntriples → `ntriples` will be added with the highest priority (1.0 score) at the beginning of the `Accept` string.
    
    - **always**: Ignores the client’s preferences in the `Accept` header.

    - **NOTE**: By default, these parameters only affect requests served by Archivo. If they should apply to all upstream connections, use `patchAcceptUpstream`.

    - **ATTENTION**: In `default` or `enforcedPriority` mode, an HTTP error code 406 is thrown if the request triggers a response from Archivo, but no supported format matches the (modified) `Accept` header (e.g., `Accept` header is just JSON-LD).

  - **patchAcceptUpstream** (optional, default: `false`)
    - Defines whether the `Accept` header is patched only for proxy internal behavior or is actually sent in the changed form to the upstream server.

### restrictedAccess (default: `disabled`)

- Enable mode to only serve requests to URLs of Archivo ontologies. All others are denied/discarded by sending a proxy status 407 response and a message that you need to deploy your own proxy instance to make that work.

### httpsInterception 

- (If a CA cert is provided, this option can be used to control HTTPS interception for a specific set of fully qualified domain names (FQDNs), default is `none`):
  - **none** (default)
    - No HTTPS interception is performed, but the request is passed through.
    - **NOTE**: When hosting this publicly, this can be abused by clients to connect to any port and e.g. send spam messages.

  - **block**
    - All HTTPS connections will be blocked.

  - **archivo**
    - HTTPS interception only for FQDNs that have at least one ontology in Archivo.
      - **NOTE**: This will block other requests as well.

  - **all**
    - For every request to every domain (FQDN).


### IN PROGRESS: authMode (default: `off`)

- **off**: No authentication required.
- **basic**: Basic authentication with user-provided password and username on startup (`--auth user:pass`).
- **time travel timestamp**: Username provides a timestamp.
- **apply request-based configuration**


## Installation

### Before building the docker file:

```
git clone https://github.com/abhinavsingh/proxy.py.git
cd proxy.py
make ca-certificates
cp ca-cert.pem ~/ontology-time-machine/ca-cert.pem
cp ca-key.pem ~/ontology-time-machine/ca-key.pem
cp ca-signing-key.pem ~/ontology-time-machine/ca-signing-key.pem
```

### Install poetry virtual environment
```
poetry install
```


### Docker command:
- docker build -t ontology_time_machine:0.1 .
- docker run -d -e PORT=8899 -p 8182:8899 ontology_time_machine:0.1


## Usage

### Activate poetry environment
```
poetry shell
```

### Starting the proxy

python3 ontologytimemachine/custom_proxy.py --ontoFormat ntriples --ontoVersion originalFailoverLiveLatest --ontoPrecedence enforcedPriority


## Manual tests

### Curl tests:
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem http://www.google.com
- curl -x http://0.0.0.0:8899 -H "Accept: text/turtle" --cacert ca-cert.pem http://linked-web-apis.fit.cvut.cz/ns/core
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem https://www.w3id.org/simulation/ontology/
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem https://www.w3.org/ns/ldt#
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem https://raw.githubusercontent.com/br0ast/simulationontology/main/Ontology/simulationontology.owl
- curl -x http://0.0.0.0:8899 -H "Accept: text/turtle" --cacert ca-cert.pem http://bblfish.net/work/atom-owl/2006-06-06/
- curl -x http://0.0.0.0:8899 -H "Accept: text/turtle" --cacert ca-cert.pem http://purl.org/makolab/caont/
- curl -x http://0.0.0.0:8899 --cacert ca-cert.pem https://vocab.eccenca.com/auth/
- curl -x http://0.0.0.0:8899 -H "Accept: text/turtle" --cacert ca-cert.pem http://dbpedia.org/ontology/Person


