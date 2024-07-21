# ARIS.dev
import disnake

from botbase import BotBase
import google.generativeai as Gemini
from disnake import AppCommandInter, Option, OptionType, OptionChoice, File
from disnake.ext import commands


class ChatBot(commands.Cog):
	def __init__(self, bot: BotBase):
		self.bot: BotBase = bot

		Gemini.configure(api_key=self.bot.env.get("GEMINI_KEY"))


	async def get_gemini_response(self, content: str):
		model = Gemini.GenerativeModel("gemini-1.5-flash")
		chat = model.start_chat(history=[])
		responseContent = await chat.send_message_async(content)
		return responseContent.text


	@commands.cooldown(1, 30, commands.BucketType.user)
	@commands.slash_command(
		name="chat",
		description="Chat với một mô hình AI",
		options=[
			Option(
				name="content",
				description="Nội dung của bạn",
				type=OptionType.string,
				max_length=1000,
				required=True
			),
			Option(
				name="model",
				description="Mô hình chatbot bạn muốn sử dụng",
				type=OptionType.string,
				required=False,
				min_length=4,
				max_length=10,
				choices=[
					OptionChoice(name="Gemini", value="gemini")
				]
			)
		]
	)
	async def chat(self, inter: AppCommandInter, content: str = None, model: str = "gemini"):
		await inter.response.defer()
		if len(content) > 1000:
			await inter.edit_original_response(embed=disnake.Embed(
				title="❌ Độ dài nội dung quá lớn",
				color=0xFF0000
			))
			return

		if model == "gemini":
			response = await self.get_gemini_response(content)
		else:
			await inter.edit_original_response(embed=disnake.Embed(
				title="⚠️ Hiện tại chưa hỗ trợ mô hình này",
				color=0xFFFF00
			))
			return

		if len(response) <= 1750:
			message = f"> ### Trả lời cho {inter.author.mention}\n\n"
			message += response + "\n\n"
			message += f"-# Được cung cấp bởi mô hình {model}. Nội dung được cung cấp có thể không chính xác"
			await inter.edit_original_response(message, embed=None)

		else:
			await inter.edit_original_response(
				file=File(
					fp=bytearray(response, "utf-8"),
					filename="response.txt"
				)
			)

