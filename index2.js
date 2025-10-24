import { Client, GatewayIntentBits } from "discord.js";
import fetch from "node-fetch";
import dotenv from "dotenv";

dotenv.config();

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

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

    const data = await response.json();
    const output =
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      "⚠️ No response from Gemini.";

    // Discord messages have a 2000 character limit
    const chunks = output.match(/[\s\S]{1,1900}/g) || [];
    for (const chunk of chunks) {
      await message.reply(chunk);
    }
  } catch (err) {
    console.error(err);
    message.reply("❌ There was an error talking to Gemini.");
  }
});

client.login(process.env.DISCORD_TOKEN);
