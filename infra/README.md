## Kubernetes

### cluster

- created cluster using google cloud console
- cluster name: julep-cluster-1
- region: us-central1
- regional with default zone=us-central1-c

### default-pool

- autoscaler: 3-12
- instance: e2-standard-2

### cluster features

- vertical pod autoscaling
- control plane global access
- dataplane v2
- calico policy
- gateway api
- filestore csi
- gcs csi

### DNS

- cloud dns
- vpc scope
- \*.julep-cluster-1

## Components

1. kubero
2. OLM
3. Stackgres

## Operators

1. temporal ( https://alexandrevilain.github.io/temporal-operator/getting-started/ )
2. grafana ( https://operatorhub.io )
3. prometheus ( https://operatorhub.io )

## Helm charts

### etcd

**Note:** bitnami's version didn't work for some reason.
(Gave cryptic error: `ERROR ==> Headless service domain does not have an IP`)

```sh
helm repo add mkhpalm https://mkhpalm.github.io/helm-charts/
helm install etcd mkhpalm/etcd -n ingress-apisix
```

Additional steps:

- Then manually create the `root` user in etcd and enable authentication.

### apisix

```sh
helm repo add apisix https://charts.apiseven.com
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install apisix apisix/apisix \
  --create-namespace \
  --namespace ingress-apisix \
  --values helm/apisix.yaml \
  --set ingress-controller.config.apisix.adminKey=CHANGE_ME \
  --set etcd.password=CHANGE_ME \
  --set externalEtcd.password=CHANGE_ME \
  --set dashboard.config.conf.etcd.password=CHANGE_ME \
  --set dashboard.config.authentication.secret=CHANGE_ME \
  --set apisix.admin.credentials.admin=CHANGE_ME \
  --set apisix.admin.credentials.viewer=CHANGE_ME

```
