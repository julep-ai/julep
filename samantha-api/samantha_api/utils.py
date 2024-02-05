from jsonschema import validate


_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Function name",
            },
            "description": {
                "type": "string",
                "description": "Function description",
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                    },
                    "properties": {
                        "type": "object",
                    },
                    "required": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True,
                    },
                },
                "required": [
                    "type",
                    "properties",
                ],
            },
        },
        "required": [
            "name",
            "description",
            "parameters",
        ],
    },
}


def validate_functions(functions: list[dict]):
    validate(instance=functions, schema=_schema)
