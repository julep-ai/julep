from fastapi import APIRouter, HTTPException, status
from .protocol import Model, ModelRequest
from memory_api.clients.cozo import client


router = APIRouter()


@router.post("/models/get")
async def get_models(request: ModelRequest) -> Model:
    query = f"""
    input[model_name] <- [[
        "{request.model}",
    ]]

    ?[
        model_name,
        max_length,
        default_settings,
        updated_at,
    ] := input[model_name],
        *models {{
            model_name,
            max_length,
            default_settings,
            updated_at: validity,
            @ "NOW"
        }}, updated_at = to_int(validity)
    """

    try:
        res = [row.to_dict() for _, row in client.run(query).iterrows()][0]
        return Model(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )


@router.post("/models/create")
async def create_models(model: Model):
    query = f"""
    ?[model_name, max_length, default_settings] <- [[
        "{model.model}",
        {model.max_length},
        {model.default_settings},
    ]]

    :put models {{
        model_name,
        max_length,
        default_settings,
    }}
    """

    client.run(query)
