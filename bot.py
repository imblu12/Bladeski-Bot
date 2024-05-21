import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import asyncio

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
    print(f'Bot is ready. Logged in as {bot.user.name}')

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

@bot.event
async def on_message(message):
    if message.channel.id == command_channel_id:
        try:
            await message.delete()
        except discord.errors.Forbidden:
            print(f"Failed to delete message in channel {command_channel_id}")
    await bot.process_commands(message)

bot.run('MTI0MTkxNjczODE3NDcxNzk4Mg.GtHXuJ.TSwsgwgcNpv5viGENPNackXezsSQaq16-VxhGs')
