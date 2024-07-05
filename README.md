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

### Deployed at:
95.217.207.179:8182

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


### Not working: 
- curl -x http://0.0.0.0:8899 -H "Accept: text/turtle" --cacert ca-cert.pem http://ontologi.es/days#


# https://archivo.dbpedia.org/download?o=http://linked-web-apis.fit.cvut.cz/ns/core&v=2020.07.16-115638&versionMatching=timeStampClosest