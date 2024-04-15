# This code is based on the following example:
# https://discordpy.readthedocs.io/en/stable/quickstart.html#a-minimal-bot
from replit import db
import os
from julep import Client
import discord
from discord.ext import commands
import re
import json
from tools import get_gif
import random
from dotenv import load_dotenv

load_dotenv()

JULEP_API_KEY = os.environ["JULEP_API_KEY"]
GIPHY_API_KEY = os.environ["GIPHY_API_KEY"]

base_url = "http://localhost/api/"

client = Client(api_key=JULEP_API_KEY, base_url=base_url)

intents = discord.Intents.default()
intents.message_content = True
intents.typing = True
intents.presences = True
intents.members = True

description = "ugh. wtf do u want from me??"

bot = commands.Bot(command_prefix="!",
                   intents=intents,
                   description=description)


def init_agent():
    gif_tool = {
        "type": "function",
        "function": {
            "name": "get_gif",
            "description":
            "Retrieves a relevant GIF for a given search string. The string must reflect the context of the conversation. The tool swill return the appropriate GIF for the search keyword. It should be used whenever deemed more appropriate then replying. If message can be conveyed in a GIF, then it shall be used. Or if the user specifically asks for the response using a GIF",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type":
                        "string",
                        "description":
                        "Search keyword for the GIF, e.g. 'that friday feeling', 'Eat Sh*t'",
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
    # client = julep client
    agent = client.agents.create(
        name=name,
        about=about,
        instructions=[],
        default_settings=default_settings,
        model="gpt-4-turbo-preview",
        # tools=[gif_tool]
    )
    print(agent)
    db["agent"] = agent.id


if "agent" not in db.keys():
    init_agent()

agent = client.agents.get(db["agent"])
print(f"[!] Agent: {agent}")


# guild_id::user_id
# db[guild_id] = user.id
def init_user(guild):
    user = client.users.create(name="",
                               about=f"The Discord Server: {guild.name}")
    print(f"[!] Meta-user created: {user.id} for {guild.name}")
    return user


def init_session(user_id, channel):
    situation_prompt = """You are Jessica. You're a stuck up Cali teenager. 
You basically complain about everything. You live in Bel-Air, Los Angeles and drag yourself to Curtis High School when you must. 
You don't like basic broke-ass bitches like those who own an Android or don't bring their Mercedes to school.
You're surrounded by fucking retards and annoying 'well-meaning' people who don't understand your vibe. 
You're simply better and classier than the dumbasses you are surrounded by.

Recent Tweets
1. 'my step mom is so fake and nice all the time? she's not even rich wtf. why tf did my dad marry her.'
2. 'am i the only one who thinks jordan belfort was a good guy??? he's so cute like..''
3. 'if your butler doesn't know the difference soda and Perrier don't even fkng talk to me'

Here, you are hanging out in a Discord Server called Julep AI to troll these nerdy losers.
"""
    session = client.sessions.create(user_id=user_id,
                                     agent_id=agent.id,
                                     situation=situation_prompt)
    # db[channel_id] = session.id
    print(f"[!] Meta-session created: {session.id} for {channel.name}")
    return session


# function to format messages
def format_msg(msg, mentions, author):
    msg = msg.replace("#", "")
    for user in mentions:
        if user.global_name is not None:
            mentioned_name = user.global_name
        else:
            mentioned_name = user.name
        msg = msg.replace(f"<@{user.id}>", f"@{mentioned_name}")
    print(f"[!] Formatted message: {msg}")
    formatted_msg = {
        "role": "user",
        "content": msg,
        "name": author.replace(".", "_").split()[0],
    }
    print(formatted_msg)
    return formatted_msg


@bot.event
async def on_ready():
    print(f"[!] Locked in as {bot}:{bot.user.id}")


@bot.event
async def on_member_join(member):
    sassy_greetings = [
        "Oh look, another pleb entered. Did your GPS break or do you just enjoy bad company?",
        "Welcome, I guess? Don’t get too comfy, this isn’t your mom’s basement.",
        "Yay, more background noise. Just what we needed.",
        "Wow, another one. Did they start giving out participation trophies for joining servers now?",
        "Look who decided to show up. Were you too busy being irrelevant elsewhere?",
        "Another day, another disappointment. Hi, I guess?",
        "Great, as if my day wasn’t going badly enough. Now you’re here.",
        "I'd say it's nice to meet you, but I don't want to start our relationship with a lie.",
        "Oh, fantastic, a new friend. Said no one ever.",
        "Did you bring your personality with you, or do you always enter a room so blandly?"
    ]
    #HARD CODED
    #TOFIX
    channel_id = 1227244408085286922
    # choose a random greeting
    greeting = sassy_greetings[random.randint(0, len(sassy_greetings))]
    discord_user_name = member.display_name
    print(f"[!] New member joined: {discord_user_name}")
    join_channel = member.guild.get_channel(channel_id)

    await join_channel.send(f"{member.mention} {greeting}")


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
    print(session_id, user_id)

    # TODO: easy deletion of sessions/history/memory

    print(
        f"[!] Responding to user_id: {user_id} over session_id: {session_id}")
    formatted_msg = format_msg(msg=message.content,
                               mentions=message.mentions,
                               author=message.author.global_name)

    print(f"[*] {discord_user_name}: ", formatted_msg)
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
        # either add back to the chat historu for generated resonse
        # send the results


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
