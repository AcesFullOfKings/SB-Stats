import discord
import sqlite3
import random

from discord import app_commands
from discord.ext import commands
from credentials import oAuth_token

# Intents setup
intents = discord.Intents.default()
intents.reactions = True
#intents.messages = True  # Required for reaction monitoring
no_mentions=discord.AllowedMentions.none()

# Bot setup
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# Database setup
conn = sqlite3.connect("SBCoin_ledger.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	awarder_id TEXT NOT NULL,
	receiver_id TEXT NOT NULL,
	message_id TEXT NOT NULL,
	amount integer,
	UNIQUE(awarder_id, receiver_id, message_id)
)
''')
cursor.execute('''
CREATE INDEX IF NOT EXISTS idx_receiver_id ON transactions (receiver_id)
''')
conn.commit()

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user}!")
	await tree.sync()

@bot.event
async def on_raw_reaction_add(payload):
	"""Handles reactions on messages, including historic messages not in cache."""
	# Ensure it's the SBCoin emoji
	if payload.emoji.is_custom_emoji() and payload.emoji.id in [1032063250478661672, 1323256554677600329]:  # Replace with your emoji name
		try:
			# Fetch the channel and message
			channel = bot.get_channel(payload.channel_id)
			if channel is None:
				print(f"Channel {payload.channel_id} not found.")
				return

			message = await channel.fetch_message(payload.message_id)
			user = await bot.fetch_user(payload.user_id)  # Use fetch_user instead of get_user
			if user is None:
				print(f"User {payload.user_id} not found even after fetching.")
				return

			# Ignore if the user reacted to their own message
			if message.author.id == user.id:
				print(f"Ignoring own reaction from {user} ;)")
				return

			# Record the SBCoin transaction
			try:
				cursor.execute(
					'''INSERT OR IGNORE INTO transactions (awarder_id, receiver_id, message_id, amount)
					VALUES (?, ?, ?, ?)''',
					(user.id, message.author.id, message.id, 1)
				)
				conn.commit()
				if cursor.rowcount > 0:
					print(f"SBCoin awarded: {user} -> {message.author}")
			except Exception as e:
				print(f"Error tracking SBCoin reaction: {e}")
		except Exception as e:
			print(f"Error processing raw reaction: {e}")

@bot.tree.command(name="balance", description="Checks a user's SBCoin balance.")
@app_commands.describe(user="The user whose balance to check.")
@app_commands.describe(hide="Only you can see the response.")
async def balance(interaction: discord.Interaction, user: discord.User = None, hide:bool=False):
	"""Check a user's SBCoin balance."""
	if user is None:
		user = interaction.user

	cursor.execute(
		'''SELECT SUM(amount) FROM transactions WHERE receiver_id = ?''', (user.id,)
	)
	balance = cursor.fetchone()[0]
	if balance is None or balance == 0:
		balance = "no"
	await interaction.response.send_message(f"{user.mention} has {balance} SBCoin.",allowed_mentions=no_mentions, ephemeral=hide)

@bot.tree.command(name="gamble", description="Gamble your fortunes away.")
@app_commands.describe(amount="The amount to gamble.")
@app_commands.describe(hide="Only you can see the response.")
async def balance(interaction: discord.Interaction, amount:int, hide:bool=False):
	if amount <= 0:
		await interaction.response.send_message("The amount must be a positive integer.", ephemeral=True)
		return
	if random.random() > 0.49:
		cursor.execute(
			'''INSERT INTO transactions (awarder_id, receiver_id, message_id, amount)
			VALUES (?, ?, ?, ?)''',
			(interaction.user.id, interaction.user.id, interaction.id, -amount)
		)

		conn.commit()

		# Check new balance
		cursor.execute(
			'''SELECT SUM(amount) FROM transactions WHERE receiver_id = ?''', (interaction.user.id,)
		)
		new_balance = cursor.fetchone()[0] or 0
		await interaction.response.send_message(f"You gambled {amount} and lost! :( Now you only have {new_balance} SBCoin", ephemeral=hide)
		print(f"{interaction.user} gambled {amount} and lost. Their new balance is {new_balance}")
	else:
		cursor.execute(
			'''INSERT INTO transactions (awarder_id, receiver_id, message_id, amount)
			VALUES (?, ?, ?, ?)''',
			(interaction.user.id, interaction.user.id, interaction.id, amount)
		)

		conn.commit()

		# Check new balance
		cursor.execute(
			'''SELECT SUM(amount) FROM transactions WHERE receiver_id = ?''', (interaction.user.id,)
		)
		new_balance = cursor.fetchone()[0] or 0
		await interaction.response.send_message(f"You gambled {amount} and won! :D Now you have {new_balance} SBCoin.", ephemeral=hide)
		print(f"{interaction.user} gambled {amount} and won! Their new balance is {new_balance}")

@bot.tree.command(name="send", description="Send your hoarded treasures to someone else.")
@app_commands.describe(recipient="The user to send your coin to.")
@app_commands.describe(amount="The amount to send.")
async def send(interaction: discord.Interaction, recipient: discord.User, amount: int):
	"""Send SBCoin to another user."""
	if amount <= 0:
		await interaction.response.send_message("The amount must be a positive integer.", ephemeral=True)
		return

	if interaction.user.id == recipient.id:
		await interaction.response.send_message("Don't be silly, you can't send coin to yourself.", ephemeral=True)
		return

	# Check sender's balance
	cursor.execute(
		'''SELECT SUM(amount) FROM transactions WHERE receiver_id = ?''', (interaction.user.id,)
	)
	sender_balance = cursor.fetchone()[0] or 0

	if sender_balance < amount:
		await interaction.response.send_message(f"You do not have enough SBCoin to send {amount}. You currently have {sender_balance}.",allowed_mentions=no_mentions, ephemeral=True)
		return

	# Record the transaction
	try:
		cursor.execute(
			'''INSERT INTO transactions (awarder_id, receiver_id, message_id, amount)
			VALUES (?, ?, ?, ?)''',
			(recipient.id, interaction.user.id, interaction.id, -amount)
		)
		cursor.execute(
			'''INSERT INTO transactions (awarder_id, receiver_id, message_id, amount)
			VALUES (?, ?, ?, ?)''',
			(interaction.user.id, recipient.id, interaction.id, amount)
		)
		conn.commit()
		# Check recipient's balance
		cursor.execute(
			'''SELECT SUM(amount) FROM transactions WHERE receiver_id = ?''', (recipient.id,)
		)
		recipient_balance = cursor.fetchone()[0] or 0
		await interaction.response.send_message(f"{interaction.user.mention} sent {amount} SBCoin to {recipient.mention}. {interaction.user.mention} now has {sender_balance-amount} and {recipient.mention} now has {recipient_balance}.",allowed_mentions=no_mentions)
	except Exception as e:
		await interaction.response.send_message("An error occurred while processing the transaction.")
		print(f"Error processing send command: {e}")

bot.run(oAuth_token)
