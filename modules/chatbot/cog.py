# ARIS.dev
from botbase import BotBase
import google.generativeai as Gemini
import os
import aiohttp
from disnake import AppCommandInter, Option, OptionType, OptionChoice, Embed, Color, File
from disnake.ext import commands
from random import randint
from utils.conv import fix_characters
model_info = {
    "chatGPT": {"name": "ChatGPT"},
    "gemini": {"name": "Gemini Ai"},
}


def gen_error_embed(message: str):
        embed = Embed(
            title="❌ Đã xảy ra lỗi",
            description=message,
            color=Color.red()
        )
        return embed




class ChatBot(commands.Cog):
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot

        Gemini.configure(
            api_key=self.bot.env.get("GEMINI_KEY"))  # Get apikey at `https://aistudio.google.com/app/apikey`

        self.OpenAI_APIKEY = self.bot.env.get("CHATGPT_KEY")

    async def get_gemini_response(self, content: str):
        model = Gemini.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat(history=[])
        responseContent = await chat.send_message_async(content)
        return responseContent.text

    async def get_GPT_response(self, user_content: str):
        async with aiohttp.ClientSession() as session:
            history = []
            if user_content:
                history.append(user_content)
            base_url = "http://api.chisadin.site:81/api/chatGPT"

            data = {
                "chat_content": user_content
            }
            response = await session.post(url=base_url, data=data)

            prettyResponse = await response.text()

            if response.status == 200:
                return prettyResponse
            else:
                print(f"Đã xảy ra sự cố: {response.status}, {prettyResponse}")
                FIXresponse = await self.get_gemini_response(user_content)
                return FIXresponse


    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.slash_command(name="chat", description="AI chatbot", options = [
            Option(name="content", description="User Content", type=OptionType.string, required=True),
            Option(name="model", description="Model chatbot", type=OptionType.string, required=True, choices=[
                OptionChoice(name="GPT", value="chatGPT"),
                OptionChoice(name="Gemini", value="gemini")
            ]),
            Option(name="private", description="Private mode)", type=OptionType.boolean, required=False, choices=[
                OptionChoice(name="Bật", value=True),
                OptionChoice(name="Tắt", value=False)
            ])
        ])
    async def aichat(self, ctx: AppCommandInter, content: str = None, model: str = "gemini", private: bool = False):

        await ctx.response.defer(ephemeral=private)
        if len(content) > 2000:
            await ctx.edit_original_response(
                embed=gen_error_embed(message="The question is too long, try to split it up"))
            return

        limitContent = fix_characters(content, 16)
        chatID = randint(0, 9999999)
        response = ""

        embed = Embed(
                title="📝 Processing content, please wait ⌛",
                color=Color.yellow()
            )
        await ctx.edit_original_response(embed=embed)

        if model == "gemini":
            response += await self.get_gemini_response(content)
        elif model == "chatGPT":
            response += await self.get_GPT_response(content)

        if len(response) <= 1750:
            message = f"> ### Answer for {ctx.author.mention}, question `{limitContent}`:\n\n" + response + f"\n\n-# Powered by {model_info[model]['name']}. Information given might not correct and not been verified"
            
            await ctx.edit_original_response(message, embed=None)

        else:
            
            message = "The answer is too long, I'll put it in the file"
            with open(f"response_{chatID}.txt", "w", encoding="utf-8") as f:
                f.write(response)
                f.close()
            await ctx.edit_original_response(message, embed=None, file=File(f"response_{chatID}.txt"))

            os.remove(f"response_{chatID}.txt")


def setup(bot: BotBase):
    bot.add_cog(ChatBot(bot))
