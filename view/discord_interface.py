# ============================================================
# discord_interface.py - Duarte Grilo 2201320 - Projeto Informático
# ============================================================
# Objetivo:
# 🔹 Integrar o chatbot com o Discord _através de um _bot_
# 🔹 Responder a mensagens que comecem por um prefixo (!)
# 🔹 Utiliza asyncio e threading para chamadas ao controlador
# 🔹 Divide mensagens longas em vários envios
# 🔹 Usa reações (_emoji_) para estado
# 🔹 Usa commands._Bot_ para fácil expansão de comandos
# 🔹 Guarda _logs a ficheiro para auditoria
# 🔹 Usa o _token_ do _bot_ a partir do ficheiro .env
# ============================================================

import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from controllers.chatbot_controller import process_user_input

# Logger simples para auditoria
logging.basicConfig(
    filename='discord_bot.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

COMMAND_PREFIX = "!"
MAX_DISCORD_LENGTH = 1900  # margem para não rebentar limite de 2000 chars

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    logging.info(f'Bot iniciado como {bot.user}')


def dividir_mensagem(texto, max_length=MAX_DISCORD_LENGTH):
    """Divide texto longo em partes menores para o Discord."""
    partes = []
    while len(texto) > max_length:
        corte = texto.rfind('\n', 0, max_length)
        corte = corte if corte != -1 else max_length
        partes.append(texto[:corte])
        texto = texto[corte:]
    partes.append(texto)
    return partes


@bot.command(name="ajuda")
async def ajuda(ctx):
    """Mostra instruções de uso do _bot_."""
    msg = (
        "🤖 **Chatbot IA Velvet-2B**\n"
        f"Envia perguntas começando por `{COMMAND_PREFIX}` para obter resposta.\n"
        f"Exemplo: `{COMMAND_PREFIX}Qual a capital de Portugal?`\n"
        f"Comandos disponíveis:\n"
        f" - `{COMMAND_PREFIX}ajuda` — mostra esta mensagem\n"
        f"\nSe a resposta for longa, será enviada em várias mensagens."
    )
    await ctx.send(msg)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith(COMMAND_PREFIX):
        try:
            await message.add_reaction("👀")
        except Exception:
            pass

        conteudo = message.content[len(COMMAND_PREFIX):].strip()
        logging.info(f"Recebido de {message.author}: {conteudo}")

        # ✅ Se for comando especial: !ajuda
        if conteudo.lower() == "ajuda":
            await bot.process_commands(message)
            return

        status_msg = await message.channel.send("🤖 A pensar...")

        try:
            await status_msg.add_reaction("🤖")
        except Exception:
            pass

        try:
            resposta = await asyncio.to_thread(process_user_input, conteudo)
            if isinstance(resposta, dict):
                texto = resposta.get("resposta_pt") or resposta.get("resposta") or str(resposta)
            else:
                texto = resposta

            partes = dividir_mensagem(str(texto))
            for idx, parte in enumerate(partes):
                prefixo = f"📌 Resposta (Parte {idx+1}/{len(partes)}):\n" if len(partes) > 1 else "📌 Resposta:\n"
                await message.channel.send(prefixo + parte)

            logging.info(f"Respondido para {message.author}: {texto[:200]}...")

        except Exception as e:
            await message.channel.send("❌ Erro ao processar a pergunta.")
            try:
                await status_msg.add_reaction("❌")
            except Exception:
                pass
            logging.error(f"Erro ao processar de {message.author}: {e}")

        try:
            await status_msg.clear_reactions()
        except Exception:
            pass

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
