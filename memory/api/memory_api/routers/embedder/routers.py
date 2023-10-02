import proto

from typing import Union, List, Dict

from fastapi import APIRouter

from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

from memory_api.env import (
    prediction_project, 
    prediction_endpoint_id,
    prediction_location,
    prediction_api_endpoint,
)

from .protocol import Instances


router = APIRouter()


def predict_custom_trained_model_sample(
    project: str,
    endpoint_id: str,
    instances: Union[Dict, List[Dict]],
    location: str = "us-central1",
    api_endpoint: str = "us-central1-aiplatform.googleapis.com",
):
    """
    `instances` can be either single instance of type dict or a list
    of instances.
    """
    # The AI Platform services require regional API endpoints.
    client_options = {"api_endpoint": api_endpoint}
    # Initialize client that will be used to create and send requests.
    # This client only needs to be created once, and can be reused for multiple requests.
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
    # The format of each instance should conform to the deployed model's prediction input schema.
    instances = instances if isinstance(instances, list) else [instances]
    instances = [
        json_format.ParseDict(instance_dict, Value()) for instance_dict in instances
    ]
    parameters_dict = {}
    parameters = json_format.ParseDict(parameters_dict, Value())
    endpoint = client.endpoint_path(
        project=project, location=location, endpoint=endpoint_id
    )
    response = client.predict(
        endpoint=endpoint, instances=instances, parameters=parameters
    )
    # print("response")
    # print(" deployed_model_id:", response.deployed_model_id)
    # The predictions are a google.protobuf.Value representation of the model's predictions.
    return response


@router.post("/embed/")
async def embed(input_: Instances) -> list:
    response = predict_custom_trained_model_sample(
        project=prediction_project,
        endpoint_id=prediction_endpoint_id,
        instances=input_.instances,
        location=prediction_location,
        api_endpoint=prediction_api_endpoint,
    )

    return proto.Message.to_dict(response)["predictions"]
