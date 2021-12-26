import nextcord
import youtube_dl
import aiohttp
import os
import re
import asyncio
import logging

from util.exception import NotFound, InvalidArgs

logger = logging.getLogger("Music")

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': " -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

clients = {}  # guild: MusicClient

async def get_client(message, client):
    global clients
    if not str(message.guild.id) in clients:
        clients[str(message.guild.id)] = await MusicClient().create(message, client)
    return clients[str(message.guild.id)]

class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, option=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(nextcord.FFmpegPCMAudio(filename, **option), data=data)

class Song:
    def __init__(self, url, ss=None):
        info = ytdl.extract_info(url, download=False)
        self.url = url
        self.title = info['title']
        self.image = info['thumbnail']
        self.duration = info['duration']
        self.ss = ss
    def __str__(self):
        return "**{0.title}** - {1}:{2:02d}{3}".format(self, self.duration // 60, self.duration % 60,
                                                        f" (starts at {self.ss})" if self.ss else '')

class MusicClient:
    def __init__(self):
        pass

    async def create(self, message, client):
        logger.info("Creating MusicClient")
        if message.author.voice.channel:
            self.voice_client = await message.author.voice.channel.connect()
            self.queue = []
            self.notif_channel = message.channel
            self.client = client
        return self

    async def stream(self, song):
        logger.info(f"Starting streaming {song}")
        if song.ss:
            option = {**ffmpeg_options, **{'options':ffmpeg_options['options'] + ' -ss {}'.format(song.ss)}}
        else:
            option = ffmpeg_options
        try:
            player = await YTDLSource.from_url(song.url, loop=self.client.loop, stream=True, option=option)
        except youtube_dl.utils.DownloadError:
            return await self.notif_channel.send("Une erreur s'est produite lors du téléchargement de la musique, le propriétaire a surement bloqué le visionage extérieur.")
        after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next_music(), self.client.loop) if not e else print("ERR:", e)
        await asyncio.sleep(1)
        self.voice_client.play(player, after=after)
        em = nextcord.Embed(title=song.title, description="now playing",
                           url=song.url)
        em.set_image(url=song.image)
        await self.notif_channel.send(embed=em)

    async def play_next_music(self):
        if self.voice_client.is_playing():
            return self.voice_client.stop()
        if not self.queue:
            return await self.disconnect()
        song = self.queue[0]
        del self.queue[0]
        return await self.stream(song)

    async def add_to_queue(self, args, notif=True):
        song = Song(args[0], ss=args[1] if len(args) >= 2 else None)
        self.queue.append(song)
        if notif:
            await self.notif_channel.send("ajouté à la queue:\n{}".format(song))
        if not self.voice_client.is_playing():
            await self.play_next_music()
        return song

    async def bulk_add_to_queue(self, args):
        pass

    async def display_queue(self, channel):
        await channel.send("Queue :\n{}".format(
            '\n'.join([f"{i+1} - {v}" for i, v in enumerate(self.queue)])))

    async def disconnect(self):
        await self.voice_client.disconnect()
        global clients
        del clients[str(self.voice_client.guild.id)]

class CmdMusic:
    async def cmd_music(self, *args, message, channel, force, client, **_):
        global clients
        if not args:
            raise InvalidArgs("Aucun argument reçu.")
        music_client = await get_client(message, client)
        if args[0] == "disconnect":
            await music_client.disconnect()
            await channel.send("Client déconnecté")
        elif args[0] == "pause":
            if not music_client.voice_client:
                await channel.send("le client n'est pas connecté")
            elif music_client.voice_client.is_paused():
                await channel.send("déjà en pause")
            elif not music_client.voice_client.is_playing():
                await channel.send("aucune musique en cours")
            else:
                music_client.voice_client.pause()
                await channel.send("mise en pause ... (``/music resume`` pour reprendre)")
        elif args[0] == "resume":
            if not music_client.voice_client:
                await channel.send("le client n'est pas connecté")
            elif not music_client.voice_client.is_paused():
                await channel.send("la pause n'est pas activé")
            else:
                music_client.voice_client.resume()
        elif args[0] == "skip":
            await music_client.play_next_music()
        elif args[0] == "queue":
            await music_client.display_queue(channel)
        elif args[0] == "search":
            music = await search_music('+'.join(args[1:]))
            if not music:
                raise NotFound("J'ai trouvé aucune musique portant ce nom :(")
            await music_client.add_to_queue([music])
        else:
            if not re.match(r".*www\.youtube\.com/watch\?v=.*", args[0]):
                music = await search_music('+'.join(args))
                if not music:
                    raise NotFound("J'ai trouvé aucune musique portant ce nom :(")
                return await music_client.add_to_queue([music])
            await music_client.add_to_queue(args)


async def search_music(song_name):
    async with aiohttp.ClientSession() as client:
        async with client.get('https://www.youtube.com/results?search_query={}'.format(song_name)) as resp:
            assert resp.status == 200
            html = await resp.text()
    result = re.findall(r'href=\"\/watch\?v=(.{11})', html)
    logger.info(f"find music {result}")
    if not result:
        return None
    return "https://www.youtube.com/watch?v=" + result[0]