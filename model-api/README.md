# Samantha API
Samantha API server

## Install and run vllm service
```bash
$ cd services/vllm
$ poetry install
$ poetry shell
$ python samantha_api/web.py --model ehartford/samantha-33b --tensor-parallel-size 2 --host 127.0.0.1 --port 8000 --backlog 4096

$ python -m model_api --model julep-ai/samantha-1-turbo 
```

## Set up skypilot to run service on A100 spot instances

you can use this as a starting point:  
https://github.com/julep-ai/samantha-monorepo/blob/main/infra/sky/vllm.yaml

### Docs:
- quickstart: https://skypilot.readthedocs.io/en/latest/getting-started/quickstart.html
- spot jobs: https://skypilot.readthedocs.io/en/latest/examples/spot-jobs.html
- services: https://skypilot.readthedocs.io/en/latest/serving/sky-serve.html

### Setup:
1. Authenticate gcloud cli. `gcloud auth login` and then `gcloud auth application-default login`
1. `pip install --upgrade skypilot nightly`
1. Run `sky check` to check that it detected the gcp credentials

### Create service:
1. Edit the vllm.yaml file with setup instructions of our custom code
1. `sky serve up -n vllm-service vllm.yaml` to start service (no support for in-place update unfortunately)
1. `sky serve logs vllm-service 1` (1 is the ID of first replica, repeat for every replica)
1. `watch -n10 sky serve status` for live status of services

### Notes:
1. Right now `sky serve up` does not support using environment variables for some reason so set them manually in the file itself (and remember to unset before committing to git)
1. Right now `sky serve` does not support updating a service -- which means if you change anything, you have to `sky serve down vllm-service` and then `sky serve up ...` again...
