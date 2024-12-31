import discord
import sqlite3
import random

from asyncio import sleep
from time import localtime, time
from discord import app_commands
from discord.ext import commands
from credentials import oAuth_token

intents = discord.Intents.default()
intents.reactions = True
no_mentions=discord.AllowedMentions.none()

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

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
CREATE TABLE IF NOT EXISTS users (
	userID TEXT NOT NULL,
	username TEXT NOT NULL
)
''')

conn.commit()


def log(log_text):
	"""
	Takes a string, s, and logs it to a log file on disk with a timestamp. Also prints the string to console.
	"""
	current_time = localtime()
	# year   = str(current_time.tm_year)
	month  = str(current_time.tm_mon ).zfill(2)
	day    = str(current_time.tm_mday).zfill(2)
	hour   = str(current_time.tm_hour).zfill(2)
	minute = str(current_time.tm_min ).zfill(2)
	second = str(current_time.tm_sec ).zfill(2)

	log_time = f"{day}/{month} {hour}:{minute}:{second}"
	log_text = log_text.replace("\n", "").replace("\r", "") # makes sure each log line is only one line

	print(f"{hour}:{minute} - {log_text}")
	with open("log.txt", "a", encoding="utf-8") as f:
		f.write(log_time + " - " + log_text + "\n")

async def first_update():
	log(f"Beginning first_update()")
	cursor.execute("select awarder_id, receiver_id from transactions")
	rows = cursor.fetchall()

	for row in rows:
		awarder_id, receiver_id = row

		try:
			await save_userID(awarder_id)
		except Exception as ex:
			log(f"Error when saving userID {awarder_id} - {ex}")

		try:
			await save_userID(receiver_id)
		except Exception as ex:
			log(f"Error when saving userID {receiver_id} - {ex}")

async def save_userID(userID):
	cursor.execute("Select * from users where userID=?", (userID,))
	result = cursor.fetchone()

	if not result:
		discord_user = await bot.fetch_user(userID)
		username = str(discord_user)
		log(f"Saving userID {userID} -> {username}")
		cursor.execute("Insert into users (userID, username) values (?,?)", (userID,username))
		conn.commit()
		await sleep(1)

@bot.event
async def on_ready():
	log(f"Logged in as {bot.user}!")
	await tree.sync()
	await first_update()

@bot.event
async def on_raw_reaction_add(payload):
	"""Handles reactions on messages, including historic messages not in cache."""
	# Ensure it's the SBCoin emoji
	if payload.emoji.is_custom_emoji() and payload.emoji.id in [1032063250478661672, 1323256554677600329]:
		try:
			channel = bot.get_channel(payload.channel_id)
			if channel is None:
				log(f"Channel {payload.channel_id} not found.")
				return

			message = await channel.fetch_message(payload.message_id)
			user = await bot.fetch_user(payload.user_id)  # Use fetch_user instead of get_user
			if user is None:
				log(f"User {payload.user_id} not found even after fetching.")
				return

			await save_userID(payload.user_id)

			# Ignore if the user reacted to their own message
			if message.author.id == user.id:
				log(f"Ignoring own reaction from {user} ;)")
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
					log(f"SBCoin awarded: {user} -> {message.author}")
			except Exception as e:
				log(f"Error tracking SBCoin reaction: {e}")
		except Exception as e:
			log(f"Error processing raw reaction: {e}")

@bot.tree.command(name="balance", description="Checks a user's SBCoin balance.")
@app_commands.describe(user="The user whose balance to check.")
@app_commands.describe(hide="Only you can see the response.")
async def balance(interaction: discord.Interaction, user: discord.User = None, hide:bool=False):
	"""Check a user's SBCoin balance."""
	if user is None:
		user = interaction.user

	await save_userID(interaction.user.id)

	cursor.execute(
		'''SELECT SUM(amount) FROM transactions WHERE receiver_id = ?''', (user.id,)
	)
	balance = cursor.fetchone()[0]
	if balance is None or balance == 0:
		balance = "no"
	await interaction.response.send_message(f"{user.mention} has {balance} SBCoin.", allowed_mentions=no_mentions, ephemeral=hide)

cooldowns = dict()

@bot.tree.command(name="gamble", description="Gamble your fortunes away.")
@app_commands.describe(amount="The amount to gamble.")
@app_commands.describe(hide="Only you can see the response.")
async def balance(interaction: discord.Interaction, amount:int, hide:bool=False):
	if not hide:
		if cooldowns.get(interaction.user.id, 0) >= time()-60:
			log(f"{interaction.user} tried to gamble {amount}, but is on cooldown.")
			await interaction.response.send_message(f"You can't gamble yet as you are on cooldown. You can gamble silently with hide=True, or wait another {round(time()-cooldowns.get(interaction.user.id, 0))} seconds,", ephemeral=True)
			return
		else:
			cooldowns[interaction.user.id] = int(time())

	if amount <= 0:
		await interaction.response.send_message("The amount must be a positive integer.", ephemeral=True)
		log(f"{interaction.user} tried to gamble {amount}, but it failed because that's not a positive int.")
		return

	cursor.execute(
			'''SELECT SUM(amount) FROM transactions WHERE receiver_id = ?''', (interaction.user.id,)
	)

	user_balance = cursor.fetchone()[0] or 0
	if amount > user_balance:
		await interaction.response.send_message(f"You don't have enough SBCoin to gamble {amount}; you only have {user_balance}", ephemeral=True)
		log(f"{interaction.user} tried to gamble {amount}, but it failed because they only have {user_balance}.")
		return

	if random.random() > 0.49:
		cursor.execute(
			'''INSERT INTO transactions (awarder_id, receiver_id, message_id, amount)
			VALUES (?, ?, ?, ?)''',
			(interaction.user.id, interaction.user.id, interaction.id, -amount)
		)

		conn.commit()

		new_balance = user_balance - amount
		await interaction.response.send_message(f"You gambled {amount} SBCoin and lost! :( Now you only have {new_balance} SBCoin", ephemeral=hide)
		log(f"{interaction.user} gambled {amount} and lost. Their new balance is {new_balance}")
	else:
		cursor.execute(
			'''INSERT INTO transactions (awarder_id, receiver_id, message_id, amount)
			VALUES (?, ?, ?, ?)''',
			(interaction.user.id, interaction.user.id, interaction.id, amount)
		)

		conn.commit()

		new_balance = user_balance + amount
		await interaction.response.send_message(f"You gambled {amount} SBCoin and won! :D Now you have {new_balance} SBCoin.", ephemeral=hide)
		log(f"{interaction.user} gambled {amount} and won! Their new balance is {new_balance}")

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
		await interaction.response.send_message(f"You do not have enough SBCoin to send {amount}. You currently have {sender_balance}.", allowed_mentions=no_mentions, ephemeral=True)
		return

	# Record the transaction
	try:
	    #recipient awards negative amount to user??
		cursor.execute(
			'''INSERT INTO transactions (awarder_id, receiver_id, message_id, amount)
			VALUES (?, ?, ?, ?)''',
			(recipient.id, interaction.user.id, interaction.id, -amount)
		)

		#user awards amount to recipient
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
		log(f"Error processing send command: {e}")


bot.run(oAuth_token)
