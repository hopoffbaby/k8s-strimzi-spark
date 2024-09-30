sudo apt-get update

sudo apt-get install openssl

# create CA private key
openssl genrsa -out ca.key 4096

# create the root certificate
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out cacerts.pem \
  -subj "/C=US/ST=State/L=City/O=YourOrganization/OU=IT/CN=YourRootCA"

# generate private key for rancher
openssl genrsa -out tls.key 2048

# generate the CSR
openssl req -new -key tls.key -out tls.csr -config /vagrant/data/csrReq.conf

# sign the CSR with the CA
openssl x509 -req -in tls.csr -CA cacerts.pem -CAkey ca.key -CAcreateserial -out tls.crt -days 365 -sha256 -extfile /vagrant/data/csrReq.conf -extensions req_ext

#Install the certs on the OS
sudo cp cacerts.pem /usr/local/share/ca-certificates/cacerts.crt
sudo update-ca-certificates