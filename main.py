import os
import discord
import google.generativeai as genai
from discord import app_commands  # Import app_commands
from myserver import server_on  # Import the server function


DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)


# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)  # Create the command tree


@client.event
async def on_ready():
    print(f' Logged in as {client.user}')
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@tree.command(name="join", description="ให้บอทเข้าห้อง voice ของคุณ")
async def join(interaction: discord.Interaction):
    voice_state = interaction.user.voice

    if voice_state and voice_state.channel:
        try:
            await interaction.response.send_message(
                f" เข้าห้อง: {voice_state.channel.name}", ephemeral=True)
            await voice_state.channel.connect()
        except Exception as e:
            await interaction.followup.send(f" เข้าห้องไม่สำเร็จ: {str(e)}")
    else:
        await interaction.response.send_message(
            " คุณต้องอยู่ใน voice channel ก่อน", ephemeral=True)


@client.event
async def on_voice_state_update(member, before, after):
    voice_channel = before.channel

    # ตรวจสอบว่า member ออกจากห้องเสียง
    if voice_channel and len(voice_channel.members) == 1:
        bot_member = voice_channel.guild.voice_client

        # ถ้าบอทอยู่ในห้องนั้น และเหลือแค่บอท
        if bot_member and bot_member.is_connected():
            await bot_member.disconnect()
            print(
                f"บอทออกจากห้องเสียง {voice_channel.name} เพราะไม่มีใครอยู่แล้ว"
            )


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!ask"):
        prompt = message.content[len("!ask"):].strip()

        print(f"[📩] รับข้อความจาก {message.author}: {prompt}")

        if not prompt:
            await message.channel.send(" กรุณาพิมพ์ข้อความหลัง `!ask`")
            return

        await message.channel.send(" บอทกำลังคิดคำตอบ...")

        try:
            await message.channel.typing()  # เพื่อให้รู้ว่ากำลังประมวลผล

            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)

            print(f"[✅] ตอบกลับจาก Gemini:\n{response.text}")

            if response.text:
                await message.channel.send(response.text)
            else:
                await message.channel.send(" บอทไม่สามารถสร้างคำตอบได้")

        except Exception as e:
            print(f"[] ERROR: {e}")
            await message.channel.send(f" เกิดข้อผิดพลาด: {str(e)}")
# Start the Flask server in a separate thread
server_on()

client.run(DISCORD_BOT_TOKEN)
