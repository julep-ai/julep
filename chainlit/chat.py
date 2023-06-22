from collections import deque
import itertools as it
import random
from threading import Thread
from typing import Literal, Optional, TypedDict

import chainlit as cl
from chainlit import user_session

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer,
)


###########
## Types ##
###########

class ChatMLMessage(TypedDict):
    name: Optional[str] = None
    role: Literal["assistant", "system", "user"]
    content: str

ChatML = list[ChatMLMessage]

# Example:
# [
#     {"role": "system", "name": "situation", "content": "I am talking to Diwank"},
#     {"role": "assistant", "name": "Samantha", "content": "Hey Diwank"},
#     {"role": "user", "name": "Diwank", "content": "Hey!"},
# ]

############
## Consts ##
############

AGENT_NAME: str = "Samantha"


###########
## Model ##
###########

# assistant_model_id = "julep-ai/samantha-7b-ds-03"
# assistant_model = AutoModelForCausalLM.from_pretrained(assistant_model_id, torch_dtype=torch.bfloat16, device_map="auto")

# Load model and tokenizer
# model_id = "julep-ai/samantha-33b-0"
# tokenizer_id = "timdettmers/guanaco-65b-merged"
model_id = "julep-ai/samantha-33b-ds-03"
tokenizer_id = "julep-ai/samantha-33b-ds-03"

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(tokenizer_id, use_fast=False)

# warmup
model.generate(**tokenizer("Hello", return_tensors="pt").to(0), max_new_tokens=2)

print("Model loaded")


##############
## Generate ##
##############

class StopSequenceCriteria(StoppingCriteria):
    def __init__(
        self,
        tokenizer,
        stop: list[str],
        input_length,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        
        self.stop = stop
        self.tokenizer = tokenizer
        self.input_length = input_length

    def __call__(
        self,
        input_ids: torch.LongTensor,
        scores: torch.FloatTensor,
        **kwargs,
    ) -> bool:

        input_ids = input_ids.long().tolist()
        new_input_ids = [i[self.input_length:] for i in input_ids]
        
        for text in self.stop:
            generated_so_far = ""
            
            for input_id in new_input_ids:
                decoded = self.tokenizer.decode(input_id, skip_special_tokens=False)
                generated_so_far += decoded

                if text in generated_so_far:
                    return True

        return False


def message_role_to_prefix(message: ChatMLMessage) -> str:
    match message:
        case {"role": "system", "name": name, **rest}:
            return name
        case {"role": "user", "name": name, **rest}:
            return f"person ({name})" if name else "person"
        case {"role": "assistant", "name": name, **rest}:
            return f"me ({name})" if name else "me"


def to_prompt(
    messages: ChatML,
    bos: str = "<|section|>",
    eos: str = "<|endsection|>",
    suffix: str = f"\n<|section|>me ({AGENT_NAME})\n",
) -> str:
    # Input format:
    # [
    #     {"role": "system", "name": "situation", "content": "I am talking to Diwank"},
    #     {"role": "assistant", "name": "Samantha", "content": "Hey Diwank"},
    #     {"role": "user", "name": "Diwank", "content": "Hey!"},
    # ]
    
    # Output format:
    #
    # <|section|>situation
    # I am talking to Diwank<|endsection|>
    # <|section|>me (Samantha)
    # Hey Diwank<|endsection|>
    # <|section|>person (Diwank)
    # Hey<|endsection|>
    # <|section|>me (Samantha)\n
    

    prompt = "\n".join([
        f"{bos}{message_role_to_prefix(message)}\n{message['content']}{eos}"
        for message in messages
    ])

    return prompt + suffix


def groupwise(iterable, n):
    """Like itertools.pairwise but for n elements"""

    accum = deque((), n)
    count = 0
    
    for element in iterable:
        accum.append(element)
        count += 1
        
        if len(accum) == n:
            yield tuple(accum)

    if count < n:
        yield tuple(accum)


def wrap_iterator(iterator):
    for item in iterator:
        yield item

# TODO: Turn this into accepting regular expressions instead
def remove_stops(iterator, tokenizer, stop: list[str] = []):

    # If there's nothing to check yield everything as is
    if not stop:
        yield from iterator
        return

    # We need to look ahead n number of tokens so that,
    #   we can check if a stop sequence is coming up
    #   and not yield starting part of the stop sequence.

    # Look ahead by len of largest stop sequence
    look_ahead = max([
        len(tokenizer.encode(s, add_special_tokens=False))
        for s in stop
    ])

    # Group tokens into look_ahead groups
    for items in groupwise(iterator, look_ahead):

        # Check if group has a stop sequence
        joined = "".join(items).strip()
        has_stop_sequence = {s: joined.endswith(s) for s in stop}

        # If so, yield tokens minus stop sequence and return
        if any(has_stop_sequence.values()):
            # which stop sequence was found?
            offending_sequence = next(s for s, is_bad in has_stop_sequence.items() if is_bad)

            # remove that bit, yield and exit
            yield joined.split(offending_sequence)[0]
            return

        # Otherwise, keep yielding the first item in the group
        first, *_ = items
        
        if first.strip():
            yield first


def generate(
    messages: ChatML,
    stop: list[str] = [],
    timeout: int = 15,
    stream: bool = False,
    **kwargs
) -> TextIteratorStreamer | str:
    
    # Prepare input
    prompt = to_prompt(messages)
    inputs = tokenizer(prompt, return_tensors="pt").to(0)
    input_length = len(inputs["input_ids"].squeeze().tolist())

    # Stopping criteria
    stopping_criteria = (
        StoppingCriteriaList([StopSequenceCriteria(
            tokenizer=tokenizer,
            stop=stop,
            input_length=input_length,
        )])
        if stop else None
    )

    # Generation parameters
    generation_kwargs = {
        # defaults
        "max_new_tokens": 40, 
        "repetition_penalty": 1.02,
        "no_repeat_ngram_size": 4,
        "renormalize_logits": True,
        "temperature": 1.1,
        #
        # overrides
        **kwargs,
        #
        # required params
        "stopping_criteria": stopping_criteria,
        # "assistant_model": assistant_model,
        #
        # add inputs
        **inputs,
    }

    # If not streaming, run directly and return result
    if not stream:
        [output] = model.generate(**generation_kwargs)
        result = tokenizer.decode(output[input_length:], skip_special_tokens=False)

        # Remove the stop sequence at the end (needed)
        for s in stop:
            result = result.split(s)[0].strip()
        
        return result
    
    # If streaming, prepare streamer
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, timeout=timeout, skip_special_tokens=False)
    generation_kwargs["streamer"] = streamer

    # and start generating in new thread
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    
    # stop sequence filter
    return remove_stops(streamer, tokenizer, stop)


##############
## Chainlit ##
##############

def extend_history(messages: ChatML) -> ChatML:

    # Get history
    history = user_session.get("history")
    assert isinstance(history, list), "history not set in session"

    # Extend history
    new_history = [*history, *messages]
    user_session.set("history", new_history)

    return new_history


@cl.on_chat_start
async def main():

    # Init
    name = user_session.get("name")
    history = user_session.get("history")

    # Set empty history on start
    if not history:
        user_session.set("history", [])

    # Ask for name and push to history
    if not name:
        
        # Prompt user for name
        prompt_name = "Hi! What's your name?"
        res = await cl.AskUserMessage(
            content=prompt_name + " (just first name is good)",
            author=AGENT_NAME,
            timeout=3600,
        ).send()

        # Timed out? Exit
        if not res:
            return

        # Process name change
        name = res["content"]
        hey_name = f"Hey {name}! Nice to meet you."

        await cl.sleep(random.randint(1, 2))
        await cl.Message(content=hey_name, author=AGENT_NAME).send()

        # Set name in session
        user_session.set("name", name)

        # Add init messages to history
        extend_history([
            ChatMLMessage(role="system", name="situation", content=f"I am talking to {name}."),
            ChatMLMessage(role="assistant", name=AGENT_NAME, content=prompt_name),
            ChatMLMessage(role="user", name=name, content=name),
            ChatMLMessage(role="assistant", name=AGENT_NAME, content=hey_name),
        ])


@cl.on_message
async def handler(message: str):

    # Prepare prompt
    user_name = user_session.get("name")
    
    chatml = extend_history([
        ChatMLMessage(role="user", name=user_name, content=message),
    ])
    
    prompt = to_prompt(chatml)

    # LLM settings
    llm_settings = dict(
        max_new_tokens=80, 
        stop=["<|", "\n\n", "? ?", "person (", "???", "person(", "? person", ". person"],
        temperature=1.3,
    )

    # Generate streaming response
    response_stream = generate(
        chatml,
        stream=True,
        **llm_settings,
    )

    # Stream response back to the user
    cl_message = cl.Message(
        content="",
        author=AGENT_NAME,
        prompt=prompt,
        llm_settings=cl.LLMSettings(**llm_settings),
    )

    # Also collect tokens to add to agent history
    response = ""
    for token in response_stream:
        response += token
        print(response)
        
        await cl_message.stream_token(token)

    # Add agent response to history
    extend_history([
        ChatMLMessage(role="assistant", name=AGENT_NAME, content=response),
    ])
    
    # Finalize message
    await cl_message.send()
