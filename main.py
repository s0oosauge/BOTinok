import nextcord
from nextcord import Interaction
from nextcord import Button, ButtonStyle
from nextcord.ext import commands
from nextcord.utils import get
import yt_dlp as ytdlp
import asyncio
import gtts
import random
import time
import logging
import sqlite3


#logging.basicConfig(level=logging.INFO)
file = open("TOKEN1.txt", 'r')
TOKEN = file.read()


conn = sqlite3.connect('song_database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    song_title TEXT,
    video_url TEXT,
    UNIQUE(user_id, video_url)
);

''')
conn.commit()


def mp3save(name, text, lang):
    file = gtts.gTTS(text, lang=lang, slow=False)
    file.save(f"data/{name}.mp3")


async def join_voice_channel(interaction: Interaction):
    channel = interaction.user.voice.channel
    return await channel.connect()


async def speech_join(interaction: Interaction, name, args, lang):
    user = interaction.user
    if not user:
        return None

    channel = user.voice.channel
    voice = get(client.voice_clients, guild=interaction.guild)

    if voice:
        if voice.is_playing():
            voice.stop()
        await voice.disconnect()

    if not voice or not voice.is_connected():
        await channel.connect()

    voice = get(client.voice_clients, guild=interaction.guild)

    mp3save(name, args, lang)
    source = await nextcord.FFmpegOpusAudio.from_probe(f'data/{name}.mp3', method='fallback')
    voice.play(source)

    return voice


class AddToQueue_Modal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Add a song")

        self.Enter_song = nextcord.ui.TextInput(label="Song to add to the queue", min_length=1, max_length=50,
                                                required=True)
        self.add_item(self.Enter_song)

    async def callback(self, interaction: Interaction) -> None:
        song = self.Enter_song.value
        return await play(interaction, song)


class ActionButtons(nextcord.ui.View):
    def __init__(self, timeout: float = None):
        super().__init__(timeout=timeout)
        self.value = None

    @nextcord.ui.button(style=nextcord.ButtonStyle.grey,
                        emoji="\N{CLOCKWISE RIGHTWARDS AND LEFTWARDS OPEN CIRCLE ARROWS}")
    async def looping(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        global is_looped
        if is_looped < 2:
            is_looped += 1
            if is_looped == 1:
                await interaction.send("``Queue is now being looped.``")
            else:
                await interaction.send("``Song is now being looped``")
        else:
            is_looped = 0
            await interaction.send("``Song no longer being looped``")

    @nextcord.ui.button(style=nextcord.ButtonStyle.grey, emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}")
    async def previous(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await previous(interaction)

    @nextcord.ui.button(style=nextcord.ButtonStyle.blurple, emoji="\N{DOUBLE VERTICAL BAR}")
    async def pause(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.value:
            await resume(interaction)
            self.value = False
        else:
            await pause(interaction)
            self.value = True

    @nextcord.ui.button(style=nextcord.ButtonStyle.grey, emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}")
    async def skip(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await skip(interaction)

    @nextcord.ui.button(style=nextcord.ButtonStyle.grey, emoji="\N{SQUARED NEW}")
    async def add_to_queue(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(AddToQueue_Modal())


class Dropdown(nextcord.ui.Select):
    def __init__(self, song_choices):
        super().__init__(placeholder="Choose a song to play", options=song_choices, custom_id="my_songs_select")

    async def callback(self, interaction: Interaction):
        if self.values[0]:
            await play(interaction, self.values[0])


class DropdownView(nextcord.ui.View):
    def __init__(self, song_choices, timeout: float = None):
        super().__init__(timeout=timeout)
        self.add_item(Dropdown(song_choices))


client = commands.Bot(command_prefix='/', intents=nextcord.Intents.all())

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1\
 -reconnect_streamed 1 -reconnect_delay_max 5'}

YTDLP_OPTIONS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

names = {'4sinl': 'Носатый', 'aiioe': 'мой псевдосоздатель', 'barigaavito': 'валесос с копьем',
         'soosya': 'кумар', 'default': 'бомж'}

mp3save("leave", "пока", "ru")


@client.user_command(force_global=True)
async def hello(interaction: nextcord.Interaction, member: nextcord.Member):
    await interaction.response.send_message(f"Hello {member}!")


@client.slash_command(name="ping", description="Displays the bot's latency", force_global=True)
async def ping(interaction: Interaction):
    start_time = time.time()

    await interaction.response.send_message("Pong!")

    end_time = time.time()

    latency = round((end_time - start_time) * 1000)
    await interaction.followup.send(f"(Latency: {latency}ms. API Latency: {round(client.latency * 1000)}ms.)")


@client.slash_command(name="help", description="Sends you a detailed list of the bot's commands", force_global=True)
async def help(interaction: Interaction):
    embed = nextcord.Embed(
        title="Bot Commands",
        description="Here is a list of available commands:",
        color=0x4EA6DA
    )

    embed.add_field(
        name="/play [query]",
        value="Plays a song",
        inline=False
    )

    embed.add_field(
        name="/skip",
        value="Skips the current track",
        inline=False
    )

    embed.add_field(
        name="/previous",
        value="Plays the previous track",
        inline=False
    )

    embed.add_field(
        name="/loop_queue",
        value="Loops the queue",
        inline=False
    )

    embed.add_field(
        name="/loop_song",
        value="Loops the current song",
        inline=False
    )

    embed.add_field(
        name="/my_songs",
        value="Displays songs queued by the user",
        inline=False
    )

    embed.add_field(
        name="/nowplaying",
        value="Displays the song that is currently playing",
        inline=False
    )

    embed.add_field(
        name="/pause",
        value="Pauses the current song",
        inline=False
    )

    embed.add_field(
        name="/resume",
        value="Resumes the current song",
        inline=False
    )

    embed.add_field(
        name="/queue",
        value="Displays the current queue",
        inline=False
    )

    embed.add_field(
        name="/clear",
        value="Clears all the songs in the queue",
        inline=False

    )

    embed.add_field(
        name="/clean [messages]",
        value="Clean up bot messages",
        inline=False

    )

    embed.add_field(
        name="/join",
        value="Joins your voice channel",
        inline=False

    )

    embed.add_field(
        name="/leave",
        value="Leaves your voice channel",
        inline=False

    )

    embed.add_field(
        name="/ping",
        value="Displays the bot's latency",
        inline=False

    )

    embed.add_field(
        name="/say [args]",
        value="Asks to say something",
        inline=False

    )

    embed.add_field(
        name="/say_german [args]",
        value="Asks to shout something in german",
        inline=False

    )

    embed.add_field(
        name="/say_ukrainian [args]",
        value="Asks to shout something in ukrainian",
        inline=False

    )

    embed.add_field(
        name="/say_vietnamese [args]",
        value="Asks to shout something in vietnamese",
        inline=False

    )

    await interaction.response.send_message(embed=embed)


@client.event
async def on_ready():
    print('BOTinok is ready')


@client.event
async def on_disconnect():
    conn.close()


@client.slash_command(name="hello", description="Greets you well", force_global=True)
async def hello(interaction: Interaction, arg):
    await interaction.send(f'{interaction.user.mention} {arg}')


async def join(interaction: Interaction):
    channel = interaction.user.voice.channel
    voice = get(client.voice_clients)

    if not voice or not voice.is_connected():
        await channel.connect()

    await asyncio.sleep(0.75)

    voice = get(client.voice_clients)

    mp3save("join", "ку рибятки", "ru")
    source = await nextcord.FFmpegOpusAudio.from_probe(f'data/join.mp3', method='fallback')
    voice.play(source)

    return voice


@client.slash_command(name="join", description="Keeps you company", force_global=True)
async def join(interaction: Interaction):

    if interaction.user.voice:
        channel = interaction.user.voice.channel
        voice = get(client.voice_clients, guild=interaction.guild)

        if not voice or not voice.is_connected() or voice.channel != channel:
            await channel.connect()
            await interaction.send(f"Joined the voice channel: {channel.name}")
        else:
            await interaction.send("I'm already in your voice channel.", ephemeral=True)
    else:
        await interaction.send("You need to be in a voice channel to use this command.", ephemeral=True)


@client.slash_command(name="leave", description="Leaves your voice channel", force_global=True)
async def leave(interaction: Interaction):
    global q, queue_list, index, is_previous, is_paused, is_looped

    voice = get(client.voice_clients, guild=interaction.guild)

    q = []
    queue_list = []
    index = 0
    is_previous = False
    is_paused = False
    is_looped = 0

    if voice and voice.is_connected():
        await voice.disconnect()
        await interaction.send("Left the voice channel.")
    else:
        await interaction.send("I'm not currently in a voice channel.", ephemeral=True)


ignored_channels = set()


@client.slash_command(name="ignore", description="Ignore commands in a specific channel", force_global=True)
async def ignore_channel(interaction: Interaction, channel: nextcord.TextChannel):

    if interaction.guild and interaction.channel.permissions_for(interaction.user).manage_channels:
        ignored_channels.add(channel.id)
        await interaction.response.send_message(f"Commands will now be ignored in {channel.mention}.")
    else:
        await interaction.response.send_message("You don't have the required permissions to use this command.",
                                                ephemeral=True)


@client.slash_command(name="clean", description="Clean up bot messages", force_global=True)
async def clean(interaction: Interaction, messages: int = 100):
    """
    Удаляет сообщения бота в канале.

    Параметры:
    - messages: Кол-во сообщений к удалению(по умолчанию: 100)
    """
    # Проверка на то, ести ли у пользователя, разрешение на удаление сообщений
    if interaction.channel.permissions_for(interaction.user).manage_messages:
        # Удаление сообщений бота в канале с заданным количеством
        deleted_messages = await interaction.channel.purge(limit=messages, check=lambda msg: msg.author == client.user)

        await interaction.response.send_message(f"Cleaned {len(deleted_messages)} bot messages.")
    else:
        await interaction.response.send_message("You don't have the required permissions to use this command.",
                                                ephemeral=True)


q = []
queue_list = []
index = 0
is_previous = False
is_paused = False
is_looped = 0


@client.slash_command(name="my_songs", description="Display songs queued by the user", force_global=True)
async def my_songs(interaction: Interaction):

    cursor.execute("SELECT id, song_title, video_url FROM songs WHERE user_id = ?", (interaction.user.id,))
    songs = cursor.fetchall()

    if songs:
        song_choices = [
            nextcord.SelectOption(label=title, value=url) for song_id, title, url in songs
        ]

        view = DropdownView(song_choices)

        await interaction.send(f"Select a song to play from {interaction.user.mention} requests:", view=view)
    else:
        await interaction.send("You haven't queued any songs yet.", ephemeral=True)


@client.slash_command(name="play", description="Plays a song.", force_global=True)
async def play(interaction: Interaction, query: str = nextcord.SlashOption(name="query",
                                                                           description="The query to search for.",
                                                                           required=True)):
    if interaction.user.voice:
        if "http" in query:
            await interaction.send("Adding...", ephemeral=True)
            q.append(query)
        else:
            await interaction.send("Searching...", ephemeral=True)
            await search_and_add_to_queue(interaction, query)

        video_title, video_duration, video_author = get_video_title(q[len(q) - 1])

        try:
            cursor.execute("INSERT INTO songs (user_id, song_title, video_url) VALUES (?, ?, ?)",
                           (interaction.user.id, video_title, q[len(q) - 1]))
            conn.commit()
        except sqlite3.IntegrityError:
            print("Песня уже существует в базе данных для этого пользователя.")

        queue_list.append(f"[{video_title}]({q[len(q) - 1]}) [{video_duration}] • {interaction.user.mention}")

        embed = nextcord.Embed(description=f"Queued {video_title} [{video_duration}] • {interaction.user.mention}",
                               color=0x4EA6DA)
        await interaction.send(embed=embed)

        if len(q) == 1:
            await play1(interaction)
    else:
        await interaction.send("You need to be in a voice channel to use this command.", ephemeral=True)


# Функция для поиска и добавления песни в очередь по ключевым словам
async def search_and_add_to_queue(interaction: Interaction, query):
    with ytdlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
        try:
            search_results = ydl.extract_info(f'ytsearch:{query}', download=False)['entries']
            if search_results:
                first_result = search_results[0]
                video_url = first_result['original_url']
                q.append(video_url)
            else:
                await interaction.send('No videos found.')
        except Exception as e:
            await interaction.send(f'An error occurred: {str(e)}')


async def play1(interaction: Interaction):
    global index
    url = q[index]
    with ytdlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info.get('title', None)
        video_url = info.get('url', None)
        channel_name = info.get('uploader', None)
        video_duration = info.get('duration_string', None)
        thumbnail_url = info.get('thumbnails', [{}])[27].get('url', nextcord.Embed.Empty)
    voice = get(client.voice_clients, guild=interaction.guild)
    if not voice or not voice.is_connected():
        voice = await join_voice_channel(interaction)

    embed = nextcord.Embed(
        title=f"**{video_title}**",
        description=f"by {channel_name}\nDuration - [{video_duration}]",
        color=0x4EA6DA
    )
    embed.set_thumbnail(url=thumbnail_url)

    await interaction.send(embed=embed, view=ActionButtons())

    voice.play(nextcord.FFmpegPCMAudio(
        video_url, **FFMPEG_OPTIONS), after=lambda e: queue_pass(interaction))


async def queue_pass(interaction: Interaction):
    global q, queue_list, index, is_previous, is_paused, is_looped
    if is_looped == 2:
        await play1(interaction)
    elif index < (len(q) - 1):
        index += 1
        await play1(interaction)
    elif is_previous and index > 0:
        index -= 1
        is_previous = False
        await play1(interaction)
    elif is_looped == 1:
        index = 0
        await play1(interaction)
    else:
        await interaction.send("Queue ended.")
        q = []
        queue_list = []
        index = 0
        is_previous = False
        is_paused = False
        await leave(interaction)


@client.slash_command(name="queue", description="Displays the current queue", force_global=True)
async def show_queue(interaction: Interaction):
    global q, index, queue_list

    if not q:
        await interaction.send("There are no songs currently playing, please play a song to use the command.",
                               ephemeral=True)
        return

    queue_info = f"**Now playing: {queue_list[index]}**\n\n**Up next:**\n"

    for i, track in enumerate(queue_list[index + 1:], start=index + 1):
        queue_info += f"{i}. {track}\n"

    embed = nextcord.Embed(
        title=f"**Queue**",
        description=queue_info,
        color=0x4EA6DA
    )

    await interaction.send(embed=embed)


@client.slash_command(name="shuffle", description="Shuffles the songs in the queue", force_global=True)
async def shuffle(interaction: Interaction):
    global q, queue_list, index, is_previous, is_paused
    voice = get(client.voice_clients, guild=interaction.guild)
    if voice and voice.is_playing():
        voice.pause()
        await interaction.send("Shuffled the queue. Now playing:")

    if not q:
        await interaction.send("There are no songs currently playing, please play a song to use the command.",
                               ephemeral=True)
        return

    random.shuffle(q)
    index = 0
    queue_list = []
    is_previous = False
    is_paused = False

    await play1(interaction)
    for i in range(0, len(q)):
        video_title, video_duration, video_author = get_video_title(q[i])
        queue_list.append(f"[{video_title}]({q[i]}) [{video_duration}] • {interaction.user.mention}")


@client.slash_command(name="play_something", description="Shuffles the user's queued songs", force_global=True)
async def play_something(interaction: Interaction, amount: int = 5):
    global q, queue_list, index, is_previous, is_paused
    voice = get(client.voice_clients, guild=interaction.guild)
    if voice and voice.is_playing():
        voice.pause()
        await interaction.send("Shuffled the queries.")

    cursor.execute("SELECT id, song_title, video_url FROM songs WHERE user_id = ?", (interaction.user.id,))
    songs = cursor.fetchall()

    if not songs:
        await interaction.send("You haven't queued any songs yet.", ephemeral=True)
        return

    song_urls = [song[2] for song in songs]
    random.shuffle(song_urls)

    q.clear()
    q.extend(song_urls[:amount])

    index = 0
    is_previous = False
    is_paused = False
    queue_list = []

    await play1(interaction)

    for i in range(0, len(q)):
        video_title, video_duration, video_author = get_video_title(q[i])
        queue_list.append(f"[{video_title}]({q[i]}) [{video_duration}] • {interaction.user.mention}")


def get_video_title(video_url: str) -> str:
    with ytdlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
        info = ydl.extract_info(video_url, download=False)
        video_title = info.get('title', None)
        video_duration = info.get('duration_string', None)
        video_author = info.get('uploader', None)
        return video_title, video_duration, video_author


@client.slash_command(name="clear", description="Clears all the song in the queue", force_global=True)
async def clear(interaction: Interaction):
    global q, queue_list, index, is_previous, is_paused

    if not q:
        await interaction.send("There are no songs currently playing, please play a song to use the command.",
                               ephemeral=True)
        return

    q = [q[0]]
    queue_list = [queue_list[0]]
    index = 0
    is_previous = False
    is_paused = False

    await interaction.send("Cleared the queue")


@client.slash_command(name="pause", description="Pauses the current song.", force_global=True)
async def pause(interaction: Interaction):
    global is_paused
    voice = get(client.voice_clients, guild=interaction.guild)

    if voice and voice.is_playing():
        voice.pause()
        is_paused = True
        await interaction.response.send_message(f"Music is paused by {interaction.user.mention}.")
    else:
        await interaction.response.send_message("No music is currently playing.", ephemeral=True)


@client.slash_command(name="resume", description="Resumes the current song.", force_global=True)
async def resume(interaction: Interaction):
    global is_paused
    voice = get(client.voice_clients, guild=interaction.guild)

    if voice and voice.is_paused():
        voice.resume()
        is_paused = False
        await interaction.response.send_message(f"Music is resumed by {interaction.user.mention}.")
    else:
        await interaction.response.send_message("The music is not paused.")


@client.slash_command(name="skip", description="Skips the current track", force_global=True)
async def skip(interaction: Interaction):
    global q, index, is_paused
    voice = get(client.voice_clients)

    if voice and voice.is_playing():
        voice.stop()
        await interaction.response.send_message(f"Current track is skipped by {interaction.user.mention}.")
    elif is_paused and index < len(q)-1:
        voice.resume()
        voice.stop()
        await interaction.response.send_message(f"Current track is skipped by {interaction.user.mention}.")
        is_paused = False
    else:
        await interaction.response.send_message("No music is currently playing.")


@client.slash_command(name="previous", description="Plays the previous track", force_global=True)
async def previous(interaction: Interaction):
    global is_previous, index, is_paused
    voice = get(client.voice_clients)

    if voice and voice.is_playing() and index > 0:
        is_previous = True
        voice.stop()
        await interaction.response.send_message(f"Backing up to the previous track by {interaction.user.mention}.")
    elif is_paused and index > 0:
        is_previous = True
        voice.resume()
        voice.stop()
        await interaction.response.send_message(f"Backing up to the previous track by {interaction.user.mention}.")
        is_paused = False
    else:
        await interaction.response.send_message("There is no previous song.", ephemeral=True)


@client.slash_command(name="loop_queue", description="Loops the queue.", force_global=True)
async def loop_queue(interaction: Interaction):
    global is_looped, q
    if q:
        is_looped = 1
        await interaction.send("The queue is looped now.",
                               ephemeral=True)
    else:
        await interaction.send("There are no songs currently playing, please play a song to use the command.",
                               ephemeral=True)


@client.slash_command(name="loop_song", description="Loops the current song.", force_global=True)
async def loop_song(interaction: Interaction):
    global is_looped, q
    if q:
        is_looped = 2
        await interaction.send("The current song is looped now.",
                               ephemeral=True)
    else:
        await interaction.send("There are no songs currently playing, please play a song to use the command.",
                               ephemeral=True)


@client.slash_command(name="nowplaying", description="Displays the song that is currently playing.", force_global=True)
async def nowplaying(interaction: Interaction):
    global index, q
    if q:
        url = q[index]
        with ytdlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', None)
            channel_name = info.get('uploader', None)
            video_duration = info.get('duration_string', None)
            thumbnail_url = info.get('thumbnails', [{}])[27].get('url', nextcord.Embed.Empty)
        embed = nextcord.Embed(
            title=f"**{video_title}**",
            description=f"by {channel_name}\nDuration - [{video_duration}]",
            color=0x4EA6DA
        )
        embed.set_thumbnail(url=thumbnail_url)

        await interaction.send(embed=embed)
    else:
        await interaction.send("There are no songs currently playing, please play a song to use the command.",
                               ephemeral=True)


@client.slash_command(name="say", description="Ask to say something.", force_global=True)
async def say(interaction: Interaction, args):
    if 'клей' in args:
        await interaction.send_message('не тупой, такого не скажу')
    else:
        await interaction.message.delete()
        await interaction.send_message(args)


@client.slash_command(name="shout", description="Ask to shout something.", force_global=True)
async def shout(interaction: Interaction, args):
    name = str(interaction.message.author).split("#")[0]
    action = ['говорит', 'высказал', 'выделил', 'пишет'][random.randint(0, 3)]

    await speech_join(interaction, "say_ru",
                      names.get(name, "default") + ' ' + action + ': ' + args,
                      "ru")


@client.slash_command(name="say_german", description="Ask to shout something on german.", force_global=True)
async def say_de(interaction: Interaction, args):
    await interaction.send("Говорю...", ephemeral=True)
    await speech_join(interaction, "say_de", args, "de")


@client.slash_command(name="say_ukrainian", description="Ask to shout something on ukrainian.", force_global=True)
async def say_uk(interaction: Interaction, args):
    await interaction.send("Говорю...", ephemeral=True)
    await speech_join(interaction, "say_uk", args, "uk")


@client.slash_command(name="say_vietnamese", description="Ask to shout something on vietnamese.", force_global=True)
async def say_vi(interaction: Interaction, args):
    await interaction.send("Говорю...", ephemeral=True)
    await speech_join(interaction, "say_vi", args, "vi")


client.run(TOKEN)
