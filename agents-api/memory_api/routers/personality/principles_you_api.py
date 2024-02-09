import httpx
from async_lru import alru_cache
from memory_api.env import (
    client_id,
    client_secret,
    endpoint_base,
    cogito_endpoint,
)


###############
## Endpoints ##
###############

oauth_url = f"https://{client_id}:{client_secret}@{cogito_endpoint}"

me_endpoint = f"{endpoint_base}/api/v2/me"
list_tenants_endpoint = f"{endpoint_base}/api/v1/integration_account_tenant_ids"
tenants_endpoint = f"{endpoint_base}/api/v1/integration_account_tenants"


def users_endpoint(tenant_id):
    return f"{endpoint_base}/api/v1/integration_account_tenants/{tenant_id}/users"


questions_endpoint = f"{endpoint_base}/api/v1/assessment/questions"
answers_endpoint = f"{endpoint_base}/api/v1/assessment/answers"


def shortscale_results_endpoint(accountId):
    return f"{endpoint_base}/api/v1/shortscale_results/{accountId}"


def full_results_endpoint(accountId):
    return f"{endpoint_base}/api/v2/assesment_results/{accountId}"


def pdf_endpoint(accountId):
    return f"{endpoint_base}/api/v1/assessment_results/{accountId}/pdf"


###########
## Utils ##
###########


async def make_request(method: str, url: str, **kwargs):
    async with httpx.AsyncClient() as client:
        req = getattr(client, method.lower())

        response = await req(url, **kwargs)
        response.raise_for_status()
        result = response.json()

    return result


##########
## Auth ##
##########


# Get access token
@alru_cache(maxsize=1, ttl=3000)
async def get_access_token():
    oauth_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    grant_type = "client_credentials"
    scope = "com.principles.kernel/integration_account:use"

    oauth_payload_txt = f"""grant_type={grant_type}&
    client_id={client_id}&
    scope={scope}
    """

    response = await make_request(
        "post", oauth_url, headers=oauth_headers, data=oauth_payload_txt
    )

    access_token = response["access_token"]

    return access_token


# Get Me
async def get_me():
    access_token = await get_access_token()
    access_token_header = dict(Authorization=f"Bearer {access_token}")
    response = await make_request(
        "get",
        me_endpoint,
        headers=access_token_header,
    )
    tenantUser = response["tenantUser"]

    return tenantUser


#########
## Ops ##
#########


# Create tenant
async def create_tenant(name: str = "Julep Tenant"):
    access_token = await get_access_token()
    access_token_header = dict(Authorization=f"Bearer {access_token}")
    tenant_params = dict(fields=dict(name=name))
    response = await make_request(
        "post", tenants_endpoint, headers=access_token_header, json=tenant_params
    )
    tenant = response["tenant"]

    return tenant


# List tenants
@alru_cache(maxsize=1)
async def list_tenants():
    access_token = await get_access_token()
    access_token_header = dict(Authorization=f"Bearer {access_token}")
    response = await make_request(
        "get",
        list_tenants_endpoint,
        headers=access_token_header,
    )
    tenant_ids = response["tenantIds"]

    return tenant_ids


async def get_tenant_id():
    tenantIds = await list_tenants()
    tenantId = tenantIds[0]

    return tenantId


# Create user
async def create_user(email: str, display_name: str, tenant_id: str):
    access_token = await get_access_token()
    access_token_header = dict(Authorization=f"Bearer {access_token}")

    user_params = dict(email=email, displayName=display_name)

    response = await make_request(
        "post", users_endpoint(tenant_id), headers=access_token_header, json=user_params
    )

    tenantUser = response["tenantUser"]

    return tenantUser


# Get assessment questions
async def get_qs(account_id):
    access_token = await get_access_token()
    access_token_header = dict(Authorization=f"Bearer {access_token}")

    assessment_headers = access_token_header | {"x-on-behalf-of": account_id}

    assessment_qs = await make_request(
        "get",
        questions_endpoint,
        headers=assessment_headers,
    )

    return assessment_qs


# Submit assessment answers
async def submit_ans(account_id, answers: list[dict[str, int]]):
    access_token = await get_access_token()
    access_token_header = dict(Authorization=f"Bearer {access_token}")

    assessment_headers = access_token_header | {"x-on-behalf-of": account_id}

    response = await make_request(
        "post", answers_endpoint, headers=assessment_headers, json=dict(answers=answers)
    )

    assessment_progress = response["assessmentProgress"]

    return assessment_progress


# get results
async def get_shortscale_result(account_id):
    access_token = await get_access_token()
    access_token_header = dict(Authorization=f"Bearer {access_token}")

    result_headers = access_token_header | {"x-on-behalf-of": account_id}

    response = await make_request(
        "get",
        shortscale_results_endpoint(account_id),
        headers=result_headers,
    )

    return response["shortscaleResult"]


async def get_full_assesment_result(account_id):
    access_token = await get_access_token()
    access_token_header = dict(Authorization=f"Bearer {access_token}")

    result_headers = access_token_header | {"x-on-behalf-of": account_id}

    response = await make_request(
        "get",
        full_results_endpoint(account_id),
        headers=result_headers,
    )

    return response["assesment"]


async def run_interative(account_id, endstate: str = "shortscaleComplete"):
    questions_so_far = []
    answers_so_far = []

    while not (assessment_qs := await get_qs(account_id))["assessmentProgress"][
        endstate
    ]:
        questions = assessment_qs["questions"]
        questions_so_far.extend(questions)
        new_answers = []

        for q in questions:
            questionNumber = q["number"]
            answerNumber = int(input(f"{q['text']}: (1-7):"))
            new_answers.append(
                dict(questionNumber=questionNumber, answerNumber=answerNumber)
            )

        await submit_ans(account_id, new_answers)

        answers_so_far.extend(new_answers)

    return questions_so_far, answers_so_far
