# Cloud Run on GKE and Cloud Run Managed demo

Simple repo to show how to deploy a Python Flask service in both Cloud Run on GKE and Cloud Run Managed. When in GKE mode, we'll use as well KNative tooling to test what has been deployed.

## What you need

- Access to Google Cloud Platform console and billing enabled.
- Google Cloud SDK (`brew cask install google-cloud-sdk`).
- A Google Cloud Platform project where you are owner (`gcloud projects create <myprojectid>`).
- KNative command line tool, `kn` (`brew install knative/client/kn`)).
- Kubectx tool (`brew install kubectx`).
- Python 3.8 installed in your system (optional, only if you want to test the application before deploying the service)

All commands above assume you're using a Mac OS X based computer, but adapting to other systems should be easy, see documentation for each of the tools mentioned.

## Setup
- Clone this project: git clone `https://github.com/javiercanadillas/cloud-run-gke-simple`
- Move to the project folder, `cd cloud-run-gke-simple`
- Make sure `gcloud` is pointing to the right project:

  ```bash
  gcloud config set project <myprojectid>
  ```

- Make sure you're authorized to use the Cloud SDK:

  ```bash
  gcloud auth login
  ```

- Configure the `.env` file to match your configuration. The only variables that you must change are `PROJECT_NAME` and `NAMESPACE`. Both should have the same value, the `project id` of your existing project.
- Prepare the environment by setting up local environment variables:

  ```bash
  . .env
  ```

- Run the GKE cluster creation script:

  ```bash
  ./setup_cloud_run_gke --zone "${ZONE}" --cluster-name "${CLUSTER_NAME}" --project-id "${PROJECT_ID}"
  ```

After some time, the script should create a 3 node GKE cluster with all the necessary configuration to deploy Cloud Run/KNative compatible services. Wait until you see your cluster is ready:

```bash
gcloud container clusters describe "${CLUSTER_NAME}"
```

When ready, proceed to deploy the Flask service as described in the next section.

## Deploy to Cloud Run for Anthos on Google Cloud

Now it's time to deploy the Flask service. We'll use Cloud Build and a Dockerfile describing the image we'll be building

```bash
gcloud builds submit --config=cloudbuild-gke.yaml \
  --substitutions=_SERVICE_NAME="${SERVICE_NAME}",_CLUSTER_NAME="${CLUSTER_NAME}",_ZONE="${ZONE}" .
```

It's interesting to have a look at both the `cloudbuild-gke.yaml` and the `dockerfile`. The first file defines the delivery pipeline for the service, from the builing of the image following the `dockerfile` specification, to the final deployment of a container based on the image in the Cloud Run serving platform configured in the GKE cluster.

If successful, the next thing you need is the IP of the service implementing the istio-ingress to invoke your service.

Before continuing, make sure you're operating in the right GKE cluster and that you have the proper `kubectl` credentials:

```bash
gcloud container clusters get-credentials "${CLUSTER_NAME}"
kubectx <your cluster>
```

Now we can check the Istio configuration that GKE is using for KNative having a look at its configmap `config-istio`:

```bash
kubectl get configmap config-istio --namespace knative-serving -oyaml
```

Then, we get the IP for the Istio Ingress included in Cloud Run and put it in a new file:

```bash
kubectl get service istio-ingress --namespace gke-system -o=jsonpath='{$.status.loadBalancer.ingress[0].ip}' >> external-ip.txt
```

To test that the service is running, there are two options:
- Use curl to make a GET request to the IP, injecting the service FQDN as a `Host` header in the request for the ingress to route appropriately: 
  ```bash
  curl -s -w'\n' -H Host:"${SERVICE_NAME}".default.example.com $(cat external-ip.txt)
  ```
- Install a browser extension like [ModHeader](https://bewisse.com/modheader/) and configure to inject the previous header `Host: <service_name>.default.example.com` in the request.

### Exploring the KNative service

What we've just deployed is a KNative-compatible service. We can have a look at it using KNative & Kubernetes standard tools.

We can get the service that's deployed in the cluster using `kubectl`. The service should be available in the `knative-serving` namespace configured in the GKE cluster:

```bash
kubectl get services -n knative-serving
```

We can also use the `kn` tool that's part of the KNative distribution that you should've installed:

```bash
kn service list
kn service describe "${SERVICE_NAME}"
```

Finally, you can delete the service just deployed using either `kn`:

```bash
kn service delete "${SERVICE_NAME}"
```

or the Cloud SDK through `gcloud`:

```bash
gcloud run services delete "${SERVICE_NAME}" --platform=gke
```

## Deploy to Cloud Run on GCP

Now, we'll deploy the service to Cloud Run on GCP. As its GKE-based equivalent, Cloud Run on GCP is the Google fully managed version of KNative. That means that the same constructions and primitive will be available in the Cloud, but no cluster management will be necessary as this falls under the Google responsibility.

To deploy the service to Cloud Run, we'll use again Cloud Build, invoked via the `gcloud` command. Remember that in the following command we're using the environment variables defined in the `.env` file:

```bash
gcloud builds submit --config=cloudbuild-managed.yaml \
  --substitutions=_SERVICE_NAME="${SERVICE_NAME}",_REGION="${REGION}" .
```

The service has been deployed with the option `--allow-unauthenticated`, which means that you should be able to access it from the URL that's printed in the screen after successful deployment.

You can also get from `gcloud` the list of deployed services:

```bash
gcloud run services list --platform=managed
```