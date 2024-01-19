# Capabilities

1. **Science/Knowledge Questions**

* Covers biology, chemistry, physics, and more. Can answer complex questions with high accuracy.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" fullWidth="true" %}
```bash
curl --location 'https://api-alpha.julep.ai/v1/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "prompt": "<|im_start|>What are the physical properties of the tau lepton, and how are they different from the electron and muon?<|im_end|>",
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```json
{
    "id": "cmpl-e05db27115b84ccebf9640d622930a09",
    "object": "text_completion",
    "created": 1699533923,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "text": "<|im_start|> The tau lepton, also known as the tau particle or τ-lepton, is a negatively charged elementary particle that belongs to the lepton family, along with the electron and muon. It has a mass of approximately 1.777 GeV/c², which is significantly heavier than the electron (0.511 MeV/c²) and muon (105.7 MeV/c²).\n\nThe tau lepton has a charge of -1 elementary charge, similar to the electron and muon. It has a spin of -1/2, which is the same as the electron and muon. The tau lepton has a half-life of about 2.9 x 10^(-13) seconds, which is much shorter than the muon's half-life (2.2 x 10^(-6) seconds). This means that the tau lepton decays more rapidly than the muon, but more slowly than the electron, which does not decay.\n\nThe tau lepton's decay modes are also different from those of the electron and muon. The electron primarily decays through a process called \"radiative decay,\" emitting a photon and a neutrino. The muon, on the other hand, primarily decays through the weak force, emitting a neutron, an antineutrino, and a gamma ray. The tau lepton decays through both the weak force and the electromagnetic force, emitting leptons (electrons or muons) and associated neutrinos, as well as photons and gamma rays.\n\nIn summary, the tau lepton is a heavier particle than the electron and muon, with a distinct mass and decay properties. It shares some similarities with the other leptons, such as having a negative charge and a spin of -1/2, but its decay modes and half-life set it apart from the electron and muon.",
            "logprobs": null,
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 27,
        "total_tokens": 458,
        "completion_tokens": 431
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



2. **Therapy/Psychology Dataset**

* Strong knowledge base in psychology and therapy topics, providing nuanced support and guidance.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```bash
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "role": "user",
            "content": "Hi. I wanted to speak to you about my debilitating fear of spiders. What can you suggest?"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```json
{
    "id": "cmpl-567dab5a31fa4e82ae18ca3ebc15f7a2",
    "object": "chat.completion",
    "created": 1699537280,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " I'm happy to help. Arachnophobia, the fear of spiders, can be managed with a variety of techniques. One common approach is exposure therapy, which involves gradually exposing yourself to spiders and their webs in a safe and controlled environment. This can help reduce fear and anxiety and eventually lead to a more positive attitude towards spiders."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 31,
        "total_tokens": 106,
        "completion_tokens": 75
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



3. **Stance evaluation (debates, discussions, negotiations)**

* Determine user stance in discussions or debates.
* Evaluate relevance to specified topics.
* Identify supporting or opposing facts to a stance.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```bash
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "role": "user",
            "content": "Why shouldn'\''t we ban fossil fuels?"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```json
{
    "id": "cmpl-54c6d848c90341d081cdda57921e7afc",
    "object": "chat.completion",
    "created": 1699538556,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 1,
            "message": {
                "role": "assistant",
                "content": " Banning fossil fuels would have several negative consequences. Fossil fuels are a major source of energy, and their sudden removal from the market would likely cause energy shortages and price spikes. This could lead to economic instability and reduced economic growth.\n\nAdditionally, many jobs are dependent on the fossil fuel industry, including mining, transportation, and power generation. A sudden ban could lead to significant unemployment and social unrest.\n\nMoreover, banning fossil fuels without a viable alternative energy source in place could lead to a significant decrease in energy availability, which could impact the quality of life for individuals and communities.\n\nInstead of an outright ban, a gradual transition towards renewable energy sources, alongside government support and incentives, is a more sustainable and equitable approach."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 19,
        "total_tokens": 189,
        "completion_tokens": 170
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



4. **Multi-participant Conversations**

* Manages and analyses conversations involving multiple participants, keeping track of different perspectives.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "role": "system",
            "name": "situation",
            "content": "You are an expert psychologist and acclaimed cognitive behavior researcher. You are listening at an exchange between Anna and Jacob. Anna is expressing a concern about their mental health and Jacob is giving them advice from their perspective. As an expert in the field, think about the exchange and then evaluate whether it'\''s a good advice or not. To back up your evaluation, lay down your reasons for why you think so in detail and add remarks for what Jacob can do better."
        },
        {
            "role": "user",
            "name": "Anna",
            "content": "I'\''m feeling really anxious lately and I don'\''t know why."
        },
        {
            "role": "user",
            "name": "Jacob",
            "content": "Anxiety is just a sign of weakness. You need to toughen up and stop worrying so much. Have you tried just distracting yourself from your anxious thoughts with something else?"
        },
        {
            "role": "assistant",
            "continue": true
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```json
{
    "id": "cmpl-ca94896e115e4374a307fdd61cf9b5e9",
    "object": "chat.completion",
    "created": 1699539408,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " Jacob's advice is not good. It is not supportive or empathetic, and it does not acknowledge Anna's feelings. Additionally, it is not based on any scientific understanding of anxiety. \n\nAnxiety is not a sign of weakness. It is a natural human response to stressors and can occur in varying degrees of intensity. It can be helpful to distract oneself from anxious thoughts, but this should not be the primary solution. \n\nJacob could improve his advice by first validating Anna's feelings, acknowledging that anxiety can be difficult and uncomfortable. He could then suggest seeking professional help, such as talking to a psychologist or psychiatrist, who can provide appropriate treatment and coping strategies. \n\nHe could also recommend some relaxation techniques such as deep breathing, meditation, or mindfulness, which have been scientifically proven to help manage anxiety. It's important to remember that while distraction can be helpful, it is not a long-term solution and can often lead to more anxiety in the long run."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 174,
        "total_tokens": 390,
        "completion_tokens": 216
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



5. **Intent Detection**

* Discerns the underlying intent behind user questions or statements.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "AI Assistant is talking to customer to provide support.",
            "name": "situation",
            "role": "system"
        },
        {
            "content": "Would it be possible to cancel the order I made?",
            "name": "Customer",
            "role": "user"
        },
        {
            "content": "Describe the intent of the customer",
            "name": "thought",
            "role": "system"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-fe4d18b6e52a48bb82eaa6a199d851a0",
    "object": "chat.completion",
    "created": 1699540311,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 1,
            "message": {
                "role": "assistant",
                "content": " The customer wants to cancel the order they made."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 46,
        "total_tokens": 57,
        "completion_tokens": 11
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



6. **Temporal Awareness**

* Excels in understanding and adapting to time-related references and special dates.

{% tabs %}
{% tab title="First Tab" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "Monday, October 10, 2022. Samantha is talking to Christopher. It'\''s Columbus Day!",
            "name": "situation",
            "role": "system"
        },
        {
            "content": "Hey Samantha, do you know what today is?",
            "name": "Christopher",
            "role": "user"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Second Tab" %}

{% endtab %}
{% endtabs %}



7. **Chain of Thought**

* Employs a "chain of thought" approach for complex reasoning and problem-solving.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "Joe is studying a bacteria population.  There are 20 bacteria present at 3:00 p.m. and the population doubles every 3 minutes.  Assuming none of the bacteria die, how many bacteria are present at 3:15 p.m. the same day?",
            "name": "John",
            "role": "user"
        },
        {
            "continue": true,
            "name": "Samantha",
            "role": "assistant"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-a05a1470ab7d44bebabdc5fcf39bb460",
    "object": "chat.completion",
    "created": 1699555229,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " To determine the number of bacteria at 3:15 p.m., we first need to find out how many times the bacteria population doubled since 3:00 p.m. \n\nWe know that the population doubles every 3 minutes, so in 15 minutes (1/4 of an hour), it would have doubled 4 times.\n\nTo calculate the number of bacteria at 3:15 p.m., we can use the formula:\n\nFinal population = Initial population * (2 ^ Number of doubling periods)\n\nPlugging in the values, we get:\n\nFinal population = 20 * (2 ^ 4)\n\nFinal population = 20 * 16\n\nFinal population = 320\n\nSo, there are 320 bacteria present at 3:15 p.m."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 80,
        "total_tokens": 270,
        "completion_tokens": 190
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



8. **Roleplay/Expert Guidance**

* Capable of immersive roleplay and providing expert guidance tailored to the specified expertise level.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "Give three tips for staying healthy.",
            "name": "John",
            "role": "user"
        },
        {
            "continue": true,
            "name": "Samantha",
            "role": "assistant"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-88cb758dce814f57bf1f3e123555a6eb",
    "object": "chat.completion",
    "created": 1699555006,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " Sure, here are three tips for staying healthy:\n\n1. Eat a balanced diet: Make sure to incorporate a variety of fruits, vegetables, whole grains, lean proteins, and healthy fats in your meals. This will provide your body with the nutrients it needs to function properly and help prevent chronic diseases.\n\n2. Exercise regularly: Aim for at least 30 minutes of moderate-intensity physical activity most days of the week. This can help improve your cardiovascular health, strengthen your muscles, and boost your mood.\n\n3. Get enough sleep: Aim for 7-9 hours of sleep per night to give your body and mind the rest they need to function optimally. Lack of sleep can increase your risk of developing chronic diseases, impair your cognitive function, and negatively impact your overall quality of life."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 24,
        "total_tokens": 206,
        "completion_tokens": 182
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



9. **Comprehension**

* **Description**: Deep understanding of the context for effective Q\&A interactions.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "Immunology is a branch of biomedical science that covers the study of immune systems in all organisms. It charts, measures, and contextualizes the: physiological functioning of the immune system in states of both health and diseases; malfunctions of the immune system in immunological disorders (such as autoimmune diseases, hypersensitivities, immune deficiency, and transplant rejection); the physical, chemical and physiological characteristics of the components of the immune system in vitro, in situ, and in vivo. Immunology has applications in numerous disciplines of medicine, particularly in the fields of organ transplantation, oncology, virology, bacteriology, parasitology, psychiatry, and dermatology. Prior to the designation of immunity from the etymological root immunis, which is Latin for '\''exempt'\''; early physicians characterized organs that would later be proven as essential components of the immune system. The important lymphoid organs of the immune system are the thymus and bone marrow, and chief lymphatic tissues such as spleen, tonsils, lymph vessels, lymph nodes, adenoids, and liver. When health conditions worsen to emergency status, portions of immune system organs including the thymus, spleen, bone marrow, lymph nodes and other lymphatic tissues can be surgically excised for examination while patients are still alive.",
            "name": "situation",
            "role": "system"
        },
        {
            "role": "user",
            "name": "John",
            "content": "Can some tissue be examined while the patients are still alive?"
        },
        {
            "continue": true,
            "name": "Samantha",
            "role": "assistant"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-a06436487e204dffb70225bb77652978",
    "object": "chat.completion",
    "created": 1699555795,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " Yes, portions of immune system organs such as the thymus, spleen, bone marrow, lymph nodes and other lymphatic tissues can be surgically excised for examination while patients are still alive. This is done when health conditions worsen to emergency status."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 348,
        "total_tokens": 410,
        "completion_tokens": 62
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



10. **Emotion/Dialog Act Analysis**

* Analyzes and classifies user inputs for emotional content, intensity, and dialog acts.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "Two persons `Anna` and `Bob` are talking to each other. As an AI Model, you are observing the conversation in order to analyze and annotate it. After every reponse from either `A` or `B`, the AI model needs to think about that response and write down the '\''Dialog Act'\'' and the '\''Emotion'\'' expressed in that response as a valid yaml object. Dialog Acts should be one of: neutral,inform, question, directive, commissive. Emotions should be one of: neutral, anger, disgust, fear, happiness, sadness, surprise.",
            "name": "situation",
            "role": "system"
        },
        {
            "content": "Say , Bob , how about going for a few beers after dinner ?",
            "name": "Anna",
            "role": "user"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-42fe7d8def5e4fba9d8063722a4784a7",
    "object": "chat.completion",
    "created": 1699573614,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " Dialog Act: directive\nEmotion: happiness"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 162,
        "total_tokens": 173,
        "completion_tokens": 11
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



11. **Lookup Information**

* Retrieves and cross-references information through combined functions and reasoning.

{% tabs %}
{% tab title="First Tab" %}
{% code overflow="wrap" %}
````bash
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "User is talking to an AI Large Language Model and asking it general knowledge question. The AI must not use prior knowledge or any piece of information not explicitly retrieved from reliable sources.\n\nIn order to call a function, AI just needs to specify the name of the function to call and its arguments as a valid JSON string.",
            "name": "situation",
            "role": "system"
        },
        {
            "content": "Available functions and their signatures as JSON schema:\n\n```\n{\n    \"name\": \"lookup_info\",\n    \"description\": \"In order to ensure that the answer is based on factual, up-to-date information, use this tool for fetching relevant information before answering.\",\n    \"parameters\": {\n        \"type\": \"object\",\n        \"properties\": {\n            \"queries\": {\n                \"type\": \"array\",\n                \"items\": {\n                    \"type\": \"string\"\n                }\n            }\n        }\n    }\n}\n```",
            "name": "functions",
            "role": "system"
        },
        {
            "content": "When did the simpsons first air on television?",
            "name": "John",
            "role": "user"
        },
        {
            "content": "Thought:\n\nIn order to answer this question, I need more information about \"The Simpsons\".",
            "name": "thought",
            "role": "system"
        },
        {
            "content": "{\"name\": \"lookup_info\", \"arguments\": {\"queries\": [\"The Simpsons\", \"When did the simpsons first air on television?\"]}}",
            "role": "function_call"
        },
        {
            "content": "`lookup_info` Result:\n\nQ: When did the Simpsons first air on television as an animated short on the Tracey Ullman Show?\nA: April 19, 1987\n\nQ: When did the Simpsons first air as a half-hour prime time show?\nA: December 17, 1989",
            "name": "information",
            "role": "system"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
````
{% endcode %}
{% endtab %}

{% tab title="Second Tab" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-acca5ae587ef4d2ea6a05b7bcaf31460",
    "object": "chat.completion",
    "created": 1699572799,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " The correct answer is: April 19 , 1987"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 382,
        "total_tokens": 398,
        "completion_tokens": 16
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



12. **Basic knowledge of human anatomy and medicine**

* Possess a foundational understanding of human anatomy and various medical concepts. (For medical advice, strongly recommended to ground on relevant authoritative material and add disclaimers)

{% tabs %}
{% tab title="First Tab" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "I am a student answering a question based on the context given below.",
            "name": "situation",
            "role": "system"
        },
        {
            "content": "In rheumatoid arthritis, the body'\''s immune system misfunctions by attacking healthy cells in the joints causing the release of a hormone that in turn causes pain and swelling. This hormone is normally activated only in reaction to injury or infection. A new arthritis medication will contain a protein that inhibits the functioning of the hormone that causes pain and swelling in the joints.",
            "name": "information",
            "role": "system"
        },
        {
            "content": "Question: The statements above, if true, most strongly support which one of the following conclusions?\nChoices:\nA) Unlike aspirin and other medications that reduce pain and swelling and that are currently available, the new medication would repair existing cell damage that had been caused by rheumatoid arthritis.\nB) A patient treated with the new medication for rheumatoid arthritis could sustain a joint injury without becoming aware of it.\nC) Joint diseases other than rheumatoid arthritis would not be affected by the new medication.\nD) The benefits to rheumatoid arthritis sufferers of the new medication would outweigh the medication'\''s possible harmful side effects.\n\nCorrect answer: B) A patient treated with the new medication for rheumatoid arthritis could sustain a joint injury without becoming aware of it.",
            "name": "thought",
            "role": "system"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Second Tab" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-d216671585c34edba94c02b853942f1b",
    "object": "chat.completion",
    "created": 1699581843,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 1,
            "message": {
                "role": "assistant",
                "content": " The correct answer is B) A patient treated with the new medication for rheumatoid arthritis could sustain a joint injury without becoming aware of it. This is because the new medication inhibits the functioning of the hormone that causes pain and swelling in the joints, which means that any injuries or infections to the joints would not be detected by the patient."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 313,
        "total_tokens": 393,
        "completion_tokens": 80
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



13. **Mathematical Knowledge**

* Delivers mathematical knowledge and computational abilities for complex reasoning and calculations.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "I'\''m seeking your support in calculating the quotient and remainder of 631 and 55. Can you answer it for me?",
            "name": "Anna",
            "role": "user"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-a2d1614ac8cb420587eb90f7d81b3965",
    "object": "chat.completion",
    "created": 1699583949,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " Sure, Anna. I can definitely help with that. So, when you divide 631 by 55, you get 11 with a remainder of 81."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 43,
        "total_tokens": 82,
        "completion_tokens": 39
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



14. **Recursive Summarization**

* Generates summaries and can recursively refine them for denser content.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "As an AI model, you are tasked with summarizing long form content into 1-3 sentences.",
            "name": "situation",
            "role": "system"
        },
        {
            "content": "Customers could soon design their own items, go into a supermarket and have them printed in 3D, if an ambitious major project by Tesco succeeds. The high street retail giant is working on developing new technology for a variety of products in its stores. Ideas include digitally making clothing, furniture, personal gifts and even food in their shops. The supermarket giant is keen to use new technologies to offer a wider range of products to consumers. Company researchers believe 3D printers are a natural progression given that they already offer photo and poster printing . The project could also see Tesco stores repair broken items or print spare parts for a product that has already been purchased. Paul Wilkinson, a lead research specialist with Tesco, revealed the retail giant’s ambitions writing a blog post on tesco.com about the potential of 3D printing. He said: '\''3D printing] could revolutionise the way we view stores and what we can get from them.'\'' Wilkinson, who is heading on a fact-finding mission to San Francisco with a team from Tesco, added in The Grocer magazine: '\''We already print photos and posters in many of our larger stores, so why not other gifts and personalised items? '\''How about letting kids design their own toys and then actually being able to get them made? What if we had a digital catalogue of spare parts for items that you’d bought? 3D printing is burgeoning industry with all manner of objects, such as this gun, now being created. '\''They could be printed on demand and ready for you by the time you’d finished your shopping. You could even take a broken item into store; we could scan it in 3D, repair it digitally and make you a new one. '\''There’s been a lot of buzz recently. It’s great that we have one of the machines to test out and to be able to look at how they might change the way stores work.'\'' He said the Tesco team would be meeting “some of the big names and getting together with lots of start-ups and trying to find that idea or product that might just change the retail world.'\'' This is not the first time 3D technology has attracted headlines after it was revealed recently a printed gun had been digitally made.  The blueprints for the gun were then posted on a website and downloaded over 100,000 times. The Mail on Sunday also printed their own gun and demonstrated how easy it was to get it through immigration and security.",
            "name": "Bob",
            "role": "user"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-23876d5743d842bfa75fea16940073e0",
    "object": "chat.completion",
    "created": 1699585006,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " Tesco is developing new technology for a variety of products in its stores, including 3D printing clothing, furniture, personal gifts, and food. The company believes 3D printers are a natural progression given that they already offer photo and poster printing. This project could also see Tesco stores repair broken items or print spare parts for a product that has already been purchased. Tesco is keen to use new technologies to offer a wider range of products to consumers."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 570,
        "total_tokens": 666,
        "completion_tokens": 96
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



15. **Blogging / Writing**

* Assist with various aspects of content creation, specifically tailored for blogging and writing tasks

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "Maya is writing essays about life advice. These are based on her own experiences and what she has learned from talking to others about the human psychology and how it works.",
            "name": "situation",
            "role": "system"
        },
        {
            "content": "Maya'\''s Autobiography\n\\n\\...I found a form of coaching designed for smart, skeptical people: logical, rigorous, analytical and mind-blowingly effective. It is 100% woo-free, but its results can look and feel like magic. In half a year, I went from not even knowing why I was so miserable to being the calmest person I know, and happier than I thought possible. I learned skills that keep me clear, focused, in tune with myself, moving toward my goals but possessed of a firm belief in my worth no matter my external achievements. In just six months, I learned something profound and essential about how to live better as a human that changed everything for me. And, to my enduring surprise, I learned it from life coaching."
,
            "name": "information",
            "role": "system"
        },
        {
            "content": "There is no Magic Key",
            "role": "user",
            "name": "Maya"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-2564257980d54b44813cf3e54c02d24c",
    "object": "chat.completion",
    "created": 1699587330,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " There is no Magic Key\n\nI sometimes wish there were a magic key to happiness and fulfillment. A pill you could take, or a genie you could wish from, that would just make everything better without any effort on your part.\n\nBut there isn’t.\n\nThe best news we have to share is that creating the life you want is a learnable skill. It’s not always easy, but it is something you can get better at, just like anything else.\n\nThe worst news is that creating the life you want is a learnable skill. It’s not always easy, but it is something you can get better at, just like anything else.\n\nThat means there’s no shortcut. There’s no pill you can take or genie you can wish from that will just make everything better without any effort on your part.\n\nBut it also means that if you put in the effort, you can change your life in ways that are just as profound and lasting as any magic key could provide. You can learn to be the creator of your own life, rather than feeling like it’s happening to you.\n\nOne of the most powerful things I’ve learned from coaching is that we have the ability to create our own reality, right now, regardless of what has happened in the past. We can decide to take stock of what we have and what we want, and to make different choices going forward. We can decide to be the authors of our own lives, rather than feeling like we’re just the audience for someone else’s story.\n\nThat doesn’t mean that we get to pick our circumstances and make them instantly better. It doesn’t mean that we can just think happy thoughts and magically erase any challenges we’re facing. But it does mean that we can decide to take responsibility for our own lives, rather than waiting around for something outside of us to make everything better.\n\nAnd that is a powerful kind of magic, if you ask me."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 230,
        "total_tokens": 649,
        "completion_tokens": 419
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



16. **General-purpose Tasks**

* Handles a broad range of tasks, including translation, email writing, brainstorming, coding, puzzles, jokes, trivia, and explanatory content.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "Definition: You are given a statement written in Kannada. Choose the most logical word from the given 4 options which can be used to replace the <MASK> token in the statement. Output the word from the correct option .\nInput: Statement: ವೃತ್ತಿ ಜೀವನದ ಉತ್ತುಂಗದ ದಿನಗಳಲ್ಲೇ ವೈವಾಹಿಕ ಜೀವನಕ್ಕೆ ಕಾಲಿರಿಸಿದ ವನಿತಾ ನಿರ್ದೇಶಕ <MASK> ಅವರ ಶ್ರೇಷ್ಠ ಚಿತ್ರ ನಾಗಮಂಡಲ(೧೯೯೭)ದಲ್ಲಿನ ಪ್ರಮುಖ ಪಾತ್ರವೊಂದರಲ್ಲಿ ಅಭಿನಯಿಸುವ ಮೂಲಕ ಬೆಳ್ಳಿತೆರೆಗೆ ಮರಳಿದರು. ಆ ನಂತರದಲ್ಲಿ ಪ್ರೀತ್ಸೆ(೨೦೦೦), ಮೆಜೆಸ್ಟಿಕ್(೨೦೦೨), ಏಕಾಂಗಿ(೨೦೦೨), ಗಣೇಶ(೨೦೦೭) ಮತ್ತು ಹುಡುಗರು(೨೦೧೧) ಮುಂತಾದ ಚಿತ್ರಗಳಲ್ಲಿ ಪೋಷಕ ಪಾತ್ರಗಳಲ್ಲಿ ಕಾಣಿಸಿಕೊಂಡು ಉತ್ತಮ ಅಭಿನಯ ನೀಡಿದ್ದಾರೆ.\n\n Option A: ಅಂಬರೀಶ್\n\n Option B: ಟಿ.ಎಸ್.ನಾಗಾಭರಣ\n\n Option C: ದೇವರಾಜ್\u200c\n\n Option D: ಕಾಶಿನಾಥ್\nOutput:",
            "name": "situation",
            "role": "system"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-4c8ce549429b4ed08f9c836462391e31",
    "object": "chat.completion",
    "created": 1699587986,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " ಟಿ.ಎಸ್.ನಾಗಾಭರಣ"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 640,
        "total_tokens": 664,
        "completion_tokens": 24
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



17. **Self-Reflection**

* Engages in self-reflection and mistake analysis to refine responses for accuracy-sensitive tasks.

{% tabs %}
{% tab title="First Tab" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
        {
            "content": "Analyze the following conversation between a User and an LLM-based AI Assistant. Then reflect on the AI'\''s response in the conversation.\n\nUser: Give three tips for staying healthy.\n\nAI Assistant: 1. Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule.",
            "name": "Bob",
            "role": "user"
        },
        {
            "content": "Reflection:\n\nThe AI'\''s response to the given instruction is generally accurate and relevant, providing three clear tips for staying healthy. However, there is still room for improvement in terms of depth, specificity, and personalization. To enhance the quality of the response, the AI could consider the following improvements: \n\n1. Provide more depth and detail: The tips given are quite basic and common. To make the response more valuable, the AI could expand on each tip with more specific advice, such as recommended daily servings of fruits and vegetables, types of exercises for different fitness levels, or the optimal sleep duration for various age groups. \n2. Offer evidence or expert advice: Citing research studies, expert opinions, or guidelines from reputable organizations would lend credibility to the AI'\''s response and make it more informative. For example, the AI could refer to the World Health Organization'\''s recommendations on diet, exercise, and sleep. \n3. Personalize the response: The tips provided are generic and may not cater to the unique needs of different individuals. The AI could improve its response by asking the user for additional information or by considering factors such as age, gender, and fitness level to provide more tailored advice. \n\nBy incorporating these suggestions, the AI could deliver a more comprehensive and helpful response that better addresses the user'\''s needs and offers a higher level of expertise.",
            "name": "thought",
            "role": "system"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Second Tab" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-f08b2c8043c448e5be4d9da65b75e9af",
    "object": "chat.completion",
    "created": 1699588410,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 1,
            "message": {
                "role": "assistant",
                "content": " Updated AI Response:\n\n1. Eat a balanced diet that includes plenty of fruits and vegetables. Aim for at least five servings of fruits and vegetables daily, and choose whole grains over refined carbohydrates. Incorporate lean proteins, such as chicken, fish, or legumes, into your meals. Don't forget to stay hydrated by drinking water throughout the day.\n2. Exercise regularly to keep your body active and strong. The World Health Organization recommends at least 150 minutes of moderate-intensity aerobic exercise or 75 minutes of vigorous-intensity aerobic exercise per week, spread across at least three days. In addition, include muscle-strengthening activities two days per week. Remember to consult with a healthcare professional before starting any new exercise regimen.\n3. Get enough sleep and maintain a consistent sleep schedule. Most adults need 7-9 hours of sleep per night. Establish a regular sleep routine by going to bed and waking up at the same time every day, even on weekends. Create a sleep-friendly environment by keeping your bedroom dark, quiet, and cool. Avoid caffeine and electronic devices before bedtime, and consider practicing good sleep hygiene."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 401,
        "total_tokens": 670,
        "completion_tokens": 269
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



18. **Function Calling**

* Enhances conversations with callable functions for dynamic interactions.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
    {
        "content": "A user is talking to their helpful AI Assistant that can help them accomplish different tasks. In order to do so, the AI has access to various functions that it can call as described below.\n\nIn order to call a function, AI just needs to specify the name of the function to call and its arguments as a valid JSON string. If no appropriate function is available to carry out the user'\''s request, please respond with an error (code: need_function) json in the function call.",
        "name": "situation",
        "role": "system"
    },
    {
        "content": "Available functions and their signatures as JSON schema:\n\n{\n    \"name\": \"generate_anagram\",\n    \"description\": \"Generate an anagram of a given word\",\n    \"parameters\": {\n        \"type\": \"object\",\n        \"properties\": {\n            \"word\": {\n                \"type\": \"string\",\n                \"description\": \"The word to generate an anagram of\"\n            }\n        },\n        \"required\": [\n            \"word\"\n        ]\n    }\n}",
        "name": "functions",
        "role": "system"
    },
    {
        "content": "I need a random number between 1 and 100.",
        "name": "Anna",
        "role": "user"
    },
    {
        "content": "{\"error\": \"No function available that can help me perform this.\", \"error_code\": \"need_function\"}",
        "role": "function_call"
    }
]
,
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-07a21be708f34a268a381370c796d44a",
    "object": "chat.completion",
    "created": 1699589209,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " I'm sorry, but I don't know how to generate a random number for you. Is there anything else I can help you with?"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 280,
        "total_tokens": 311,
        "completion_tokens": 31
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



19. **Coding**

* Assists with coding queries and can generate code snippets or explanations.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
````
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages": [
    {
        "content": "Bob is discussing a function written in Python with Samantha.",
        "name": "situation",
        "role": "system"
    },
    {
        "content": "Hey Samantha! Can you explain this Python function to me?\n\n```python\n '\''def bfs(graph, s, t, parent):\n    # Return True if there is node that has not iterated.\n    visited = [False] * len(graph)\n    queue = [s]\n    visited[s] = True\n\n    while queue:\n        u = queue.pop(0)\n        for ind in range(len(graph[u])):\n            if visited[ind] is False and graph[u][ind] > 0:\n                queue.append(ind)\n                visited[ind] = True\n                parent[ind] = u\n\n    return visited[t]'\''",
        "name": "Bob",
        "role": "user"
    }
]
,
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
````
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-a88901d6308544b19a56bb607b4cdcad",
    "object": "chat.completion",
    "created": 1699589488,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " This function performs a breadth-first search on a graph. It takes in the graph, a starting node (s), an ending node (t), and a parent array. It uses a queue to traverse the graph and returns True if"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 191,
        "total_tokens": 241,
        "completion_tokens": 50
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}



20. &#x20;**General Conversations**

* Engages in general conversations spanning various topics, including philosophy and everyday scenarios.

{% tabs %}
{% tab title="Request" %}
{% code overflow="wrap" %}
```
curl --location 'https://api-alpha.julep.ai/v1/chat/completions' \
--header 'Authorization: Bearer <API_KEY>' \
--header 'Content-Type: application/json' \
--data '{
    "model": "julep-ai/samantha-1-turbo",
    "messages":[
    {
        "content": "Samantha is talking to Leslie about topics that she is interested in.",
        "name": "situation",
        "role": "system"
    },
    {
        "content": "Hey Samantha, I'\''ve been thinking about my work environment. I guess I could use some advice on how to deal with a tough situation.",
        "name": "Leslie",
        "role": "user"
    },
    {
        "content": "Of course Leslie, I'\''m here to help. What'\''s been going on?",
        "name": "Samantha",
        "role": "assistant"
    },
    {
        "content": "It'\''s my manager. He doesn'\''t seem to really understand the work but he keeps calling the shots and it'\''s frustrating.",
        "name": "Leslie",
        "role": "user"
    },
    {
        "content": "I see. Leslie, consider this perspective: a great manager doesn'\''t necessarily do the work - they coordinate it. Imagine an orchestra conductor, they don'\''t play an instrument, but they guide everyone to create harmonious music.",
        "name": "Samantha",
        "role": "assistant"
    },
    {
        "content": "I'\''ve tried telling him that he'\''s being too controlling, but he doesn'\''t seem to get it.",
        "name": "Leslie",
        "role": "user"
    },
    {
        "content": "A truly effective manager knows how to lead, inspire, and provide direction. They should empower and encourage their team, not criticize them.",
        "name": "Samantha",
        "role": "assistant"
    },
    {
        "content": "I spoke up about it and he just brushed me off, said he was busy.",
        "name": "Leslie",
        "role": "user"
    }
]
,
    "temperature": 0.6,
    "max_tokens": 600,
    "best_of": 2
}'
```
{% endcode %}
{% endtab %}

{% tab title="Response" %}
{% code overflow="wrap" %}
```
{
    "id": "cmpl-a1bef14e492d4409b98e2dc195ae67ed",
    "object": "chat.completion",
    "created": 1699597316,
    "model": "julep-ai/samantha-1-turbo",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " Leslie, your input is valuable. If you're being ignored, it might be time to escalate the issue. You could speak to his supervisor or another manager you trust."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 281,
        "total_tokens": 320,
        "completion_tokens": 39
    }
}
```
{% endcode %}
{% endtab %}
{% endtabs %}

\
