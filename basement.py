import discord
from discord.ext import commands
import os
import asyncio

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="'", intents=intents)

# ================= CONFIG =================
LOG_CHANNEL_ID = 1491880119638163487

whitelist_users = set()
whitelist_roles = set()

# ================= HELPER =================

def is_whitelisted(member):
    if member.id in whitelist_users:
        return True
    for role in member.roles:
        if role.id in whitelist_roles:
            return True
    return False

async def get_member(interaction, user_input):
    guild = interaction.guild

    if user_input.startswith("<@"):
        user_id = user_input.replace("<@", "").replace("!", "").replace(">", "")
        return guild.get_member(int(user_id))

    if user_input.isdigit():
        return guild.get_member(int(user_input))

    for member in guild.members:
        if member.name == user_input or member.display_name == user_input:
            return member

    return None

async def get_voice_channel(interaction, channel_input):
    guild = interaction.guild

    if channel_input and channel_input.isdigit():
        return guild.get_channel(int(channel_input))

    if channel_input and channel_input.startswith("<#"):
        channel_id = channel_input.replace("<#", "").replace(">", "")
        return guild.get_channel(int(channel_id))

    if channel_input:
        for channel in guild.voice_channels:
            if channel.name == channel_input:
                return channel

    return None

# ================= READY =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

    bot.loop.create_task(update_status())

# ================= STATUS =================

async def update_status():
    await bot.wait_until_ready()

    while not bot.is_closed():
        total_members = sum(g.member_count for g in bot.guilds)

        await bot.change_presence(
            activity=discord.Streaming(
                name=f"{total_members} members",
                url="https://twitch.tv/discord"
            )
        )

        await asyncio.sleep(60)

# ================= ADVANCED EMBED LOGS =================

import datetime

def log_embed(title, description, color=discord.Color.blue()):
    now = datetime.datetime.utcnow()

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=now
    )

    embed.set_footer(text=f"Date: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    return embed


def get_account_age(user):
    now = datetime.datetime.utcnow()
    age = now - user.created_at.replace(tzinfo=None)
    return f"{age.days} days"


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    embed = log_embed(
        "Member Joined",
        f"User: <@{member.id}>\nID: {member.id}\nAccount Age: {get_account_age(member)}",
        discord.Color.green()
    )

    embed.set_thumbnail(url=member.display_avatar.url)
    await channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
    guild = member.guild
    channel = bot.get_channel(LOG_CHANNEL_ID)

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target.id == member.id:
            executor = entry.user

            embed = log_embed(
                "Member Kicked",
                f"User: <@{member.id}>\nID: {member.id}\nBy: <@{executor.id}>\nAccount Age: {get_account_age(member)}\nReason: {entry.reason}",
                discord.Color.red()
            )

            await channel.send(embed=embed)
            return

    embed = log_embed(
        "Member Left",
        f"User: <@{member.id}>\nID: {member.id}\nAccount Age: {get_account_age(member)}",
        discord.Color.orange()
    )

    await channel.send(embed=embed)


@bot.event
async def on_member_ban(guild, user):
    channel = bot.get_channel(LOG_CHANNEL_ID)

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target.id == user.id:
            executor = entry.user

            embed = log_embed(
                "User Banned",
                f"User: <@{user.id}>\nID: {user.id}\nBy: <@{executor.id}>\nAccount Age: {get_account_age(user)}\nReason: {entry.reason}",
                discord.Color.dark_red()
            )

            await channel.send(embed=embed)


@bot.event
async def on_member_unban(guild, user):
    channel = bot.get_channel(LOG_CHANNEL_ID)

    embed = log_embed(
        "User Unbanned",
        f"User: <@{user.id}>\nID: {user.id}\nAccount Age: {get_account_age(user)}",
        discord.Color.green()
    )

    await channel.send(embed=embed)

# ================= COMMANDS =================

@bot.tree.command(name="kick", description="kick a member")
@commands.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, user: str, reason: str = "No reason"):
    member = await get_member(interaction, user)

    if not member:
        await interaction.response.send_message("member not found", ephemeral=True)
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("cannot kick higher role", ephemeral=True)
        return

    await member.kick(reason=reason)
    await interaction.response.send_message(f"kicked {member}")

@bot.tree.command(name="ban", description="ban a member")
@commands.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, user: str, reason: str = "No reason"):
    member = await get_member(interaction, user)

    if not member:
        await interaction.response.send_message("member not found", ephemeral=True)
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("cannot ban higher role", ephemeral=True)
        return

    await member.ban(reason=reason)
    await interaction.response.send_message(f"banned {member}")

@bot.tree.command(name="unban", description="unban a member")
@commands.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user: str):
    try:
        user_id = int(user.replace("<@", "").replace("!", "").replace(">", ""))
        user_obj = await bot.fetch_user(user_id)
        await interaction.guild.unban(user_obj)
        await interaction.response.send_message(f"unbanned {user_obj}")
    except:
        await interaction.response.send_message("invalid id", ephemeral=True)

@bot.tree.command(name="avatar", description="get avatar")
async def avatar(interaction: discord.Interaction, user: str = None):
    member = interaction.user if not user else await get_member(interaction, user)

    if not member:
        await interaction.response.send_message("member not found", ephemeral=True)
        return

    await interaction.response.send_message(member.display_avatar.url)

@bot.tree.command(name="join", description="join voice channel")
async def join(interaction: discord.Interaction, channel: str = None):
    vc = interaction.user.voice.channel if not channel and interaction.user.voice else await get_voice_channel(interaction, channel)

    if not vc:
        await interaction.response.send_message("channel not found", ephemeral=True)
        return

    try:
        await vc.connect()
        await interaction.response.send_message(f"joined {vc.name}")
    except:
        await interaction.response.send_message("error joining", ephemeral=True)

# ================= WHITELIST =================

@bot.tree.command(name="whitelist_add_user", description="add user to whitelist")
async def whitelist_add_user(interaction: discord.Interaction, user: discord.Member):
    whitelist_users.add(user.id)
    await interaction.response.send_message(f"{user} added")

@bot.tree.command(name="whitelist_remove_user", description="remove user from whitelist")
async def whitelist_remove_user(interaction: discord.Interaction, user: discord.Member):
    whitelist_users.discard(user.id)
    await interaction.response.send_message(f"{user} removed")

@bot.tree.command(name="whitelist_add_role", description="add role to whitelist")
async def whitelist_add_role(interaction: discord.Interaction, role: discord.Role):
    whitelist_roles.add(role.id)
    await interaction.response.send_message(f"{role.name} added")

@bot.tree.command(name="whitelist_remove_role", description="remove role from whitelist")
async def whitelist_remove_role(interaction: discord.Interaction, role: discord.Role):
    whitelist_roles.discard(role.id)
    await interaction.response.send_message(f"{role.name} removed")

import random

# ================= ANGRY DATA =================
angry_counts = {}

# حط الجيفات هنا 👇
ANGRY_GIFS = [
    "https://nekos.best/api/v2/angry/22a73761-4611-468c-b39d-14400e6d5182.gif",
    "https://tenor.com/view/ram-re-zero-downlook-disgusted-anime-gif-16841200256546358049",
    "https://tenor.com/view/anime-angry-gif-22001291",
    "https://tenor.com/view/anime-blush-girl-mad-gif-16116911",
    "https://tenor.com/view/kittyhana-catfox-vtuber-angy-anime-mad-gif-16558404169050634072",
    "https://tenor.com/view/yosuga-no-sora-anime-anime-girl-cute-look-gif-1457869867166180864",
    "https://tenor.com/view/class-no-daikirai-na-joshi-to-kekkon-suru-koto-ni-natta-i%27m-getting-married-to-a-girl-i-hate-in-my-class-akane-sakuramori-angry-mad-gif-16488682991703357320",
]

# ================= ANGRY COMMAND =================

@bot.tree.command(name="angry", description="Get angry at someone")
async def angry(interaction: discord.Interaction, member: discord.Member):

    # حساب عدد المرات
    key = (interaction.user.id, member.id)

    if key not in angry_counts:
        angry_counts[key] = 0

    angry_counts[key] += 1
    count = angry_counts[key]

    # اختيار gif عشوائي
    gif = random.choice(ANGRY_GIFS)

    # الرسالة
    message = f"{interaction.user.mention} got angry at {member.mention} for the {count} time"

    embed = discord.Embed(description=message, color=discord.Color.red())
    embed.set_image(url=gif)

    await interaction.response.send_message(embed=embed)

import random

# ================= FUN COUNTS =================
fun_counts = {}

def get_count(user1, user2, action):
    key = (user1, user2, action)

    if key not in fun_counts:
        fun_counts[key] = 0

    fun_counts[key] += 1
    return fun_counts[key]

def format_msg(author, target, action, count):
    suffix = "time" if count == 1 else "times"
    return f"{author} {action} {target} for the {count} {suffix}"

# ================= GIF LISTS =================

KILL_GIFS = [
    "https://tenor.com/view/die-kill-kills-you-anime-gif-23910501",
    "https://tenor.com/view/reze-chainsaw-man-reze-arc-choking-rain-gif-12346418835128647519"
]

HUG_GIFS = [
    "https://tenor.com/view/animehug-gif-4492243580644690368",
    "https://tenor.com/view/cling-gif-10419099168557106015"
]

SLAP_GIFS = [
    "https://tenor.com/view/spank-slap-butt-anime-gif-17784858",
    "https://tenor.com/view/anime-tio-yue-girl-cute-gif-3850301508930160307"
]

KISS_GIFS = [
    "https://tenor.com/view/kiss-gif-6425930033453626328",
    "https://tenor.com/view/forehead-kiss-gif-16477707187334941899"
]

# ================= COMMANDS =================

@bot.tree.command(name="kill", description="Kill someone")
async def kill(interaction: discord.Interaction, member: discord.Member):
    count = get_count(interaction.user.id, member.id, "kill")
    gif = random.choice(KILL_GIFS)

    msg = format_msg(interaction.user.mention, member.mention, "killed", count)

    embed = discord.Embed(description=msg, color=discord.Color.dark_red())
    embed.set_image(url=gif)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="hug", description="Hug someone")
async def hug(interaction: discord.Interaction, member: discord.Member):
    count = get_count(interaction.user.id, member.id, "hug")
    gif = random.choice(HUG_GIFS)

    msg = format_msg(interaction.user.mention, member.mention, "hugged", count)

    embed = discord.Embed(description=msg, color=discord.Color.green())
    embed.set_image(url=gif)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="slap", description="Slap someone")
async def slap(interaction: discord.Interaction, member: discord.Member):
    count = get_count(interaction.user.id, member.id, "slap")
    gif = random.choice(SLAP_GIFS)

    msg = format_msg(interaction.user.mention, member.mention, "slapped", count)

    embed = discord.Embed(description=msg, color=discord.Color.orange())
    embed.set_image(url=gif)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="kiss", description="Kiss someone")
async def kiss(interaction: discord.Interaction, member: discord.Member):
    count = get_count(interaction.user.id, member.id, "kiss")
    gif = random.choice(KISS_GIFS)

    msg = format_msg(interaction.user.mention, member.mention, "kissed", count)

    embed = discord.Embed(description=msg, color=discord.Color.pink())
    embed.set_image(url=gif)

    await interaction.response.send_message(embed=embed)

# ================= PREFIX COMMANDS =================

import random

# ---------- COUNTS ----------
fun_counts = {}

def get_count(user1, user2, action):
    key = (user1, user2, action)
    if key not in fun_counts:
        fun_counts[key] = 0
    fun_counts[key] += 1
    return fun_counts[key]

def format_msg(author, target, action, count):
    suffix = "time" if count == 1 else "times"
    return f"{author} {action} {target} for the {count} {suffix}"

# ---------- MOD COMMANDS ----------

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason"):
    if member.top_role >= ctx.author.top_role:
        await ctx.send("cannot kick higher role")
        return

    await member.kick(reason=reason)
    await ctx.send(f"kicked {member}")


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason"):
    if member.top_role >= ctx.author.top_role:
        await ctx.send("cannot ban higher role")
        return

    await member.ban(reason=reason)
    await ctx.send(f"banned {member}")


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"unbanned {user}")

# ---------- GENERAL ----------

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)


@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("joined voice")
    else:
        await ctx.send("you are not in a voice channel")

# ---------- FUN ----------

@bot.command()
async def kill(ctx, member: discord.Member):
    count = get_count(ctx.author.id, member.id, "kill")
    gif = random.choice(KILL_GIFS)

    msg = format_msg(ctx.author.mention, member.mention, "killed", count)

    embed = discord.Embed(description=msg, color=discord.Color.dark_red())
    embed.set_image(url=gif)

    await ctx.send(embed=embed)


@bot.command()
async def hug(ctx, member: discord.Member):
    count = get_count(ctx.author.id, member.id, "hug")
    gif = random.choice(HUG_GIFS)

    msg = format_msg(ctx.author.mention, member.mention, "hugged", count)

    embed = discord.Embed(description=msg, color=discord.Color.green())
    embed.set_image(url=gif)

    await ctx.send(embed=embed)


@bot.command()
async def slap(ctx, member: discord.Member):
    count = get_count(ctx.author.id, member.id, "slap")
    gif = random.choice(SLAP_GIFS)

    msg = format_msg(ctx.author.mention, member.mention, "slapped", count)

    embed = discord.Embed(description=msg, color=discord.Color.orange())
    embed.set_image(url=gif)

    await ctx.send(embed=embed)


@bot.command()
async def kiss(ctx, member: discord.Member):
    count = get_count(ctx.author.id, member.id, "kiss")
    gif = random.choice(KISS_GIFS)

    msg = format_msg(ctx.author.mention, member.mention, "kissed", count)

    embed = discord.Embed(description=msg, color=discord.Color.pink())
    embed.set_image(url=gif)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user: str):
    try:
        # يشيل المنشن لو حطيته
        user_id = int(user.replace("<@", "").replace("!", "").replace(">", ""))

        user_obj = await bot.fetch_user(user_id)
        await ctx.guild.unban(user_obj)

        await ctx.send(f"unbanned <@{user_id}>")

    except:
        await ctx.send("invalid id or user not banned")

WELCOME_CHANNEL_ID = 1459299005338091532  # حط ID الروم هنا

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    await channel.send(f"Welcome, {member.mention} don't forget to use our server tag for perms!")
    
# ================= TOKEN =================

token = os.getenv("TOKEN")

if not token:
    print("No TOKEN found")
else:
    bot.run(token)
