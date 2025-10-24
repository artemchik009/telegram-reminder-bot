// index.js
import { Client, GatewayIntentBits } from "discord.js";
import fetch from "node-fetch";

// ⚠️ Put your keys here (KEEP PRIVATE)
const DISCORD_TOKEN = "MTQzMDkzNjI1MTQ5MzUxNTQ0NQ.GXH2Hc.fg9ZtOEeSOQ_JllNsgM855HQKyM4Irq4874OtM";
const GEMINI_API_KEY = "AIzaSyCe2lO3I7IiyMuLJXMTVYQAcuhJsd5NusI";

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

client.once("ready", () => {
  console.log(`✅ Logged in as ${client.user.tag}`);
});

client.on("messageCreate", async (message) => {
  if (message.author.bot) return;
  if (!message.content.startsWith("!ask")) return;

  const prompt = message.content.slice(4).trim();
  if (!prompt) return message.reply("Please provide a question after `!ask`.");

  await message.channel.send("💭 Thinking...");

  try {
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${GEMINI_API_KEY}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
        }),
      }
    );

    const text = await response.text();

    // Handle non-JSON responses gracefully
    if (text.startsWith("<!DOCTYPE")) {
      console.error("❌ HTML response received — check your Gemini API key or URL");
      return message.reply("❌ Gemini returned an HTML error page — check your API key.");
    }

    const data = JSON.parse(text);
    const output =
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      "⚠️ No valid response from Gemini.";

    // Discord messages have a 2000-character limit
    const chunks = output.match(/[\s\S]{1,1900}/g) || [];
    for (const chunk of chunks) {
      await message.reply(chunk);
    }
  } catch (err) {
    console.error("Gemini API error:", err);
    message.reply("❌ There was an error talking to Gemini.");
  }
});

client.login(DISCORD_TOKEN);
