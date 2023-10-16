from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import UUID4
from .protocol import AnswersRequest
from .db import (
    get_account_query, 
    create_account_query, 
    save_results_query,
    get_user_data,
)
from .principles_you_api import (
    list_tenants,
    create_user,
    get_qs,
    submit_ans,
    get_shortscale_result,
    get_full_assesment_result,
)
from memory_api.clients.worker.worker import add_principles_task
from memory_api.clients.worker.types import AddPrinciplesTaskArgs


router = APIRouter()


@router.get("/personality/{user_id}/questions")
async def get_questions(user_id: UUID4) -> JSONResponse:
    tenant_ids = await list_tenants()
    if not len(tenant_ids):
        raise HTTPException(status_code=400, detail=f"tenants not found: {user_id}")

    account = get_account_query(user_id)
    if account.get("account_id") is None or not len(account.get("account_id")):
        user_data = get_user_data(user_id)
        if not len(user_data):
            raise HTTPException(status_code=400, detail=f"user not found: {user_id}")
        
        user = await create_user(user_data["email"][0], user_data["name"][0], tenant_ids[0])
        account_id = user["account"]["accountId"]
        create_account_query(user_id, account_id)
    else:
        account_id = account["account_id"][0]

    return JSONResponse(await get_qs(account_id))


@router.post("/personality/{user_id}/questions")
async def post_questions(req: AnswersRequest, user_id: UUID4) -> JSONResponse:
    account = get_account_query(user_id)
    if account.get("account_id") is None or not len(account.get("account_id")):
        raise HTTPException(status_code=400, detail=f"account not found for user ID: {user_id}")
    
    account_id = account["account_id"][0]
    resp = await submit_ans(account_id, req.model_dump(by_alias=True)["answers"])

    shortscale_complete = resp.get("shortscaleComplete", False)
    assesment_complete = resp.get("assesmentComplete", False)
    if shortscale_complete or assesment_complete:
        get_result = get_shortscale_result if shortscale_complete else get_full_assesment_result
        results = await get_result(account_id)
        save_results_query(user_id, results, False)
        user_data = get_user_data(user_id)
        await add_principles_task(
            AddPrinciplesTaskArgs(
                scores=results, 
                full=assesment_complete, 
                name=user_data.get("name"), 
                user_id=user_id,
            )
        )

        return JSONResponse(results)

    return JSONResponse(resp)
