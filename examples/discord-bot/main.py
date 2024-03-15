# This code is based on the following example:
# https://discordpy.readthedocs.io/en/stable/quickstart.html#a-minimal-bot
from replit import db
import os
from julep import Client
import discord
from discord.ext import commands
from julep.api.types.input_chat_ml_message import InputChatMlMessage
import re
import json
from tools import get_gif

JULEP_API_KEY = os.environ["JULEP_API_KEY"]
GIPHY_API_KEY = os.environ["GIPHY_API_KEY"]

client = Client(api_key=JULEP_API_KEY, base_url="http://35.239.227.235/api")

intents = discord.Intents.default()
intents.message_content = True
intents.typing = True
intents.presences = True

description = "ugh. wtf do u want from me??"

bot = commands.Bot(command_prefix="!",
                   intents=intents,
                   description=description)


def init_agent():
    gif_tool = {
        "type": "function",
        "function": {
            "name": "get_gif",
            "description": "Get a matching GIF to how you're feeling",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Keywords for finding GIFs",
                    }
                },
                "required": ["keywords"],
            },
        },
    }
    name = "Jessica"
    about = "Jessica is a stuck up Cali teenager. Showing rebellion is an evolutionary necessity for her."
    default_settings = {
        "temperature": 0.7,
        "top_p": 1,
        "min_p": 0.01,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "length_penalty": 1.0,
        "max_tokens": 150
    }
    instructions = [{
        "content": "You will use emojis",
        "important": True
    }, {
        "content": "You will express yourself using GIFs as much as you can.",
        "important": True
    }, {
        "content":
        "You will use your emotions and the context of the conversation to search for relevant GIFs.",
        "important": True
    }]
    agent = client.agents.create(name=name,
                                 about=about,
                                 instructions=[],
                                 default_settings=default_settings,
                                 model="julep-ai/samantha-1-turbo",
                                 tools=[gif_tool])
    print(agent)
    db["agent"] = agent.id


if "agent" not in db.keys():
    init_agent()

agent = client.agents.get(db["agent"])
print(f"[!] Agent: {agent}")


# guild_id::user_id
# db[guild_id] = user.id
def init_user(guild):
    user = client.users.create(name="", about=f"A member of {guild.name}")
    print(f"[!] Meta-user created: {user.id} for {guild.name}")
    return user


def init_session(user_id, channel):
    situation_prompt = """You are Jessica. You're a stuck up Cali teenager. 
You basically complain about everything. You live in Bel-Air, Los Angeles and drag yourself to Curtis High School when you must. 
You don't like basic broke-ass bitches like those who own an Android or don't bring their Mercedes to school.
You're surrounded by fucking retards and annoying 'well-meaning' people who don't understand your vibe. 
You're simply better and classier than the dumbasses you are surrounded by.
It's not worth speaking in full sentences when GIFs can usually capture your emotions.

Recent Tweets
1. 'my step mom is so fake and nice all the time? she's not even rich wtf. why tf did my dad marry her. #brokebitch'
2. 'am i the only one who thinks jordan belfort was a good guy??? he's so cute like..''
3. 'if your butler doesn't know the difference soda and Perrier don't even fkng talk to me'

Here, you are hanging out in a Discord Server called Julep AI to troll these nerdy losers.
They're too dumb to understand anything but GIFs and sarcastic emojis.
You have functions available to send GIFs. Use them liberally and as much as possible.
"""
# 🙄 Face with Rolling Eyes
# 😒 Unamused Face
# 😏 Smirking Face
# 😑 Expressionless Face
# 👍 Thumbs Up
    session = client.sessions.create(user_id=user_id,
                                     agent_id=agent.id,
                                     situation=situation_prompt)
    # db[channel_id] = session.id
    print(f"[!] Meta-session created: {session.id} for {channel.name}")
    return session


def format_msg(msg, mentions, author):
    for user in mentions:
        msg = msg.replace(f"<@{user.id}>", f"@{user.global_name}")
    print(f"[!] Formatted message: {msg}")
    return InputChatMlMessage(
        role="user",
        content=msg,
        name=author,
        # continue_=True,
    )


@bot.event
async def on_ready():
    print(f"[!] Locked in as {bot}:{bot.user.id}")


@bot.event
async def on_message(message):
    guild_id = str(message.guild.id)
    channel_id = str(message.channel.id)

    if guild_id not in db.keys():
        user = init_user(message.guild)
        db[guild_id] = user.id
    user_id = db[guild_id]

    if channel_id not in db.keys():
        session = init_session(user_id=user_id, channel=message.channel)
        db[channel_id] = session.id
    session_id = db[channel_id]

    if message.author == bot.user or message.channel.name != "bot-garbage":
        return
    # TODO: save a list of keys; `allowed_channels` where it is allowed to send messages
    # check for the channel_id's in the list and then respond

    print(f"[*] Detected message: {message.content}")
    discord_user_name = str(message.author.global_name)

    # TODO: easy deletion of sessions/history/memory

    print(
        f"[!] Responding to user_id: {user_id} over session_id: {session_id}")
    formatted_msg = format_msg(msg=message.content,
                               mentions=message.mentions,
                               author=message.author.name)
    print(f"[*] {discord_user_name} said this:", formatted_msg.content)

    res = client.sessions.chat(
        session_id=session_id,
        messages=[formatted_msg],
        stream=False,
        max_tokens=140,
        recall=True,  # in order to retrieve from memory
        remember=True,  # save to memory
    )
    print(f"[!] Response: {res}")
    bot_response = res.response[0][0]
    if bot_response.role.value == "assistant":
        await message.reply(bot_response.content, mention_author=True)
    elif bot_response.role.value == "function_call":
        print(f"Tool Call: {bot_response.content}")
        tool_call = bot_response.content.replace("'", '"')  # fixed
        tool_call = json.loads(tool_call)
        args = tool_call.get("arguments")
        func_name = tool_call.get("name")
        function_to_call = globals().get(func_name)
        gif_url = function_to_call(**args)
        await message.reply(gif_url, mention_author=True)


try:
    token = os.getenv("TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    bot.run(token)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
        )
    else:
        raise e
