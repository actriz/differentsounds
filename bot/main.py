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


# Join Command
@bot.command(
    name="join",
    help="This command makes the bot access the voice channel",
)
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client is not None:
            await ctx.send("I am already in a voice channel")
            return
        try:
            await channel.connect()
            await ctx.send(f"Joined {channel}")
        except Exception as e:
            await ctx.send(f"Failed to join the channel: {str(e)}")
    else:
        await ctx.send("You are not in a voice channel")


# Stop Command
@bot.command(
    name="stop",
    help="This command makes the bot end the radio session",
)
async def stop(ctx):
    if ctx.voice_client:
        if ctx.author.voice and ctx.author.voice.channel == ctx.voice_client.channel:
            try:
                await ctx.voice_client.disconnect()
                await ctx.send("Disconnected from the voice channel")
            except Exception as e:
                await ctx.send(f"Failed to disconnect: {str(e)}")
        else:
            await ctx.send(
                "You need to be in the same voice channel as the bot to stop it"
            )
    else:
        await ctx.send("I'm not in a voice channel")


# Start Command
@bot.command(
    name="start",
    help="This command makes the bot start the radio session",
)
async def start(ctx):
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

    try:
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
        history = open("log_music", "a")
        history.write(f"Query: {query}\t")
        history.close()

        # Generate the Query for Discogs API
        response = discogs.search(query, type="release")

        # Select the Random Music Agent Element
        random_element = random.randint(0, min(9999, len(response)) - 1)

        # Log Trace 1
        history = open("log_music", "a")
        history.write(f"Random Element: {random_element}\t")
        history.close()

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
        history = open("log_music", "a")
        history.write(f"ID: {selected_release.id}\t")
        history.write(f"Author: {author}\t")
        history.write(f"Song: {song}\t")
        history.close()

        # Merge the Author and Song
        author_and_song = f"{author} {song}"

        # Log Trace 3
        history = open("log_music", "a")
        history.write(f"Search: {author_and_song}\n")
        history.close()

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
        errorLog = open("log_error", "a")
        errorLog.write(
            f"Query: {query}\tRandom Element: {random_element}\tID: {selected_release.id}\tAuthor: {author}\tSong: {song}\tSearch: {author_and_song}\n"
        )
        errorLog.close()
        await ctx.send(f"An error occurred: {str(e)}")
        await ctx.invoke(bot.get_command("start"))


# New Command
@bot.command(
    name="new",
    help="This command makes the bot pass to another new song",
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

    except Exception as e:
        await ctx.send(f"Failed to skip to a new song: {str(e)}")


# Launch Random Radio BOT
bot.run(token)
