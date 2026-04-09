import discord
from discord.ext import commands
import os
import asyncio

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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

# ================= EMBED LOGS =================

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


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    embed = log_embed(
        "Member Joined",
        f"User: {member.mention}\nID: {member.id}",
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
                f"User: {member}\nBy: {executor}\nReason: {entry.reason}",
                discord.Color.red()
            )

            await channel.send(embed=embed)
            return

    embed = log_embed(
        "Member Left",
        f"User: {member}",
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
                f"User: {user}\nBy: {executor}\nReason: {entry.reason}",
                discord.Color.dark_red()
            )

            await channel.send(embed=embed)


@bot.event
async def on_member_unban(guild, user):
    channel = bot.get_channel(LOG_CHANNEL_ID)

    embed = log_embed(
        "User Unbanned",
        f"User: {user}",
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

# ================= TOKEN =================

token = os.getenv("TOKEN")

if not token:
    print("No TOKEN found")
else:
    bot.run(token)
