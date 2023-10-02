from typing import Union, List, Dict
from pydantic import BaseModel


class Instances(BaseModel):
    instances: Union[Dict, List[Dict], List[str]]
