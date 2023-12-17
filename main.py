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


#logging.basicConfig(level=logging.INFO)
file = open("TOKEN.txt", 'r')
TOKEN = file.read()


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

names = {'4sinl': 'Носатый', 'duck_malish': 'тупой сынок шлюхи',
         'aiioe': 'мой псевдосоздатель', 'barigaavito': 'валесос с копьем',
         'soosya': 'кумар', 'default': 'бомж задристанный'}

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
        color=0xFF00FF
    )

    embed.add_field(
        name="/hello [arg]",
        value="Greet the bot",
        inline=False
    )

    embed.add_field(
        name="/join",
        value="Join the voice channel",
        inline=False
    )

    embed.add_field(
        name="/leave",
        value="Leave the voice channel",
        inline=False
    )

    embed.add_field(
        name="/спой [url]",
        value="Add a song to the queue",
        inline=False
    )

    embed.add_field(
        name="/скажи [args]",
        value="Make the bot say something",
        inline=False
    )

    embed.add_field(
        name="/крикни [args]",
        value="Make the bot shout something",
        inline=False
    )

    embed.add_field(
        name="/адольф_крикни [args]",
        value="Make the bot shout something in German",
        inline=False
    )

    embed.add_field(
        name="/хохол_крикни [args]",
        value="Make the bot shout something in Ukrainian",
        inline=False
    )

    embed.add_field(
        name="/серёга_крикни [args]",
        value="Make the bot shout something in Vietnamese",
        inline=False
    )

    embed.add_field(
        name="/help",
        value="Display this help message",
        inline=False
    )

    await interaction.response.send_message(embed=embed)


@client.event
async def on_ready():
    print('Bot connected')


@client.event
async def on_message(message):
    # Check if the message is a command and if the channel is in the ignored_channels set
    if message.content.startswith('/') and message.channel.id in ignored_channels:
        return  # Ignore commands in the specified channel

    await client.process_commands(message)  # Process commands as usual


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

    voice = get(client.voice_clients, guild=interaction.guild)

    if voice and voice.is_playing():
        voice.stop()

    if voice and voice.is_connected():
        await voice.disconnect()
        await interaction.send("Left the voice channel.")
    else:
        await interaction.send("I'm not currently in a voice channel.", ephemeral=True)


ignored_channels = set()  # Set to store ignored channels


@client.slash_command(name="ignore", description="Ignore commands in a specific channel", force_global=True)
async def ignore_channel(interaction: Interaction, channel: nextcord.TextChannel):
    """
    Ignores commands in the specified channel.

    Parameters:
    - channel: The channel to ignore commands in.
    """
    # Check if the user has the manage_channels permission
    if interaction.guild and interaction.channel.permissions_for(interaction.user).manage_channels:
        # Add the channel to the set of ignored channels
        ignored_channels.add(channel.id)
        await interaction.response.send_message(f"Commands will now be ignored in {channel.mention}.")
    else:
        # User doesn't have the necessary permissions
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
prev_songs = []
index = 0
is_previous = False
is_paused = False
is_looped = 0


@client.slash_command(name="play", description="Plays a song.", force_global=True)
async def play(interaction: Interaction, query: str = nextcord.SlashOption(name="query",
                                                                           description="The query to search for.",
                                                                           choices=prev_songs)):
    global prev_songs
    await interaction.send("Searching...", ephemeral=True)
    if "http" in query:
        q.append(query)
    else:
        await search_and_add_to_queue(interaction, query)

    video_title, video_duration = get_video_title(q[len(q)-1])

    prev_songs.append(video_title)

    queue_list.append(f"[{video_title}]({q[len(q)-1]}) [{video_duration}] • @{interaction.user.global_name}")

    await interaction.send(f"``Queued {video_title} [{video_duration}] • @{interaction.user.global_name}``")

    if len(q) == 1:
        await play1(interaction)


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


def get_video_title(video_url: str) -> str:
    with ytdlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
        info = ydl.extract_info(video_url, download=False)
        video_title = info.get('title', None)
        video_duration = info.get('duration_string', None)
        return video_title, video_duration


@client.slash_command(name="clear", description="Clears all the song in the queue", force_global=True)
async def clear(interaction: Interaction):
    global q, queue_list, index, is_previous, is_paused

    if not q:
        await interaction.send("There are no songs currently playing, please play a song to use the command.",
                               ephemeral=True)
        return

    q = []
    queue_list = []
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
        await interaction.response.send_message(f"Music is paused by {interaction.user.global_name}.")
    else:
        await interaction.response.send_message("No music is currently playing.", ephemeral=True)


@client.slash_command(name="resume", description="Resumes the current song.", force_global=True)
async def resume(interaction: Interaction):
    global is_paused
    voice = get(client.voice_clients, guild=interaction.guild)

    if voice and voice.is_paused():
        voice.resume()
        is_paused = False
        await interaction.response.send_message(f"Music is resumed by {interaction.user.global_name}.")
    else:
        await interaction.response.send_message("The music is not paused.")


@client.slash_command(name="skip", description="Skips the current track", force_global=True)
async def skip(interaction: Interaction):
    global q, index, is_paused
    voice = get(client.voice_clients)

    if voice and voice.is_playing():
        voice.stop()
        await interaction.response.send_message(f"Current track is skipped by {interaction.user.global_name}.")
    elif is_paused and index < len(q)-1:
        voice.resume()
        voice.stop()
        await interaction.response.send_message(f"Current track is skipped by {interaction.user.global_name}.")
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
        await interaction.response.send_message(f"Backing up to the previous track by {interaction.user.global_name}.")
    elif is_paused and index > 0:
        is_previous = True
        voice.resume()
        voice.stop()
        await interaction.response.send_message(f"Backing up to the previous track by {interaction.user.global_name}.")
        is_paused = False
    else:
        await interaction.response.send_message("There is no previous song.", ephemeral=True)


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
