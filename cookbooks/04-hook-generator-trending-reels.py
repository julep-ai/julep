

# %%
# Global UUID is generated for agent and task
import time, yaml
from dotenv import load_dotenv
import os
import uuid
load_dotenv(override=True)

AGENT_UUID =  uuid.uuid4()
TASK_UUID = uuid.uuid4()
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
RAPID_API_HOST = os.getenv('RAPID_API_HOST')
JULEP_API_KEY = os.getenv('JULEP_API_KEY') or os.getenv('JULEP_API_KEY_LOCAL')

print(f'AGENT_UUID: {AGENT_UUID}')
print(f'TASK_UUID: {TASK_UUID}')
print(f'JULEP_API_KEY: {JULEP_API_KEY}')
print(f'RAPID_API_KEY: {RAPID_API_KEY}')
print(f'RAPID_API_HOST: {RAPID_API_HOST}')


# ### Creating Julep Client with the API Key

from julep import Client
# # Create a client
client = Client(api_key=JULEP_API_KEY,environment="dev")

#  Creating an agent for handling persistent sessions
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Session Manager",
    about="An AI agent specialized in managing persistent sessions and context.",
    model="gpt-4o",
)

# ### Creating a Document for Hooks
hooks_data = [
    {"categories": "Price-Focused",
     "content": [
         "Save both time and money with [product].",
         "Save both time and money on [task].",
         "Is [product] worth the price? Let’s find out!",
         "Why is it challenging and costly to find a good [product category]?",
         "Searching for an affordable [product type]? Check this out!",
         "How to locate an affordable [service].",
         "I can’t believe this costs only [price].",
         "Don't waste your money on [X]; instead buy [X]."
     ]},
    {"categories": "Informative",
     "content": [
         "What’s inside [product]?",
         "Common questions I get about [product].",
         "Now you can get X delivered right to your door.",
         "Thinking of trying [product type]?",
         "Allow me to introduce you to [product].",
         "[category] Tip #X.",
         "Here’s how to achieve [value prop].",
         "I know this sounds unbelievable, but…",
         "How to get X done in just 10 minutes.",
         "How to find time for X.",
         "Here’s my biggest life hack for X.",
         "Add more [value prop] to your day."
     ]},
    {"categories": "Versus the Alternative (or Competition)",
        "content": ["Before you try [product type], watch this first.",
                    "Hate [the worse alternative]? Give this a try!",
                    "Thinking about [worse alternative]?",
                    "Instead of [worse alternative], try this.",
                    "Still using [the worse alternative to the product]? Watch this.",
                    "Something that’s always annoyed me about X.",
                    "Don’t buy X that doesn’t work. Try this instead.",
                    "I tested every [product category] so you don’t have to: here’s what I found.",
                    "Stop doing [worse alternative]. Try [product] instead.",
                    "Dealing with [negative experience]? I used [product] to help.",
                    "Why millennials are switching to [product].",
                    "How to do X without [worse alternative].",
                    "I only get my [product category] from [brand name].",
                    "I no longer buy my [product category] from [worse alternative].",
                    "[Worse alternative] can be difficult to deal with.",
                    "Your new X alternative.",
                    "[value prop] without the [negative side effect].",
                    "I kept experiencing [pain point], so I tried this instead!",
                    "If you have [pain point] — you need to see this!",
                    "I wanted to stop doing X, so I tried this instead.",
                    "Your X isn't [adverb]; you just need X.",
                    "My secret to [popular trend] revealed!"
                    ]},
    {"categories": "User Experience",
     "content": [
         "Guys, it’s here…",
         "What I ordered vs. what I received.",
         "[Product] unboxing.",
         "Let’s create X with [product].",
         "POV: You tried [product].",
         "A day in the life of X.",
         "Get ready with me to do [task].",
         "“Put a finger down” [product category] edition.",
         "Trying home remedies for X.",
         "[Product category] ASMR."
     ]},
    {"categories": "Responding to Hype",
     "content": [
         "TikTok made me try [product].",
         "Things TikTok made me try #13.",
         "This [product type] is going viral on [social media platform].",
         "I tested the viral [product type] to see if it lives up to the hype.",
         "This [product type] has over 5,000 reviews… let’s see if it’s worth it.",
         "[Publication] can’t stop raving about us.",
         "It’s so good it sold out in a week."
     ]},
    {"categories": "It’s Easier",
     "content": [
         "Are you [accomplishing the goal optimally]?",
         "Life Hack: Try [product] for [pain point].",
         "My go-to [product] for [pain point].",
         "How to easily [task].",
         "[Task] has never been easier than with [product].",
         "My favorite [product] to make [hard task] simpler.",
         "Here’s my top product for [task].",
         "Struggling to do [task]?",
         "I’ve been struggling with [task], but [product] has really helped.",
         "Easiest way to do [task]?",
         "Make your week easier.",
         "Why adults avoid [task]… [product] makes it easy.",
         "[Product] made [task] so much easier! You’ve got to try it.",
         "When I use [product], it’s one less thing I have to worry about.",
         "How to do [X] in half the time.",
         "This trick/hack/method will save you hours...",
         "Easy hack to [X]...",
         "Simple [X] that will make you [X]."
     ]},
    {"categories": "Lists",
     "content": [
         "5 Ways [product] Helps with [pain point].",
         "3 reasons to buy [product].",
         "3 reasons to try [service].",
         "Get [value prop] in 3 steps.",
         "Here are 3 ways [worse alternative] affects your life.",
         "5 things you didn’t know about [topic].",
         "The ultimate [X] checklist to [action].",
         "Reasons why [X].",
         "Here are the 3 best ways to [X].",
         "Here are [X] mistakes you might be making...",
         "If you want [X], do these 5 things..."
     ]},
    {"categories": "The Best",
     "content": [
         "The internet’s #1 [product type].",
         "The best way to [accomplish the goal of the product].",
         "What makes [the product type] the best?",
         "My skin has never looked better with [product].",
         "The best way to find X in 2022.",
         "[Product] changed how I do [task], and I’m never going back.",
         "Why is [product] so good though?",
         "After hours of researching, I found the best [product type] for [task].",
         "I found the best [product category] for [value prop].",
         "This is going to blow your mind.",
         "How I got [X] in 24 hours.",
         "Must-have [products] for [X].",
         "The best [target audience] know something that you don't."
     ]},
    {"categories": "Other Video Hooks that Address Viewers Directly",
        "content": [
            "Hey, [customer type], you’ve got to try this.",
            "People looking for [product category], stop scrolling.",
            "Wait, have you tried X?",
            "Take control of your X with [product].",
            "Imagine if X was also X.",
            "Watch this if you X."
        ]},
    {"categories": "Facts & Stats",
     "content": [
         "PSA: [statement about product category].",
         "Did you know? [fact about product category].",
         "I just found out [fact about product category].",
         "Are you one of [fact about product category] people who do X?",
         "New customers get [discount].",
         "Take [discount] off when you try [product].",
         "I didn’t know X could be related to X.",
         "Why is it important to [do product-related task]?",
         "99\% of your [target audience] don't. To be the 1% you need to [X].",
         "This [product] is the secret to [X]."
     ]},
    {"categories": "Curiosity & Engagement",
     "content": [
         "Is there anything worse than [X]?",
         "I will never [adjective] from learning this.",
         "X people start scrolling. I have the perfect [X] for you.",
         "Here's a challenge for you...",
         "There's nothing more painful than [X].",
         "What would you do if...",
         "Watch till the end…"
     ]},
    {"categories": "Negative Hooks",
     "content": [
         "Why you're failing at [activity].",
         "The worst mistake you can make in [subject].",
         "Avoid these common pitfalls in [topic].",
         "The dark side of [popular trend].",
         "Don't be fooled by [misconception].",
         "Why [common practice] is ruining your [outcome].",
         "What no one tells you about [issue].",
         "The hidden dangers of [activity].",
         "Stop doing this if you want to succeed in [field].",
         "The ugly truth about [common belief].",
         "Why [habit] is wasting your time.",
         "Exposing the myths about [topic].",
         "The biggest regret you'll have in [situation].",
         "How [action] is destroying your [goal].",
         "The shocking reality of [popular topic].",
         "Why [trend] is a bad idea.",
         "The real reason you're not seeing results in [field].",
         "The downside of [seemingly positive aspect].",
         "What you should never do in [activity].",
         "Why [common advice] is actually harmful."
     ]}
]

hooks_doc_content = []
for category in hooks_data:
    hooks_doc_content.extend(category['content'])

doc = client.agents.docs.create(
    agent_id=AGENT_UUID, title="hooks_doc", content=hooks_doc_content)
print(doc.id)

# ####Listing the Documents
for doc in client.agents.docs.list(agent_id=AGENT_UUID):
    print(doc.content)

#  Defining a Task
import yaml
task_def = yaml.safe_load(f"""
name: Trending Reels Hook Generator

tools:
- name: api_tool_call
  type: api_call
  api_call:
    method: GET
    url: "https://instagram-scraper-api3.p.rapidapi.com/reels_by_keyword"
    headers:
      x-rapidapi-key: "{RAPID_API_KEY}"
      x-rapidapi-host: "{RAPID_API_HOST}"
    follow_redirects: true

- name: get_hooks_doc
  type: system
  system:
    resource: agent
    subresource: doc
    operation: list

main:

- tool: api_tool_call
  arguments:
    params:
      query: "inputs[0].topic"

- evaluate:
    summary: "list({{
              'caption': ((clip.get('media') or {{}}).get('caption') or {{}}).get('text') or 'No Caption Available',
              'code': (clip.get('media') or {{}}).get('code') or 'No Code Available',
              'media_id': ((clip.get('media') or {{}}).get('caption') or {{}}).get('media_id', 0),
              'video_duration': (clip.get('media') or {{}}).get('video_duration', 0),
              'thumbnail_url': (clip.get('media') or {{}}).get('image_versions2', {{}}).get('candidates', [{{}}])[0].get('url') or 'No Thumbnail URL Available',
              'video_url_360': [video.get('url') for video in (clip.get('media') or {{}}).get('video_versions', [{{}}]) if video.get('width') == 360][0] if [video.get('url') for video in (clip.get('media') or {{}}).get('video_versions', [{{}}]) if video.get('width') == 360] else 'No URL Available',
              'video_url_720': [video.get('url') for video in (clip.get('media') or {{}}).get('video_versions', [{{}}]) if video.get('width') == 720][0] if [video.get('url') for video in (clip.get('media') or {{}}).get('video_versions', [{{}}]) if video.get('width') == 720] else 'No URL Available',
              'play_count': (clip.get('media') or {{}}).get('play_count', 0),
              'like_count': (clip.get('media') or {{}}).get('like_count', 0),
              'comment_count': (clip.get('media') or {{}}).get('comment_count', 0),
              'reshare_count': (clip.get('media') or {{}}).get('reshare_count', 0),
              'has_audio': (clip.get('media') or {{}}).get('has_audio', False),
              'audio_type': (clip.get('media') or {{}}).get('clips_metadata', {{}}).get('audio_type', 'No Audio Type Available'),
              'username': (clip.get('media') or {{}}).get('user', {{}}).get('username') or 'No Username Available',
              'full_name': (clip.get('media') or {{}}).get('user', {{}}).get('full_name') or 'No Full Name Available',
              'profile_pic_url': (clip.get('media') or {{}}).get('user', {{}}).get('profile_pic_url') or 'No Profile Pic URL Available',
              'virality_score': (clip.get('media') or {{}}).get('reshare_count', 0) / ((clip.get('media') or {{}}).get('play_count', 1) if (clip.get('media') or {{}}).get('play_count', 0) > 0 else 1),
              'engagement_score': (clip.get('media') or {{}}).get('like_count', 0) / ((clip.get('media') or {{}}).get('play_count', 1) if (clip.get('media') or {{}}).get('play_count', 0) > 0 else 1)
              }} for clip in _['json']['data']['reels_serp_modules'][0]['clips'])"

- over: _['summary']
  parallelism: 4
  map:
    prompt:
      - role: system
        content: >-
          You are a skilled agent tasked with creating a single description for each trending real estate reel for the given topic: {{{{inputs[0].topic}}}}.
          Use information gathered from the following data sources to gather the most relevant information:

          Search Results: {{{{_['caption']}}}}
          Virality Score: {{{{_['virality_score']}}}}
          Engagement Score: {{{{_['engagement_score']}}}}

          Provide a json repsonse containing the caption, virality score, enagement score and one-liner description for the reel.
    unwrap: true   

- evaluate:
    summary: outputs[1]['summary']
    description: list(load_json(res.replace("```json", "").replace("```", "")) for res in _)

- tool: get_hooks_doc
  arguments:
    agent_id: "'{AGENT_UUID}'"
                          
- evaluate:
    hooks_doc: _[0]['content']

- over: outputs[3]['description']
  parallelism: 4
  map:
    prompt:
      - role: system
        content: >-
          You are a skilled content creator tasked with generating 3 engaging video hooks for each reel having its description and caption. Use the following document containing hook templates to create effective hooks:
          
          {{{{_.hooks_doc}}}}
          
          Here are the caption and description to create hooks for:

          Caption: {{{{_['caption']}}}}
          Description: {{{{_['description']}}}}
          Virality Score: {{{{_['virality_score']}}}}
          Engagement Score: {{{{_['engagement_score']}}}}

          Your task is to generate 3 hooks (for the reel) by adapting the most suitable templates from the document. Each hook should be no more than 1 sentence long and directly relate to its corresponding idea.
          
          Basically, all the ideas are taken from a search about this topic, which is {{{{inputs[0].topic}}}}. You should focus on this while writing the hooks.

          Ensure that each hook is creative, engaging, and relevant to its idea while following the structure of the chosen template.

          Provide a json repsonse containing the caption, virality score, enagement score, description and the list of 3 hooks for the reel.
    unwrap: true

- evaluate:
    summary: outputs[3]['summary']
    hooks: list(load_json(res.replace("```json", "").replace("```", "")) for res in _)
""")

# Creating/Updating a task
task = client.tasks.create_or_update(
    task_id=TASK_UUID,
    agent_id=AGENT_UUID,
    **task_def
)

# Creating an execution of the task
execution = client.executions.create(
    task_id=task.id,
    input={
        "topic": "halloween snacks"
    }
)

# Waiting for the execution to complete
import time
time.sleep(120)

# Lists all the task steps that have been executed up to this point in time
transitions = client.executions.transitions.list(execution_id=execution.id).items

# Transitions are retreived in reverse chronological order
for transition in reversed(transitions):
    print("Transition type: ", transition.type)
    print("Transition output: ", transition.output)
    print("-"*50)

import json
response = client.executions.transitions.list(execution_id=execution.id).items[0].output
print(json.dumps(response, indent=4))



