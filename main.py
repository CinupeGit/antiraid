import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import datetime
import asyncio
import base64
import json
import os


b64token = open('assets/token.txt', 'r').read().strip()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.help_command = None


previousmsg = ''
antispammsgtime = {}
previousmsgcount = 0
channelcount = 0
antichannelspamcount = 0

@bot.event
async def on_message(message):
    '''Prevent channels from being spammed and remove duplicate messages.'''
    global previousmsgcount
    global messageperminute
    global previousmsg

    if message.author.id != bot.user.id:
        if message.content == previousmsg:
            previousmsgcount += 1
        else:
            previousmsg = message.content
            previousmsgcount = 1

        if previousmsgcount > 19:
            if message.author.bot:
                try:
                    await message.author.kick(reason=f'Raid bot detected, or bot token was leaked. Please reset any bot tokens immediately!')
                except Exception as e:
                    print(f'Tried to removed the bot {message.author.name}, but failed because {e}')
                else:
                    print(f'Successfully kicked the user {message.author.user}')
            else:          
                fivemins = datetime.datetime.now(timezone.utc) + timedelta(minutes=5)
                try:
                    await message.author.timeout(fivemins, reason=f'Spammed {message.content}')
                except Exception as e:
                    print(f'Tried to timeout the user {message.author.name}, but failed because {e}')

        if previousmsgcount > 2:
            try:
                await message.reply(f'<@{message.author.id}>: found {previousmsgcount} duplicate messages.')
            except Exception as e:
                print(f'Tried to send a reply in a guild, but failed because {e}')

            print(f'{message.author.name} keeps spamming!')

            await message.delete()

            async for msg in message.channel.history(limit=50):
                if message.content.lower() == msg.content.lower():
                    await msg.delete()

            await asyncio.sleep(5)
            async for msg in message.channel.history(limit=50):
                if msg.author.id == bot.user.id:
                    await msg.delete()


    antispamtime = datetime.datetime.now(timezone.utc)

    if message.attachments:
        antispamtime -= datetime.timedelta(seconds=0.5)


    if message.author.id in antispammsgtime and message.author.id != bot.user.id:
        antispamtimediff = (antispamtime - antispammsgtime[message.author.id]).total_seconds()
        if antispamtimediff > 0:
            usermpm = 60 / antispamtimediff

            if usermpm > 110:
                await message.reply(f'<@{message.author.id}>: found spamming at {usermpm:.2f} messages per minute')

                await message.delete()

                async for msg in message.channel.history(limit=50):
                    if msg.content.lower() == message.content.lower():
                        await msg.delete()

                await asyncio.sleep(5)
                async for msg in message.channel.history(limit=50):
                    if msg.author.id == bot.user.id:
                        await msg.delete()
    else:
        usermpm = 0

    antispammsgtime[message.author.id] = antispamtime



lastchannelcheck = datetime.datetime.now()
lastchanneldel = datetime.datetime.now()

@bot.event
async def on_guild_channel_create(channel):
    '''Prevent channels from being created too fast to prevent raids.'''

    global channelcount
    global lastchannelcheck
    async for log in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
        suspect = log
        break
    if suspect.id == bot.user.id:
        return
    getcurrentdates = datetime.datetime.now()
    if (getcurrentdates - lastchannelcheck).seconds > 10:
        channelcount = 0
        lastchannelcheck = getcurrentdates


    guild = channel.guild
    for channel in guild.channels:
        channelname = channel.name.lower()

        if 'raid' in channelname or 'hack' in channelname or 'hacked' in channelname or 'bot' in channelname or 'nuke' in channelname or 'nuked' in channelname:
            channelcount += 1

    if channelcount > 4:
        await channel.delete()
        try:
            await suspect.kick(reason='Found suspect with permissions to create channels via audit log.')
        except Exception as e:
            print(f'Tried to kick the user {suspect.user}, but failed because {e}')
        else:
            print(f'Successfully kicked the user {suspect.user}')
        dmsuspect = await bot.fetch_user(suspect.user.id)
        try:
            await dmsuspect.send('You\'ve been detected for the rapid addition of channels in a guild.')
        except Exception as e:
            print(f'Tried to DM {suspect.user}, but failed because {e}')


@bot.event
async def on_guild_channel_delete(channel):
    '''Prevent channels from being removed too fast to prevent raids'''
    global lastchanneldel
    global antichannelspamcount

    async for log in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        suspect = log
        break

    if suspect.id == bot.user.id:
        return
    if not os.path.exists('guildinfo.json'):
        with open('guildinfo.json', 'w') as f:
                f.write('[]')

    with open('guildinfo.json', 'r') as f:
        guildjson = json.load(f)


    guildjson = [entry for entry in guildjson if str(channel.guild.id) not in entry]

    guildjson.append({
        str(channel.guild.id): {
            'guild_id': str(channel.guild.id),
            'channel_name': channel.name,
            'channel_id': str(channel.id)
        }
    })

    with open('guildinfo.json', 'w') as f:
        json.dump(guildjson, f, indent=4)

    now = datetime.datetime.now()
    if (now - lastchanneldel).seconds > 10:
        antichannelspamcount = 0
        lastchanneldel = now

    antichannelspamcount += 1
    # antichannelspamcount = 6

    if antichannelspamcount > 4:
        print('channelcount run')
        for entry in reversed(guildjson):
            if str(channel.guild.id) in entry: 
                print('str channelguildid check run')
                channel_data = entry[str(channel.guild.id)]
                channel_name = channel_data['channel_name']
                channel_id = channel_data['channel_id']
                print(f"Comparing {channel_id} with {channel.id}")
                if str(channel_id) == str(channel.id):
                    await asyncio.sleep(1)
                    await channel.guild.create_text_channel(channel_name)
                    print(f'Found suspect: {suspect.user}')
                    dmsuspect = await bot.fetch_user(suspect.user.id)
                    try:
                        await suspect.kick(reason='Found suspect with permissions to create channels via audit log.')
                    except Exception as e:
                        print(f'Tried to kick the user {suspect.user}, but failed because {e}')
                    else:
                        print(f'Successfully kicked the user {suspect.user}')

                    try:
                        await dmsuspect.send('You\'ve been detected for the rapid removal of channels in a guild.')
                    except Exception as e:
                        print(f'Tried to DM {suspect.user}, but failed because {e}')
                    else:
                        print(f'Successfully DM\'d {suspect.user}')
                    break





@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name='for raids...'
        ))


bot.run(base64.b64decode(b64token).decode('utf-8'))
