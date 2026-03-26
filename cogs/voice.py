import discord
from discord.ext import commands
import edge_tts
import asyncio
import os
import tempfile
from langdetect import detect

# Import the debater module to access shared state (TARGET_USER_IDS, BOT_ENABLED)
import cogs.debater as debater


class Voice(commands.Cog):
    """Voice chat cog — auto-joins VC when a target joins, speaks AI comebacks."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_client: discord.VoiceClient | None = None
        self.tts_voice = "en-US-GuyNeural"  # Natural male voice (free via Edge-TTS)
        self._speaking = False

    # ── TTS helpers ──────────────────────────

    def get_voice_for_text(self, text: str) -> str:
        """Detect language of text and map to an appropriate Edge-TTS voice."""
        try:
            lang_code = detect(text)
        except:
            lang_code = "en"  # fallback
            
        print(f"[Voice] Detected language code: '{lang_code}'")
        
        # Maps langdetect 2-letter codes to Edge-TTS neural voices
        voice_map = {
            "en": self.tts_voice, # use the manually set one
            "es": "es-ES-AlvaroNeural",
            "fr": "fr-FR-HenriNeural",
            "de": "de-DE-KilianNeural",
            "it": "it-IT-DiegoNeural",
            "pt": "pt-BR-AntonioNeural",
            "ru": "ru-RU-DmitryNeural",
            "ja": "ja-JP-KeitaNeural",
            "ko": "ko-KR-InJoonNeural",
            "zh-cn": "zh-CN-YunxiNeural",
            "zh-tw": "zh-TW-HsiaoChenNeural",
            "ar": "ar-AE-HamdanNeural",
            "hi": "hi-IN-MadhurNeural",
            "nl": "nl-NL-MaartenNeural",
            "sv": "sv-SE-MattiasNeural",
            "tr": "tr-TR-AhmetNeural",
            "vi": "vi-VN-HoaiMyNeural",  # Vietnamese
        }
        
        # If not mapped, fall back to whatever is set
        return voice_map.get(lang_code, self.tts_voice)

    async def generate_tts(self, text: str) -> str:
        """Generate TTS audio file from text using Edge-TTS. Returns temp file path."""
        tmp_path = os.path.join(tempfile.gettempdir(), "debate_tts.mp3")
        voice_to_use = self.get_voice_for_text(text)
        print(f"[Voice] Generating TTS with voice: '{voice_to_use}'")
        communicate = edge_tts.Communicate(text, voice_to_use)
        await communicate.save(tmp_path)
        return tmp_path

    async def speak(self, text: str):
        """Speak text in the currently connected voice channel."""
        if not self.voice_client or not self.voice_client.is_connected():
            return
        if self._speaking:
            return  # Don't interrupt current speech

        self._speaking = True
        try:
            audio_path = await self.generate_tts(text)
            source = discord.FFmpegPCMAudio(audio_path)
            self.voice_client.play(
                source,
                after=lambda e: self._on_done(e),
            )
            # Wait for playback to finish
            while self.voice_client and self.voice_client.is_playing():
                await asyncio.sleep(0.3)
        except Exception as e:
            print(f"[Voice] TTS error: {e}")
        finally:
            self._speaking = False

    def _on_done(self, error):
        if error:
            print(f"[Voice] Playback error: {error}")

    # ── Auto-join on target VC join ──────────

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """Auto-join VC when a targeted user joins a voice channel."""
        print(f"[Voice] Voice state update: {member.display_name} (ID: {member.id})")
        print(f"[Voice] Targets: {debater.TARGET_USER_IDS}, BOT_ENABLED: {debater.BOT_ENABLED}")

        if not debater.BOT_ENABLED:
            print("[Voice] Bot disabled, skipping")
            return

        # Only care about targeted users
        if member.id not in debater.TARGET_USER_IDS:
            print(f"[Voice] {member.display_name} not in target list, skipping")
            return

        # Target joined or switched to a new channel
        if after.channel is not None and (before.channel is None or before.channel != after.channel):
            target_channel = after.channel

            # Already in that channel
            if self.voice_client and self.voice_client.channel == target_channel:
                return

            # Disconnect from old channel first
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.disconnect()

            try:
                self.voice_client = await target_channel.connect()
                print(f"[Voice] Auto-joined '{target_channel.name}' to stalk {member.display_name}")
            except Exception as e:
                print(f"[Voice] Failed to join: {e}")

        # Target left VC entirely — leave too
        elif after.channel is None and before.channel is not None:
            if self.voice_client and self.voice_client.is_connected():
                # Check if any other targets are still in the channel
                remaining_targets = [
                    m for m in before.channel.members
                    if m.id in debater.TARGET_USER_IDS and m.id != member.id
                ]
                if not remaining_targets:
                    await self.voice_client.disconnect()
                    self.voice_client = None
                    print(f"[Voice] Target {member.display_name} left VC — disconnecting")

    # ── Manual commands ──────────────────────

    @commands.command(name="join")
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def join_vc(self, ctx: commands.Context):
        """Join your current voice channel. Usage: !join"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("you're not in a voice channel lol")
            return

        channel = ctx.author.voice.channel
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()

        await ctx.send(f"joined **{channel.name}** 🎤")

    @commands.command(name="leave")
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def leave_vc(self, ctx: commands.Context):
        """Leave the voice channel. Usage: !leave"""
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send("left the vc")
        else:
            await ctx.send("i'm not in a voice channel")

    @commands.command(name="setvoice")
    @commands.check_any(commands.is_owner(), commands.has_permissions(manage_guild=True))
    async def set_voice(self, ctx: commands.Context, *, voice: str = None):
        """
        Change the TTS voice. Usage: !setvoice en-US-GuyNeural
        Common voices: en-US-GuyNeural, en-US-JennyNeural, en-GB-RyanNeural
        """
        if not voice:
            await ctx.send(
                f"current voice: `{self.tts_voice}`\n"
                f"try: `en-US-GuyNeural`, `en-US-JennyNeural`, `en-GB-RyanNeural`, `en-AU-WilliamNeural`"
            )
            return
        self.tts_voice = voice
        await ctx.send(f"voice changed to `{voice}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(Voice(bot))
