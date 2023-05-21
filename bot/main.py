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
API_KEY = os.getenv('discogs')
user_agent = 'Mozilla/5.0'
discogs = discogs_client.Client(user_agent, user_token=API_KEY)

# Activate Discord
token = os.getenv('discord')
bot = commands.Bot(intents=discord.Intents().all(), command_prefix='.')

# Activate Youtube Music
ytmusic = YTMusic()

# Join Command
@bot.command(pass_context=True, name='join', help='This command makes the bot access the voice channel')
async def join(ctx):
    if (ctx.author.voice):
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You are not in a voice channel")

# Stop Command
@bot.command(pass_context=True, name='stop', help='This command makes the bot end the radio session')
async def stop(ctx):
    if (ctx.author.voice):
        if (ctx.voice_client):
            await ctx.guild.voice_client.disconnect()
        else:
            await ctx.send("I'm not in a voice channel, use the '.join' command to make me join")
    else:
        await ctx.send("You are not in a voice channel")

# Start Command
@bot.command(pass_context=True, name='start', help='This command makes the bot start the radio session')
async def start(ctx):
    if(ctx.voice_client == None):
        await ctx.send("I'm not in a voice channel, use the '.join' command to make me join")
    if(ctx.author.voice):
        if (ctx.voice_client.is_playing() == True):
            pass
        else:
            # Random Genre
            genres = os.listdir('../genres-styles')
            genres_without_txt = [ _.replace('.txt', '') for _ in genres]
            random_genre = random.choice(genres_without_txt)
            
            # Random Style
            styles = open(f'../genres-styles/{random_genre}.txt').read().splitlines()
            random_style = random.choice(styles)
            
            # Random Query
            query = random_genre+' '+random_style
            
            # Log Trace 0
            history = open('log_music', 'a')
            history.write(f'Query: {query}\t')
            history.close()

            # Generate the Query for Discogs API
            response = discogs.search(query, type='release')

            try:
                # Select the Random Music Agent Element
                if len(response) == 1:
                    random_element = 0
                elif len(response) >= 9999:
                    random_element = random.randint(0, 9999-1)
                else:
                    random_element = random.randint(0, len(response)-1)
                
                # Log Trace 1
                history = open('log_music', 'a')
                history.write(f'Random Element: {random_element}\t')
                history.close()

                # Get the Author and Song
                if response[random_element].artists[0].name == 'Various':
                    tracklist = response[random_element].tracklist
                    random_song_author = random.randint(0, len(tracklist)-1)
                    song = tracklist[random_song_author].title
                    try:
                        author = tracklist[random_song_author].artists[0].name
                    except:
                        author = ''
                else:
                    tracklist = response[random_element].tracklist
                    author = response[random_element].artists[0].name
                    songs = [ _.title for _ in tracklist]
                    song = random.choice(songs)
                
                # Log Trace 2
                history = open('log_music', 'a')
                history.write(f'ID: {response[random_element].id}\t')
                history.write(f'Author: {author}\t')
                history.write(f'Song: {song}\t')
                history.close()

                # Merge the Author and Song
                authorAndSong = author + ' ' + song
                
                # Log Trace 3
                history = open('log_music', 'a')
                history.write(f'Search: {authorAndSong}\n')
                history.close()

                # Youtube Music Search and Get Data
                search_results = ytmusic.search(authorAndSong, filter='songs')
                video_id = search_results[0]['videoId']
                title = search_results[0]['title']
                artists = search_results[0]['artists'][0]['name']
                photo = search_results[0]['thumbnails'][1]['url']
                duration = search_results[0]['duration']
                url_link = f'https://music.youtube.com/watch?v={video_id}'
                
                # Discord Embed Configuration
                embed = discord.Embed(
                    title='Now Playing',
                    description=f'[{title + " " + artists}]({url_link})',
                    color=discord.Colour.random()
                )
                embed.set_thumbnail(url=photo)
                embed.add_field(name='Duration', value=f'{duration}')
                await ctx.send(embed=embed)
                
                # Options and Configuration to Play the URL Song
                YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
                FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
                voice = get(bot.voice_clients, guild=ctx.guild)
                with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url_link, download=False)
                    voice.play(FFmpegPCMAudio(info['url'], **FFMPEG_OPTIONS), after=lambda _:bot.loop.create_task(ctx.invoke(bot.get_command('start'))))

            except:
                errorLog = open('log_error', 'a')
                errorLog.write(f'Query: {query}\tRandom Element: {random_element}\tID: {response[random_element].id}\tAuthor: {author}\tSong: {song}\tSearch: {authorAndSong}\n')
                errorLog.close()
                await ctx.invoke(bot.get_command('start'))
    else:
        await ctx.send('You are not in a voice channel')

# New Command
@bot.command(pass_context=True, name='new', help='This command makes the bot pass to another new song')
async def new(ctx):
    if(ctx.voice_client == None):
        await ctx.send("I'm not in a voice channel, use the '.join' command to make me join")
    if(ctx.author.voice):
        voice = get(bot.voice_clients, guild=ctx.guild)
        voice.stop()
    else:
        await ctx.send('You are not in a voice channel')

# Launch Random Radio BOT
bot.run(token)