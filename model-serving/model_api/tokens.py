bos_token = "<s>"
eos_token = "<|im_end|>"

bos_token_id: int = 1  # <s>
eos_token_id: int = 32000  # <|im_end|>

tag_ids_map = {
    "me": [528],
    "function_call": [908, 28730, 2845],
    "thought": [1654],
    "situation": [4620],
    "person": [1338],
    "functions": [5572],
    "information": [1871],
}

tag_start_id_map = {tag: ids[0] for tag, ids in tag_ids_map.items()}
