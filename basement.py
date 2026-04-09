import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= READY =================
import asyncio

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

    while True:
        total_members = sum(guild.member_count for guild in bot.guilds)

        await bot.change_presence(
            activity=discord.Streaming(
                name=f"{total_members} members",
                url="https://twitch.tv/discord"
            )
        )

        await asyncio.sleep(60)

# ================= HELPER =================

async def get_member(ctx_or_interaction, user_input):
    guild = ctx_or_interaction.guild

    # لو منشن
    if user_input.startswith("<@") and user_input.endswith(">"):
        user_id = user_input.replace("<@", "").replace("!", "").replace(">", "")
        return guild.get_member(int(user_id))

    # لو ID
    if user_input.isdigit():
        return guild.get_member(int(user_input))

    # لو اسم
    for member in guild.members:
        if member.name == user_input or member.display_name == user_input:
            return member

    return None

# ================= KICK =================

@bot.tree.command(name="kick", description="kick a member")
@commands.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, user: str, reason: str = "No reason"):
    member = await get_member(interaction, user)

    if not member:
        await interaction.response.send_message("member not found", ephemeral=True)
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("you cant kick a higher role member", ephemeral=True)
        return

    await member.kick(reason=reason)
    await interaction.response.send_message(f"member kicked {member}")

# ================= BAN =================

@bot.tree.command(name="ban", description="ban a member")
@commands.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, user: str, reason: str = "No reason"):
    member = await get_member(interaction, user)

    if not member:
        await interaction.response.send_message("member not fount", ephemeral=True)
        return

    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("you cant ban a higher role member", ephemeral=True)
        return

    await member.ban(reason=reason)
    await interaction.response.send_message(f"member banned {member}")

# ================= UNBAN =================

@bot.tree.command(name="unban", description="unban a member")
@commands.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user: str):
    try:
        user_id = int(user.replace("<@", "").replace("!", "").replace(">", ""))
        user_obj = await bot.fetch_user(user_id)
        await interaction.guild.unban(user_obj)
        await interaction.response.send_message(f"member unbanned {user_obj}")
    except:
        await interaction.response.send_message("invaild id or mention", ephemeral=True)


# ================= LOGS =================

LOG_CHANNEL_ID = 1491880119638163487  # حط هنا ID الروم بتاع اللوجات

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"member joined: {member.mention}")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"member left: {member}")

@bot.event
async def on_member_ban(guild, user):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"user banned: {user}")

@bot.event
async def on_member_unban(guild, user):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"user unbanned: {user}")

# ================= AVATAR =================

@bot.tree.command(name="avatar", description="member pfp")
async def avatar(interaction: discord.Interaction, user: str = None):
    if not user:
        member = interaction.user
    else:
        member = await get_member(interaction, user)

    if not member:
        await interaction.response.send_message("member not found", ephemeral=True)
        return

    await interaction.response.send_message(member.display_avatar.url)

# ================= JOIN VOICE =================

async def get_voice_channel(interaction, channel_input):
    guild = interaction.guild

    # لو ID
    if channel_input.isdigit():
        return guild.get_channel(int(channel_input))

    # لو منشن
    if channel_input.startswith("<#") and channel_input.endswith(">"):
        channel_id = channel_input.replace("<#", "").replace(">", "")
        return guild.get_channel(int(channel_id))

    # لو اسم
    for channel in guild.voice_channels:
        if channel.name == channel_input:
            return channel

    return None


@bot.tree.command(name="join", description="join a room")
async def join(interaction: discord.Interaction, channel: str = None):

    # لو المستخدم في روم
    if not channel and interaction.user.voice:
        vc = interaction.user.voice.channel
    else:
        vc = await get_voice_channel(interaction, channel)

    if not vc:
        await interaction.response.send_message("room not fount", ephemeral=True)
        return

    try:
        await vc.connect()
        await interaction.response.send_message(f"joined!: {vc.name}")
    except:
        await interaction.response.send_message("error", ephemeral=True)

# ================= PROTECTION SYSTEM =================

whitelist_users = set()
whitelist_roles = set()

# ----------- CHECK WHITELIST -----------
def is_whitelisted(member):
    if member.id in whitelist_users:
        return True

    for role in member.roles:
        if role.id in whitelist_roles:
            return True

    return False

# ----------- ANTI KICK -----------
@bot.event
async def on_member_remove(member):
    guild = member.guild

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target.id == member.id:
            executor = entry.user

            if executor.bot:
                return

            if is_whitelisted(executor):
                return

            try:
                await guild.kick(executor, reason="Anti-kick protection")
                if guild.system_channel:
                    await guild.system_channel.send(f"{executor} was punished for unauthorized kick")
            except:
                pass

# ----------- ANTI BAN -----------
@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target.id == user.id:
            executor = entry.user

            if executor.bot:
                return

            if is_whitelisted(executor):
                return

            try:
                await guild.kick(executor, reason="Anti-ban protection")
                if guild.system_channel:
                    await guild.system_channel.send(f"{executor} was punished for unauthorized ban")
            except:
                pass

# ================= WHITELIST COMMANDS =================

@bot.tree.command(name="whitelist_add_user", description="Add a user to the whitelist")
async def whitelist_add_user(interaction: discord.Interaction, user: discord.Member):
    whitelist_users.add(user.id)
    await interaction.response.send_message(f"{user} added to whitelist")

@bot.tree.command(name="whitelist_remove_user", description="Remove a user from the whitelist")
async def whitelist_remove_user(interaction: discord.Interaction, user: discord.Member):
    whitelist_users.discard(user.id)
    await interaction.response.send_message(f"{user} removed from whitelist")

@bot.tree.command(name="whitelist_add_role", description="Add a role to the whitelist")
async def whitelist_add_role(interaction: discord.Interaction, role: discord.Role):
    whitelist_roles.add(role.id)
    await interaction.response.send_message(f"Role {role.name} added to whitelist")

@bot.tree.command(name="whitelist_remove_role", description="Remove a role from the whitelist")
async def whitelist_remove_role(interaction: discord.Interaction, role: discord.Role):
    whitelist_roles.discard(role.id)
    await interaction.response.send_message(f"Role {role.name} removed from whitelist")

# ================= TOKEN =================
token = os.getenv("TOKEN")

if not token:
    print("❌ مفيش TOKEN")
else:
    bot.run(token)

