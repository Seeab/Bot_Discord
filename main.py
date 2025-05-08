import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
from collections import deque
import os
from keep_alive import keep_alive

# Configuración de intents
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Variables globales
queue = deque()
current_song = None
is_playing = False
is_paused = False

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'noplaylist': True,
    'quiet': True,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!comandos"))

async def play_next(ctx):
    global queue, current_song, is_playing, is_paused
    
    if len(queue) > 0:
        is_playing = True
        is_paused = False
        current_song = queue.popleft()
        
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(current_song['url'], **FFMPEG_OPTIONS),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        )
        
        await ctx.send(f"🎶 Reproduciendo: **{current_song['title']}**")
    else:
        is_playing = False
        current_song = None

@bot.command(name='comandos', aliases=['h', 'ayuda'])
async def show_commands(ctx):
    """Muestra todos los comandos disponibles del bot"""
    commands_list = [
        "**🎵 Comandos de Música:**",
        "`!play [url/búsqueda]` - Añade una canción a la cola (alias: `!p`)",
        "`!queue` - Muestra la cola de reproducción (alias: `!q`)",
        "`!skip` - Salta la canción actual (alias: `!s`)",
        "`!back` - Vuelve a la canción anterior (alias: `!b`)",
        "`!pause` - Pausa la reproducción",
        "`!resume` - Reanuda la reproducción (alias: `!r`)",
        "`!stop` - Detiene el bot y limpia la cola",
        "`!nowplaying` - Muestra la canción actual (alias: `!np`)",
        "",
        "**ℹ️ Comandos de Ayuda:**",
        "`!comandos` - Muestra esta ayuda (alias: `!h`, `!ayuda`)"
    ]
    
    embed = discord.Embed(
        title="🎶 Comandos del Bot de Música",
        description="\n".join(commands_list),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, url: str):
    global is_playing, is_paused
    
    try:
        if not ctx.author.voice:
            return await ctx.send("¡Únete a un canal de voz primero!")

        voice_channel = ctx.author.voice.channel

        if not ctx.voice_client:
            await voice_channel.connect()
        elif ctx.voice_client.channel != voice_channel:
            await ctx.voice_client.move_to(voice_channel)

        if not url.startswith('http'):
            url = f"ytsearch:{url}"

        with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            song = {
                'title': info['title'],
                'url': info['url'],
                'requester': ctx.author
            }

            queue.append(song)
            await ctx.send(f"✅ **{song['title']}** añadido a la cola")

            if not is_playing and not is_paused:
                await play_next(ctx)
                
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='queue', aliases=['q'])
async def show_queue(ctx):
    if not queue:
        return await ctx.send("La cola está vacía.")
    
    queue_list = []
    for i, song in enumerate(queue, 1):
        queue_list.append(f"{i}. **{song['title']}** (solicitado por {song['requester'].mention})")
    
    await ctx.send("**🎵 Cola de reproducción:**\n" + "\n".join(queue_list))

@bot.command(name='skip', aliases=['s'])
async def skip(ctx):
    global is_playing, is_paused
    
    if ctx.voice_client is None or not ctx.voice_client.is_playing():
        return await ctx.send("No hay nada reproduciendo.")
    
    ctx.voice_client.stop()
    is_playing = False
    await ctx.send("⏭️ Canción saltada")

@bot.command(name='back', aliases=['b'])
async def back(ctx):
    global queue, current_song, is_playing, is_paused
    
    if current_song is None:
        return await ctx.send("No hay canción anterior.")
    
    queue.appendleft(current_song)
    
    if len(queue) > 1:
        queue.appendleft(queue.pop())
    
    ctx.voice_client.stop()
    is_playing = False
    await play_next(ctx)
    await ctx.send("⏮️ Volviendo a la canción anterior")

@bot.command(name='pause')
async def pause(ctx):
    global is_paused
    
    if ctx.voice_client is None or not ctx.voice_client.is_playing():
        return await ctx.send("No hay nada reproduciendo.")
    
    if is_paused:
        return await ctx.send("La música ya está pausada.")
    
    ctx.voice_client.pause()
    is_paused = True
    await ctx.send("⏸️ Música pausada")

@bot.command(name='resume', aliases=['r'])
async def resume(ctx):
    global is_paused
    
    if ctx.voice_client is None or not ctx.voice_client.is_paused():
        return await ctx.send("La música no está pausada.")
    
    ctx.voice_client.resume()
    is_paused = False
    await ctx.send("▶️ Música reanudada")

@bot.command(name='stop')
async def stop(ctx):
    global queue, current_song, is_playing, is_paused
    
    if ctx.voice_client is None:
        return await ctx.send("El bot no está en un canal de voz.")
    
    queue.clear()
    current_song = None
    is_playing = False
    is_paused = False
    
    await ctx.voice_client.disconnect()
    await ctx.send("⏹️ Bot desconectado y cola limpiada")

@bot.command(name='nowplaying', aliases=['np'])
async def now_playing(ctx):
    if current_song is None:
        return await ctx.send("No hay ninguna canción reproduciéndose.")
    
    await ctx.send(f"🎶 Reproduciendo ahora: **{current_song['title']}** (solicitado por {current_song['requester'].mention})")

@play.error
async def play_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Por favor, especifica una canción o URL de YouTube.")

keep_alive()
try:
    bot.run(os.getenv('TOKEN'))
except discord.errors.HTTPException:
    print("\n\nERROR AL CONECTAR")
    print("Soluciona: https://replit.com/talk/learn/How-to-fix-Discordpy-429-errors-when-using-replit/110322")