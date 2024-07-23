import os
import random
import discogs_client
import discord
import asyncio
import yt_dlp as youtube_dl
from discord import Intents, FFmpegPCMAudio
from dotenv import load_dotenv
from discord.utils import get
from discord.ext import commands
from discord.ext.commands import Bot
from ytmusicapi import YTMusic

# Load .env
load_dotenv()

# Activate Discogs
API_KEY = os.getenv("discogs")
user_agent = "Mozilla/5.0"
discogs = discogs_client.Client(user_agent, user_token=API_KEY)

# Activate Discord
token = os.getenv("discord")
bot = commands.Bot(intents=discord.Intents().all(), command_prefix=".")

# Activate Youtube Music
ytmusic = YTMusic()

# Global variable to control the radio session
is_stopped = False
is_wanted = None


# Join Command
@bot.command(
    name="join",
    help="This command makes the bot access the voice channel",
)
async def join(ctx):
    try:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            if voice_client is not None:
                if voice_client.channel == channel:
                    await ctx.send("I am already in your voice channel")
                else:
                    await ctx.send(
                        f"I am already in another voice channel: {voice_client.channel}"
                    )
                return
            await channel.connect()
            await ctx.send(f"Joined {channel}")
        else:
            await ctx.send("You are not in a voice channel")
    except discord.DiscordException as e:
        await ctx.send(f"Failed to join the channel due to a Discord error: {str(e)}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {str(e)}")


# Stop Command
@bot.command(
    name="stop",
    help="This command makes the bot end the radio session",
)
async def stop(ctx):
    global is_stopped
    is_stopped = True
    try:
        voice_client = ctx.voice_client
        if voice_client is None:
            await ctx.send("I'm not in a voice channel")
            return
        if not ctx.author.voice or ctx.author.voice.channel != voice_client.channel:
            await ctx.send(
                "You need to be in the same voice channel as the bot to stop it"
            )
            return
        await voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel")
    except discord.DiscordException as e:
        await ctx.send(f"Failed to disconnect due to a Discord error: {str(e)}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {str(e)}")


# Start Command
@bot.command(
    name="start",
    help="This command makes the bot start the radio session",
)
async def start(ctx):
    global is_stopped
    global is_wanted
    if ctx.voice_client is None:
        await ctx.send(
            "I'm not in a voice channel, use the '.join' command to make me join"
        )
        return
    if not (ctx.author.voice and ctx.author.voice.channel == ctx.voice_client.channel):
        await ctx.send(
            "You need to be in the same voice channel as the bot to use this command"
        )
        return
    if ctx.voice_client.is_playing():
        await ctx.send("The radio session is already playing")
        return
    if is_stopped:
        is_stopped = False
        return
    try:
        if is_wanted is None:
            # Random Genre
            genres = os.listdir("./genres-styles")
            genres_without_txt = [_.replace(".txt", "") for _ in genres]
            random_genre = random.choice(genres_without_txt)
            # Random Style
            styles = open(f"./genres-styles/{random_genre}.txt").read().splitlines()
            random_style = random.choice(styles)
            # Random Query
            query = random_genre + " " + random_style
            # Log Trace 0
            with open("log_music", "a") as history:
                history.write(f"Query: {query}\t")
            # Generate the Query for Discogs API
            response = discogs.search(query, type="release")

        else:
            # Generate the Query for Discogs API
            response = discogs.search(is_wanted, type="release")
            # Log Trace 0
            with open("log_music", "a") as history:
                history.write(f"Query: {is_wanted}\t")
            # Generate the Query for Discogs API
            response = discogs.search(is_wanted, type="release")

        # Select the Random Music Agent Element
        random_element = random.randint(0, min(9999, len(response)) - 1)

        # Log Trace 1
        with open("log_music", "a") as history:
            history.write(f"Random Element: {random_element}\t")

        # Get the Author and Song
        selected_release = response[random_element]
        if selected_release.artists[0].name == "Various":
            tracklist = selected_release.tracklist
            random_song_author = random.choice(tracklist)
            song = random_song_author.title
            author = (
                random_song_author.artists[0].name if random_song_author.artists else ""
            )
        else:
            tracklist = selected_release.tracklist
            author = selected_release.artists[0].name
            song = random.choice(tracklist).title

        # Log Trace 2
        with open("log_music", "a") as history:
            history.write(f"ID: {selected_release.id}\t")
            history.write(f"Author: {author}\t")
            history.write(f"Song: {song}\t")

        # Merge the Author and Song
        author_and_song = f"{author} {song}"

        # Log Trace 3
        with open("log_music", "a") as history:
            history.write(f"Search: {author_and_song}\n")

        # Youtube Music Search and Get Data
        search_results = ytmusic.search(author_and_song, filter="songs")
        video_id = search_results[0]["videoId"]
        title = search_results[0]["title"]
        artists = search_results[0]["artists"][0]["name"]
        photo = search_results[0]["thumbnails"][1]["url"]
        duration = search_results[0]["duration"]
        url_link = f"https://music.youtube.com/watch?v={video_id}"

        # Discord Embed Configuration
        embed = discord.Embed(
            title="Now Playing",
            description=f'[{title + " " + artists}]({url_link})',
            color=discord.Colour.random(),
        )
        embed.set_thumbnail(url=photo)
        embed.add_field(name="Duration", value=f"{duration}")
        await ctx.send(embed=embed)

        # Options and Configuration to Play the URL Song
        YDL_OPTIONS = {"format": "bestaudio", "noplaylist": "True"}
        FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        voice = get(bot.voice_clients, guild=ctx.guild)
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url_link, download=False)
            voice.play(
                discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS),
                after=lambda _: bot.loop.create_task(start(ctx)),
            )
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        await ctx.invoke(bot.get_command("start"))


# New Command
@bot.command(
    name="new",
    help="This command makes the bot pass to new song",
)
async def new(ctx):
    if ctx.voice_client is None:
        await ctx.send(
            "I'm not in a voice channel, use the '.join' command to make me join"
        )
        return
    if not (ctx.author.voice and ctx.author.voice.channel == ctx.voice_client.channel):
        await ctx.send(
            "You need to be in the same voice channel as the bot to use this command"
        )
        return
    if not ctx.voice_client.is_playing():
        await ctx.send("The bot is not currently playing any music")
        return
    try:
        ctx.voice_client.stop()
        await ctx.send("Skipped to a new song")
    except discord.DiscordException as e:
        await ctx.send(f"Failed to skip to a new song due to a Discord error: {str(e)}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {str(e)}")


# I Want Command
@bot.command(
    name="iwant",
    help="This command makes the bot play music based on a specific request",
)
async def iwant(ctx, *, request):
    global is_wanted
    is_wanted = request
    if ctx.voice_client is None:
        await ctx.send(
            "I'm not in a voice channel, use the '.join' command to make me join"
        )
        return
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command")
        return
    if ctx.author.voice.channel != ctx.voice_client.channel:
        await ctx.send(
            "You need to be in the same voice channel as the bot to use this command"
        )
        return
    try:
        ctx.voice_client.stop()
        await ctx.send(f"Searching for songs similar to {request}")
    except discord.DiscordException as e:
        await ctx.send(
            f"Failed to process your request due to a Discord error: {str(e)}"
        )
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {str(e)}")


# Shuffle Command
@bot.command(
    name="shuffle",
    help="This command makes the bot returns to play music random again",
)
async def iwant(ctx):
    global is_wanted
    is_wanted = None
    if ctx.voice_client is None:
        await ctx.send(
            "I'm not in a voice channel, use the '.join' command to make me join"
        )
        return
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to use this command")
        return
    if ctx.author.voice.channel != ctx.voice_client.channel:
        await ctx.send(
            "You need to be in the same voice channel as the bot to use this command"
        )
        return
    try:
        ctx.voice_client.stop()
        await ctx.send("Back to random radio music")
    except discord.DiscordException as e:
        await ctx.send(f"Failed to shuffle due to a Discord error: {str(e)}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {str(e)}")


# Launch Random Radio BOT
bot.run(token)
