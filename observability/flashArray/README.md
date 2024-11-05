deploys a container called pure-fa-om-exporter

container can query pure servers based on headers received 

service monitor passes the array endpoint and secrets to use

kubectl --kubeconfig kubeconfig.yaml apply -n puremonitoring -f .\flashArray\

pod is working via postman, but no scrape is installed into prometheus...