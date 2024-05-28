import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import asyncio
import json
import os
import io
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

questions = [
    "How old are you?",
    "What is your time zone?",
    "Do you have any experiences with moderating? If so tell me.",
    "Are you in the clan?",
    "Why do you want to moderate in our server?",
    "Why should we chose you over other applicants",
    "What would you do if someone abused their confirmed clan donator role? (Everyone ping perms in giveaways channel)",
    "What would you do if someone spam pinged a user",
    "What would you do if someone starting being racist towards another user?",
    "What would you do if someone started disrespecting and hating other clans for no reason?"
]

application_channel_id = 1242322248074006538
command_channel_id = 1242321871161262111
user_warnings_dict = {}
warning_id_counter = 1

required_role = "Bladeski Bot Perms"  # Change this to the role you want to restrict commands to

# Function to convert duration to seconds
def convert_to_seconds(duration):
    seconds = 0
    if duration.endswith("s"):
        seconds = int(duration[:-1])
    elif duration.endswith("m"):
        seconds = int(duration[:-1]) * 60
    elif duration.endswith("h"):
        seconds = int(duration[:-1]) * 3600
    elif duration.endswith("d"):
        seconds = int(duration[:-1]) * 86400
    elif duration.endswith("w"):
        seconds = int(duration[:-1]) * 604800
    return seconds

def load_warnings():
    global user_warnings_dict, warning_id_counter
    if os.path.isfile("warnings.json"):
        try:
            with open("warnings.json", "r") as f:
                user_warnings_dict = json.load(f)
        except json.decoder.JSONDecodeError:
            # Handle the case where the file is empty or not valid JSON
            print("Warning: Unable to load warnings. Initializing user_warnings_dict as an empty dictionary.")
            user_warnings_dict = {}
    else:
        # If the file doesn't exist, initialize user_warnings_dict as an empty dictionary
        user_warnings_dict = {}
    
    # Update the warning_id_counter
    warning_id_counter = max((entry['id'] for warnings in user_warnings_dict.values() for entry in warnings), default=0) + 1


# Save warnings to file
def save_warnings():
    with open("warnings.json", "w") as f:
        json.dump(user_warnings_dict, f, indent=4)

class ConfirmView(View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()

class ReasonModal(Modal):
    def __init__(self, user, message, decision):
        self.user = user
        self.message = message
        self.decision = decision
        super().__init__(title=f"Reason for {decision}")

        self.reason_input = TextInput(label="Reason", style=discord.TextStyle.paragraph)
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value

        if self.decision == 'deny':
            embed = discord.Embed(title="Application Denied", color=discord.Color.red(), description=f"Your application at **Bladeski** was denied.\n\n**Reason:** {reason}")
            status_message = f"{self.user.mention}'s application has been denied by {interaction.user.mention} with reason: {reason}"
        else:
            embed = discord.Embed(title="Application Accepted", color=discord.Color.green(), description=f"Your application at **Bladeski** was accepted.\n\n**Reason:** {reason}")
            status_message = f"{self.user.mention}'s application has been accepted by {interaction.user.mention} with reason: {reason}"

        await self.user.send(embed=embed)
        await interaction.user.send(f"{self.user.mention} has been notified of your decision.")

        await self.message.edit(content=status_message, embed=self.message.embeds[0], view=None)
        await interaction.response.send_message("The user has been notified.", ephemeral=True)

class ApplicationReviewView(View):
    def __init__(self, bot, user, message):
        super().__init__()
        self.bot = bot
        self.user = user
        self.message = message

    @discord.ui.button(label='Accept With Reason', style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ReasonModal(user=self.user, message=self.message, decision='accept')
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Deny With Reason', style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ReasonModal(user=self.user, message=self.message, decision='deny')
        await interaction.response.send_modal(modal)

@bot.event
async def on_ready():
    load_warnings()
    print(f'Bot is ready. Logged in as {bot.user.name}')






# Define a set for faster lookup of blocked words
# Define a set for faster lookup of blocked words
blocked_words = {"nigga", "nigger", "nga", "kys", "retard", "nagger", "niger", "cunt", "faggot", "neger", "shit", "bitch", "hoe", "whore", "wetty", "wettie", "slag", "cock", "dick", "willy", "penis", "cunts", "fucks", "fuck", "shits", "niggers", "niggas", "ngas", "noggers", "nogers", "neggers", "negers", "cocks", "dicks", "shit"}

# Define a set for user IDs to be blacklisted
blacklisted_user_ids = {808785444204314696, 1193525137539076171, 1234119475717210133, 1214691014774890538}

async def warn_user(member, word):
    try:
        guild = member.guild
        warn_embed = discord.Embed(
            title="You have been warned!",
            description=f"You have been warned in **{guild.name}** for the usage of a blocked word: {word}.",
            color=discord.Color.red()
        )
        await member.send(embed=warn_embed)
    except Exception as e:
        print(f"An error occurred while warning the user: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Debug information
    print("Message Author ID:", message.author.id)
    print("Is in Blacklisted IDs:", message.author.id in blacklisted_user_ids)

    # Check if the message is from a blacklisted user
    if message.author.id in blacklisted_user_ids:
        return

    content = message.content.lower()
    for word in blocked_words:
        if word in content:
            await warn_user(message.author, word)
            await message.delete()
            break

    await bot.process_commands(message)






# Function to save warnings to file
def save_warnings():
    with open("warnings.json", "w") as file:
        json.dump(user_warnings_dict, file, indent=4)

# Function to log warning to mod logs
async def log_to_mod_logs(guild, user, blocked_word):
    try:
        # Fetch the mod log channel
        mod_log_channel_id = 1206690333220675595  # Update with your mod log channel ID
        mod_log_channel = guild.get_channel(mod_log_channel_id)
        
        if mod_log_channel is not None:
            # Construct the log message
            log_message = f"{user.mention} was warned for using a blocked word: {blocked_word}"
            
            # Send the log message
            await mod_log_channel.send(log_message)
            
            # Update user warnings
            user_mod_logs = user_warnings_dict.get(user.id, [])
            warning_entry = {"id": len(user_mod_logs) + 1, "message": f"Warned for using a blocked word: {blocked_word}"}
            user_mod_logs.append(warning_entry)
            user_warnings_dict[user.id] = user_mod_logs
            
            # Save warnings to file
            save_warnings()
            
            # Log success message
            print("Warning logged successfully.")
        else:
            # Log error if mod log channel is not found
            print("Mod log channel not found.")
    except Exception as e:
        # Log any exceptions that occur
        print(f"An error occurred while logging to mod logs: {e}")




@bot.event
async def on_message(message):
    if not message.author.bot:
        for word in blocked_words:
            if word.lower() in message.content.lower():
                await message.delete()
                await warn_user(message.author, word)
                await log_to_mod_logs(message.guild, message.author, word)  # Call the log function here
                break  # Only delete the message once and warn once per message

    await bot.process_commands(message)










@bot.command()
async def apply(ctx):
    user = ctx.author
    view = ConfirmView()
    await user.send("You are about to apply for staff at **Bladeski**. Do you wish to proceed? If so, please click **Yes** and fill out every question with detail for a higher chance of being accepted.", view=view)
    
    await view.wait()
    if view.value is None:
        await user.send('You did not respond in time. Please start the application process again.')
        return
    elif not view.value:
        await user.send('You have cancelled the application process.')
        return
    
    answers = []
    
    def check_response(m):
        return m.author == user and isinstance(m.channel, discord.DMChannel)
    
    for question in questions:
        await user.send(question)
        try:
            response = await bot.wait_for('message', check=check_response, timeout=120.0)
            answers.append(response.content)
        except asyncio.TimeoutError:
            await user.send('You took too long to respond. Please start the application process again.')
            return
    
    application_channel = bot.get_channel(application_channel_id)
    if application_channel is not None:
        embed = discord.Embed(title="New Staff Application", color=discord.Color.purple())
        
        embed.add_field(name="Questions", value="\n".join([f"**Q{i+1}:** {questions[i]}\n**A:** {answers[i]}" for i in range(len(questions))]), inline=False)
        
        embed.add_field(name="User Info", value=(
            f"**User ID:** {user.id}\n"
            f"**Username:** {user.name}#{user.discriminator}\n"
            f"**Server Join Date:** {user.joined_at.strftime('%Y-%m-%d %H:%M:%S') if user.joined_at else 'N/A'}"
        ), inline=False)
        
        view = ApplicationReviewView(bot, user, None)
        msg = await application_channel.send(embed=embed, view=view)
        view.message = msg
        await user.send('Your application has been submitted successfully.')
    else:
        await user.send('There was an error in processing your application. Please contact an administrator.')

@bot.command()
@commands.has_role(required_role)
async def modlogs(ctx, member: discord.Member):
    if member.id in user_warnings_dict:
        warning_list = user_warnings_dict[member.id]
        embed = discord.Embed(title=f"Mod Logs for {member.name}#{member.discriminator}", color=discord.Color.orange())
        for warning in warning_list:
            embed.add_field(name=f"Mod Log ID: {warning['id']}", value=warning['message'], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{member.mention} has no mod logs.")

@modlogs.error
async def modlogs_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    else:
        await ctx.send("An error occurred while trying to fetch mod logs.")

@bot.command()
@commands.has_role(required_role)
async def removelog(ctx, member: discord.Member, warning_id: int):
    if member.id in user_warnings_dict:
        warning_list = user_warnings_dict[member.id]
        new_warning_list = [warning for warning in warning_list if warning['id'] != warning_id]
        if len(new_warning_list) < len(warning_list):
            user_warnings_dict[member.id] = new_warning_list
            save_warnings()
            await ctx.send(f"Removed log with ID {warning_id} for {member.mention}.")
        else:
            await ctx.send(f"No log with ID {warning_id} found for {member.mention}.")
    else:
        await ctx.send(f"{member.mention} has no warnings.")

@removelog.error
async def removelog_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid member.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument. Please make sure to mention a valid member and provide a valid warning ID.")
    else:
        await ctx.send("An error occurred while trying to remove the warning.")

@bot.command()
@commands.has_role(required_role)
async def warn(ctx, member: discord.Member, *, reason: str):
    try:
        user_warnings = user_warnings_dict.get(member.id, [])
        
        # Find the highest warning ID for the user
        highest_warning_id = max([entry['id'] for entry in user_warnings], default=0)
        
        warning_message = f"You were warned by {ctx.author.name} for the reason: {reason}"
        warning_entry = {"id": highest_warning_id + 1, "message": warning_message}
        user_warnings.append(warning_entry)
        user_warnings_dict[member.id] = user_warnings
        
        embed = discord.Embed(title="Warning", color=discord.Color.purple())
        embed.add_field(name="You have been warned", value=f"You were warned by {ctx.author.mention} for the reason: {reason}", inline=False)
        await member.send(embed=embed)
        
        await ctx.send(f"Warned {member.mention} for the reason: {reason}.")
        save_warnings()  # Save warnings to file
    except Exception as e:
        print(f"An error occurred while trying to warn the user: {e}")

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid member.")
    else:
        await ctx.send("An error occurred while trying to warn the user.")

@bot.command()
@commands.has_role(required_role)
async def timeout(ctx, member: discord.Member, duration: str, *, reason: str):
    try:
        # Function to convert duration to seconds
        def convert_to_seconds(duration):
            seconds = 0
            if duration.endswith("s"):
                seconds = int(duration[:-1])
            elif duration.endswith("m"):
                seconds = int(duration[:-1]) * 60
            elif duration.endswith("h"):
                seconds = int(duration[:-1]) * 3600
            elif duration.endswith("d"):
                seconds = int(duration[:-1]) * 86400
            elif duration.endswith("w"):
                seconds = int(duration[:-1]) * 604800
            return seconds
        
        duration_seconds = convert_to_seconds(duration)
        
        # Revoke send message permissions for the member
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(member, send_messages=False)
        
        # Revoke connect permissions for the member in voice channels
        for channel in ctx.guild.voice_channels:
            await channel.set_permissions(member, connect=False)
        
        # Notify the user about the timeout
        await ctx.send(f"{member.mention} has been timed out for {duration} with the reason: {reason}.")
        
        # Log the timeout action in modlogs
        if member.id in user_warnings_dict:
            warning_list = user_warnings_dict[member.id]
        else:
            warning_list = []
        warning_list.append({"id": len(warning_list) + 1, "message": f"Timed out for {duration} with reason: {reason}"})
        user_warnings_dict[member.id] = warning_list
        
        # Schedule the unmute after the duration
        await asyncio.sleep(duration_seconds)
        
        # Restore permissions for the member
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(member, overwrite=None)
        for channel in ctx.guild.voice_channels:
            await channel.set_permissions(member, overwrite=None)
        
        # Notify about the end of the timeout
        await ctx.send(f"{member.mention}'s timeout has ended after {duration}.")
    except Exception as e:
        print(f"An error occurred while trying to timeout the user: {e}")
        await ctx.send(f"An error occurred while trying to timeout the user: {e}")

@timeout.error
async def timeout_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid member.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument. Please provide a valid duration (e.g., 1h, 30m).")
    else:
        await ctx.send("An error occurred while trying to timeout the user.")








@bot.command()
@commands.has_role(required_role)
async def ban(ctx, member: discord.Member, duration: str = None, *, reason: str):
    try:
        # Convert duration to seconds
        if duration:
            duration_seconds = convert_to_seconds(duration)
            duration_str = f" for {duration}"
        else:
            duration_seconds = None
            duration_str = " permanently"
        
        # Send a DM to the user before banning them
        dm_embed = discord.Embed(
            title="You have been banned",
            description=f"You have been banned from {ctx.guild.name}{duration_str} with the reason:\n\n{reason}",
            color=discord.Color.red()
        )
        await member.send(embed=dm_embed)
        
        # Ban the member
        await member.ban(reason=reason)
        
        # Log the ban action in mod logs
        mod_log_channel_id = 1233525245303066755  # Adjust the channel ID as needed
        mod_log_channel = bot.get_channel(mod_log_channel_id)
        if mod_log_channel is not None:
            ban_action_log_embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} was banned{duration_str} with the reason: {reason} by {ctx.author.mention}",
                color=discord.Color.red()
            )
            await mod_log_channel.send(embed=ban_action_log_embed)
        
        # Store the ban action in user's mod logs
        user_mod_logs = user_warnings_dict.get(member.id, [])
        ban_entry = {"id": len(user_mod_logs) + 1, "message": f"Banned{duration_str} with reason: {reason}"}
        user_mod_logs.append(ban_entry)
        user_warnings_dict[member.id] = user_mod_logs
        save_warnings()  # Save warnings to file
        
        # Schedule the unban after the duration if specified
        if duration_seconds:
            await asyncio.sleep(duration_seconds)
            await member.unban(reason="Ban duration expired")
            
            # Log the unban action in mod logs
            if mod_log_channel is not None:
                unban_action_log_embed = discord.Embed(
                    title="Member Unbanned",
                    description=f"{member.mention} was unbanned automatically after {duration}",
                    color=discord.Color.green()
                )
                await mod_log_channel.send(embed=unban_action_log_embed)
        
            await ctx.send(f"{member.mention} has been unbanned after {duration}.")
        else:
            await ctx.send(f"{member.mention} has been banned{duration_str} with reason: {reason}.")
    except Exception as e:
        print(f"An error occurred while trying to ban the user: {e}")


from typing import Union

@bot.command()
@commands.has_role(required_role)
async def unban(ctx, member: Union[discord.Member, discord.User], *, reason: str = "Unban requested"):
    try:
        # Unban the member
        await ctx.guild.unban(member, reason=reason)
        
        # Log the unban action in mod logs
        mod_log_channel_id = 1233525245303066755  # Adjust the channel ID as needed
        mod_log_channel = bot.get_channel(mod_log_channel_id)
        if mod_log_channel is not None:
            unban_action_log_embed = discord.Embed(
                title="Member Unbanned",
                description=f"{member.mention} has been unbanned by {ctx.author.mention} with reason: {reason}",
                color=discord.Color.green()
            )
            await mod_log_channel.send(embed=unban_action_log_embed)
        
        await ctx.send(f"{member.mention} has been unbanned.")
    except Exception as e:
        print(f"An error occurred while trying to unban the user: {e}")


@bot.command()
async def cmds(ctx):
    try:
        # Get all the commands available to the user
        commands_list = [f"!{command.name}" for command in bot.commands if await command.can_run(ctx)]
        
        # Sort the commands alphabetically
        commands_list.sort()
        
        # Create an embed to display the commands
        embed = discord.Embed(
            title="Available Commands",
            description="\n".join(commands_list),
            color=discord.Color.blue()
        )
        
        # Send the embed to the user
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"An error occurred while trying to fetch the list of commands: {e}")
        await ctx.send("An error occurred while trying to fetch the list of commands.")

# Make sure to adjust the color and styling of the embed as desired.


@bot.command()
async def embed(ctx, channel: discord.TextChannel, color: str, *, content: str):
    try:
        # Convert the color string to a discord.Color object
        color = discord.Color(int(color, 16))
        
        # Create the embed
        embed = discord.Embed(description=content, color=color)
        
        # Send the embed to the specified channel
        message = await channel.send(embed=embed)
        
        # Delete the invoking message
        await ctx.message.delete()
        
        # Confirm to the user that the embed has been created
        await ctx.send(f"Embed created successfully in {channel.mention}.", delete_after=5)
    except Exception as e:
        print(f"An error occurred while trying to create the embed: {e}")
        await ctx.send("An error occurred while trying to create the embed.")

# Define the function to create embeds and delete the invoking message
async def embed_create(ctx, content):
    try:
        # Parse the user input to extract channel ID, color, and content
        channel_id, color, *content = content.split(" ")
        
        # Get the channel object using the channel ID
        channel = bot.get_channel(int(channel_id))
        
        if not channel:
            await ctx.send("Invalid channel ID.")
            return
        
        # Convert the color string to a discord.Color object
        color = discord.Color(int(color, 16))
        
        # Create the embed
        embed = discord.Embed(description=" ".join(content), color=color)
        
        # Send the embed to the specified channel
        message = await channel.send(embed=embed)
        
        # Delete the invoking message
        await ctx.message.delete()
        
        # Confirm to the user that the embed has been created
        await ctx.send(f"Embed created successfully in {channel.mention}.", delete_after=5)
    except Exception as e:
        print(f"An error occurred while trying to create the embed: {e}")
        await ctx.send("An error occurred while trying to create the embed.")



# Adjust the color and styling of the embed as needed.




@bot.command()
@commands.has_role(required_role)
async def addrole(ctx, member: discord.Member, *, role: Union[discord.Role, str]):
    try:
        # Resolve the role mentioned
        if isinstance(role, str):
            role = discord.utils.find(lambda r: r.name == role or str(r.id) == role or role.strip("@") in (r.name for r in ctx.guild.roles), ctx.guild.roles)
        
        # Check if the role was found
        if not role:
            await ctx.send("Role not found.")
            return
        
        # Add the role to the member
        await member.add_roles(role)
        
        # Confirm to the user that the role has been added successfully
        await ctx.send(f"{member.mention} has been given the role {role.name}.")
    except Exception as e:
        print(f"An error occurred while trying to add the role: {e}")
        await ctx.send("An error occurred while trying to add the role.")




@bot.command()
@commands.has_role(required_role)
async def removerole(ctx, member: discord.Member, *, role: Union[discord.Role, str]):
    try:
        # Resolve the role mentioned
        if isinstance(role, str):
            role = discord.utils.find(lambda r: r.name == role or str(r.id) == role or role.strip("@") in (r.name for r in ctx.guild.roles), ctx.guild.roles)
        
        # Check if the role was found
        if not role:
            await ctx.send("Role not found.")
            return
        
        # Remove the role from the member
        await member.remove_roles(role)
        
        # Confirm to the user that the role has been removed successfully
        await ctx.send(f"{member.mention} no longer has the role {role.name}.")
    except Exception as e:
        print(f"An error occurred while trying to remove the role: {e}")
        await ctx.send("An error occurred while trying to remove the role.")



@bot.command()
@commands.has_role(required_role)
async def status(ctx, flag: bool):
    try:
        # Define the channel where the status embed will be sent
        status_channel_id = 1239174887432650752  # Replace with the actual channel ID
        
        # Get the status channel
        status_channel = bot.get_channel(status_channel_id)
        if not status_channel:
            await ctx.send("Status channel not found.")
            return
        
        # Create and send the appropriate embed based on the flag value
        if flag:
            embed = discord.Embed(title="Bladeski Status", description="Bladeski is no longer full! Create a ticket and apply ASAP before spots are taken.", color=discord.Color.green())
        else:
            embed = discord.Embed(title="Bladeski Status", description="Bladeski is currently full, meaning that you will be put on a waitlist. Spots open up every week, when kicks happen.", color=discord.Color.red())
        
        await status_channel.send(embed=embed)
        
        await ctx.send("Status updated successfully.")
    except Exception as e:
        print(f"An error occurred while trying to update status: {e}")
        await ctx.send("An error occurred while trying to update status.")




@bot.command()
@commands.has_role(required_role)
async def kick(ctx, member: discord.Member, *, reason: str):
    try:
        # Send a DM to the kicked user
        kick_embed = discord.Embed(
            title="You have been kicked",
            description=f"You have been kicked from {ctx.guild.name} for the following reason:\n\n{reason}",
            color=discord.Color.red()
        )
        kick_embed.set_footer(text=f"Kicked by {ctx.author.name}")
        await member.send(embed=kick_embed)
        
        # Log the kick action in mod logs
        mod_log_channel_id = 1233525245303066755  # Adjust the channel ID as needed
        mod_log_channel = bot.get_channel(mod_log_channel_id)
        if mod_log_channel is not None:
            kick_log_embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} was kicked by {ctx.author.mention} for {reason}",
                color=discord.Color.red()
            )
            await mod_log_channel.send(embed=kick_log_embed)
        
        # Kick the member
        await member.kick(reason=reason)
        
        await ctx.send(f"{member.mention} has been kicked from the server.")
        
    except Exception as e:
        print(f"An error occurred while trying to kick the user: {e}")
        await ctx.send("An error occurred while trying to kick the user.")




@bot.command()
@commands.has_role(required_role)
async def purge(ctx, limit: int):
    try:
        # Delete the specified number of messages from the channel
        deleted = await ctx.channel.purge(limit=limit + 1)  # Add 1 to include the command message itself
        
        # Send a message confirming the purge and indicating the number of messages deleted
        await ctx.send(f"{len(deleted) - 1} messages deleted successfully.")
    except Exception as e:
        print(f"An error occurred while trying to purge messages: {e}")
        await ctx.send("An error occurred while trying to purge messages.")





import asyncio

import asyncio

@bot.command()
@commands.has_role(required_role)
async def poll(ctx, title, duration: str, *answers):
    try:
        # Convert duration to seconds
        duration_seconds = convert_to_seconds(duration)
        
        # Check if duration is valid
        if duration_seconds <= 0:
            await ctx.send("Duration must be a positive integer.")
            return
        
        # Check if there are enough answers
        if len(answers) < 2:
            await ctx.send("You need to provide at least 2 answers for the poll.")
            return
        
        # Format the poll message
        poll_message = f"**Poll:** {title}\n\n"
        for i, answer in enumerate(answers):
            poll_message += f":{chr(127462 + i)}: {answer}\n"
        
        # Send the poll message
        poll_embed = discord.Embed(title="Poll", description=poll_message, color=discord.Color.blue())
        poll_embed.set_footer(text=f"Poll created by {ctx.author.display_name} • Ends in {duration}")
        poll_message = await ctx.send(embed=poll_embed)
        
        # Add reactions to the poll message for each answer
        for i in range(len(answers)):
            await poll_message.add_reaction(chr(127462 + i))
        
        await ctx.send("Poll created successfully.")
        
        # Start timer for poll duration
        while duration_seconds > 0:
            await asyncio.sleep(60)  # Sleep for 1 minute
            duration_seconds -= 60  # Subtract 1 minute from remaining duration
            
            # Update footer with remaining time
            poll_embed.set_footer(text=f"Poll created by {ctx.author.display_name} • Ends in {duration_seconds // 60} minutes")
            await poll_message.edit(embed=poll_embed)
        
        # Fetch the poll message to end it
        poll_message = await ctx.channel.fetch_message(poll_message.id)
        
        # Retrieve reactions from the poll message
        reactions = poll_message.reactions
        
        # Format and display poll results
        poll_results = ""
        for reaction in reactions:
            if isinstance(reaction.emoji, str):
                emoji = reaction.emoji
            else:
                emoji = reaction.emoji.name
            poll_results += f"{emoji}: {reaction.count - 1} votes\n"  # Subtract 1 to exclude bot's reaction
        
        poll_results_embed = discord.Embed(title="Poll Results", description=poll_results, color=discord.Color.green())
        await ctx.send(embed=poll_results_embed)
        
        # Delete the poll message
        await poll_message.delete()
        
    except Exception as e:
        print(f"An error occurred while trying to create or end a poll: {e}")
        await ctx.send("An error occurred while trying to create or end a poll.")




@bot.command()
@commands.has_role(required_role)
async def deletepoll(ctx, message_id: int):
    try:
        # Fetch the message to delete
        message = await ctx.channel.fetch_message(message_id)
        
        # Check if the message is a poll
        if not message.embeds or not message.embeds[0].title == "Poll":
            await ctx.send("The specified message is not a poll.")
            return
        
        # Delete the poll message
        await message.delete()
        
        await ctx.send("Poll deleted successfully.")
    except discord.NotFound:
        await ctx.send("Message not found.")
    except Exception as e:
        print(f"An error occurred while trying to delete the poll: {e}")
        await ctx.send("An error occurred while trying to delete the poll.")




@bot.command()
@commands.has_role(required_role)
async def endpoll(ctx, message_id: int):
    try:
        # Fetch the poll message
        message = await ctx.channel.fetch_message(message_id)
        
        # Check if the message is a poll
        if not message.embeds or not message.embeds[0].title == "Poll":
            await ctx.send("The specified message is not a poll.")
            return
        
        # Retrieve reactions from the poll message
        reactions = message.reactions
        
        # Format and display poll results
        poll_results = ""
        for reaction in reactions:
            if isinstance(reaction.emoji, str):
                emoji = reaction.emoji
            else:
                emoji = reaction.emoji.name
            poll_results += f"{emoji}: {reaction.count - 1} votes\n"  # Subtract 1 to exclude bot's reaction
        
        poll_embed = discord.Embed(title="Poll Results", description=poll_results, color=discord.Color.green())
        await ctx.send(embed=poll_embed)
        
        # Delete the poll message
        await message.delete()
        
        await ctx.send("Poll ended successfully.")
    except discord.NotFound:
        await ctx.send("Message not found.")
    except Exception as e:
        print(f"An error occurred while trying to end the poll: {e}")
        await ctx.send("An error occurred while trying to end the poll.")

# Add the !endpoll command to the !cmds list




@bot.command()
@commands.has_role(required_role)
async def clearwarns(ctx, member: discord.Member):
    try:
        # Check if the user has any warnings
        if member.id not in user_warnings_dict:
            await ctx.send(f"{member.display_name} has no warnings.")
            return
        
        # Clear the warnings for the user
        del user_warnings_dict[member.id]
        save_warnings()  # Save warnings to file
        
        await ctx.send(f"Warnings cleared for {member.display_name}.")
    except Exception as e:
        print(f"An error occurred while trying to clear warnings: {e}")
        await ctx.send("An error occurred while trying to clear warnings.")




@bot.command()
@commands.has_role(required_role)
async def nickname(ctx, member: discord.Member, *, nickname: str):
    try:
        await member.edit(nick=nickname)
        await ctx.send(f"Nickname for {member.mention} has been updated to {nickname}.")
    except Exception as e:
        print(f"An error occurred while trying to change the nickname: {e}")
        await ctx.send("An error occurred while trying to change the nickname.")



@bot.command()
@commands.has_role(required_role)
async def slowmode(ctx, channel: discord.TextChannel, amount: str):
    try:
        # Convert amount to seconds
        if amount.endswith('h'):
            numeric_amount = int(amount[:-1]) * 3600
        elif amount.endswith('m'):
            numeric_amount = int(amount[:-1]) * 60
        elif amount.endswith('s'):
            numeric_amount = int(amount[:-1])
        else:
            numeric_amount = int(amount)
        
        await channel.edit(slowmode_delay=numeric_amount)
        await ctx.send(f"Slowmode in {channel.mention} set to {numeric_amount} seconds.")
    except ValueError:
        await ctx.send("Invalid amount. Please provide a valid integer value followed by 's' for seconds, 'm' for minutes, or 'h' for hours.")
    except Exception as e:
        print(f"An error occurred while setting slowmode: {e}")
        await ctx.send("Failed to set slowmode. Please check the channel and try again.")





@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild

    embed = discord.Embed(title=f"{guild.name} Server Information", color=discord.Color.purple())
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.add_field(name="Owner", value=guild.owner, inline=False)
    embed.add_field(name="Creation Date", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Total Members", value=guild.member_count, inline=False)
    embed.add_field(name="Total Channels", value=len(guild.channels), inline=False)
    embed.add_field(name="Total Roles", value=len(guild.roles), inline=False)

    await ctx.send(embed=embed)




@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    embed = discord.Embed(title=f"{member.name}'s Information", color=discord.Color.purple())
    embed.set_thumbnail(url=member.avatar.url if member.avatar else discord.Embed.Empty)
    embed.add_field(name="Username", value=member.name, inline=False)
    embed.add_field(name="Discriminator", value=member.discriminator, inline=False)
    embed.add_field(name="User ID", value=member.id, inline=False)
    embed.add_field(name="Nick", value=member.nick if member.nick else "None", inline=False)
    embed.add_field(name="Status", value=member.status, inline=False)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Joined Discord", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)

    roles = [role.name for role in member.roles if role.name != "@everyone"]
    if roles:
        embed.add_field(name="Roles", value=", ".join(roles), inline=False)
    
    permissions = "\n".join([f"{perm[0]}: {perm[1]}" for perm in member.guild_permissions])
    embed.add_field(name="Permissions", value=permissions, inline=False)

    await ctx.send(embed=embed)





@bot.command()
@commands.has_role(required_role)
async def setprefix(ctx, new_prefix: str):
    try:
        # Update the bot's command prefix
        bot.command_prefix = new_prefix
        await ctx.send(f"Command prefix has been updated to `{new_prefix}`.")
    except Exception as e:
        print(f"An error occurred while trying to set the command prefix: {e}")
        await ctx.send("An error occurred while trying to set the command prefix.")



@bot.command()
@commands.has_role(required_role)
async def announce(ctx, channel: discord.TextChannel, *, message: str):
    try:
        # Send the announcement message to the specified channel
        await channel.send(message)
        await ctx.send("Announcement sent successfully.")
    except Exception as e:
        print(f"An error occurred while trying to send the announcement: {e}")
        await ctx.send("An error occurred while trying to send the announcement.")




@bot.command()
async def suggest(ctx, *, content: str):
    try:
        # Specify the channel where suggestions should be sent
        suggestion_channel_id = 1184883055840735292  # Replace with the ID of your suggestion channel
        
        # Get the suggestion channel
        suggestion_channel = bot.get_channel(suggestion_channel_id)
        
        if suggestion_channel is None:
            await ctx.send("Suggestion channel not found. Please contact the server administrator.")
            return
        
        # Send the suggestion to the suggestion channel
        suggestion_embed = discord.Embed(
            title="New Suggestion",
            description=f"**From:** {ctx.author.mention}\n\n{content}",
            color=discord.Color.gold()
        )
        await suggestion_channel.send(embed=suggestion_embed)
        
        await ctx.send("Your suggestion has been submitted successfully.")
    except Exception as e:
        print(f"An error occurred while trying to submit the suggestion: {e}")
        await ctx.send("An error occurred while trying to submit the suggestion.")




from discord.ext import commands, tasks





# Replace these with your actual role IDs and channel IDs
ROLE_ID_1 = 1239187630701154305
ROLE_ID_2 = 1185900743144775750
TRANSCRIPT_CHANNEL_ID = 1244326949677961237
CHANNEL_ID = 1239174887432650752  # replace with your channel ID

class ApplicationModal(discord.ui.Modal):
    def __init__(self, user, category):
        super().__init__(title="Bladeski Application")
        self.user = user
        self.category = category

        self.username = discord.ui.TextInput(label="Your Roblox Username", required=True)
        self.ap_amount = discord.ui.TextInput(label="How Much AP P/W (Blank if applying for CW)", required=False)
        self.elo_amount = discord.ui.TextInput(label="Your ELO (Blank if applying for Clan Grinder)", required=False)
        self.extra_words = discord.ui.TextInput(label="If you have anything else to ask, Let Us Know", required=False)

        self.add_item(self.username)
        self.add_item(self.ap_amount)
        self.add_item(self.elo_amount)
        self.add_item(self.extra_words)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        channel_name = f"ticket-{self.user.name}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, view_channel=True),
            guild.get_role(ROLE_ID_1): discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_permissions=True, view_channel=True),
            guild.get_role(ROLE_ID_2): discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_permissions=True, view_channel=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_permissions=True, view_channel=True)
        }

        category = discord.utils.get(guild.categories, id=self.category)
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
        
        embed = discord.Embed(
            title="Bladeski Application",
            description=f"{self.user.mention} has applied for **Bladeski**.",
            color=discord.Color.purple()
        )
        embed.add_field(name="Roblox Username", value=self.username.value, inline=False)
        embed.add_field(name="Activity Points P/W", value=self.ap_amount.value, inline=False)
        embed.add_field(name="ELO (If Applying For CW's)", value=self.elo_amount.value, inline=False)
        embed.add_field(name="Questions (If any)", value=self.extra_words.value, inline=False)
        embed.set_footer(text="Please wait for a staff member to review your application.")

        view = TicketView(channel.id)
        await channel.send(embed=embed, view=view)
        await interaction.followup.send(f"Your application has been submitted and a new channel has been created: {channel.mention}", ephemeral=True)

class ApplicationView(discord.ui.View):
    def __init__(self, category):
        super().__init__()
        self.category = category

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.primary)
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ApplicationModal(user=interaction.user, category=self.category)
        await interaction.response.send_modal(modal)

class TicketView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="Close/Waitlist", style=discord.ButtonStyle.primary, custom_id="close_waitlist")
    async def close_waitlist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if any(role.id in [ROLE_ID_1, ROLE_ID_2] for role in interaction.user.roles):
            await interaction.response.send_message("You are about to **Close/Waitlist** this ticket, do you wish to proceed?", view=ConfirmationView(self.channel_id), ephemeral=True)
        else:
            await interaction.response.send_message("You do not have permission to use this button.", ephemeral=True)

class ConfirmationView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=60)
        self.channel_id = channel_id

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        transcript = await generate_transcript(channel)
        transcript_channel = interaction.guild.get_channel(TRANSCRIPT_CHANNEL_ID)
        await transcript_channel.send(file=transcript)
        await channel.delete()
        await interaction.response.send_message("The ticket has been closed and the transcript has been saved.", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        await interaction.response.send_message("Cancelling", ephemeral=True)

async def generate_transcript(channel):
    messages = [message async for message in channel.history(limit=None, oldest_first=True)]
    transcript_text = ""

    for message in messages:
        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        transcript_text += f"[{timestamp}] {message.author}: {message.content}\n"

    transcript_file = discord.File(io.BytesIO(transcript_text.encode()), filename=f"transcript-{channel.name}.txt")
    return transcript_file

@tasks.loop(seconds=60)
async def send_and_delete_message():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.purge(limit=None)
        embed = discord.Embed(
            title="Apply For Bladeski",
            description="Click on the blue button to apply for **Bladeski**, And type in the ticket if you're applying for **Clan Grinder** Or **Clan Warrior/Mainteam**",
            color=discord.Color.purple()
        )
        view = ApplicationView(category=1239197040760717423)  # Replace with your category ID
        message = await channel.send(embed=embed, view=view)
        await asyncio.sleep(58)
        await message.delete()



async def clear_channel_and_send_embed():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.purge(limit=None)
        embed = discord.Embed(
            title="Apply For Bladeski",
            description="Click on the blue button to apply for **Bladeski**, And type in the ticket if you're applying for **Clan Grinder** Or **Clan Warrior/Mainteam**",
            color=discord.Color.purple()
        )
        view = ApplicationView(category=1239197040760717423)  # Replace with your category ID
        await channel.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    await clear_channel_and_send_embed()
    send_and_delete_message.start()

@bot.command(name='sendticketembed')
@commands.has_role('Bladeski Bot Perms')
async def sendticketembed(ctx):
    if ctx.channel.id == CHANNEL_ID:
        await ctx.channel.purge(limit=None)
        embed = discord.Embed(
            title="Apply For Bladeski",
            description="Click on the blue button to apply for **Bladeski**, And type in the ticket if you're applying for **Clan Grinder** Or **Clan Warrior/Mainteam**",
            color=discord.Color.purple()
        )
        view = ApplicationView(category=1239197040760717423)  # Replace with your category ID
        message = await ctx.send(embed=embed, view=view)
        await asyncio.sleep(28)
        await message.delete()




# Store user data in memory
user_data = {}

# Define roles required
required_role_names = ['Clan Grinder', 'Clan Warriors']  # Roles required for setting Roblox user
admin_role_name = 'Bladeski Bot Perms'  # Role required for checking Roblox users
check_role_names = ['Clan Grinder', 'Clan Warriors']  # Roles to check in the checkrobloxusers command


@bot.command()
async def setrobloxuser(ctx, username: str):
    # Check if user has any of the required roles
    if has_roles(ctx.author, required_role_names):
        user_data[ctx.author.id] = username
        await ctx.send(f'{ctx.author.mention}, your Roblox username has been set to `{username}`.')
    else:
        await ctx.send(f'{ctx.author.mention}, you do not have any of the required roles to set your Roblox username.')

@bot.command()
@commands.has_role(admin_role_name)
async def checkrobloxusers(ctx):
    try:
        description = ""
        for member in ctx.guild.members:
            if any(role.name in check_role_names for role in member.roles):
                roblox_username = user_data.get(member.id, 'not set')
                description += f'{member.mention} - {roblox_username}\n'
        
        if not description:
            description = "No members with the specified roles found."

        embed = discord.Embed(title="Roblox Users", description=description, color=discord.Color.purple())
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f'An error occurred while trying to execute the command: {str(e)}')
        print(f'Error in checkrobloxusers: {str(e)}')

def has_roles(member, role_names):
    roles = [role.name for role in member.roles]
    return any(role_name in roles for role_name in role_names)








# Error handlers
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid member.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument. Please provide a valid duration (e.g., 1d, 7d).")
    else:
        await ctx.send("An error occurred while trying to execute the command.")


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid member.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument. Please provide a valid duration (e.g., 1d, 7d).")
    else:
        await ctx.send("An error occurred while trying to ban the user.")


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid member.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument. Please provide a valid duration (e.g., 1d, 7d).")
    else:
        await ctx.send("An error occurred while trying to ban the user.")


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid member.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument. Please provide a valid duration (e.g., 1d, 7d).")
    else:
        await ctx.send("An error occurred while trying to ban the user.")


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member not found. Please mention a valid member.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument. Please provide a valid duration (e.g., 1d, 7d).")
    else:
        await ctx.send("An error occurred while trying to ban the user.")
