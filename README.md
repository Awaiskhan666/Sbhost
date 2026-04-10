# LTC Flash Discord Selfbot

A Discord selfbot for sending Litecoin "flash" messages and engaging in aggressive interactions with other users.

## Features

- Send flash messages with LTC amount to all accessible channels
- Send flash messages to a specific channel
- Check LTC address balances
- "Drown" users with English and Hindi insults (auto-replies when they send messages)
- Engage in "debate" with users using abusive intellectual comebacks in Hinglish
- Auto-reply to both drowned and debate users when they send messages
- Track inactivity and taunt users who don't respond 
- Stop drowning or debating specific users
- "Annoy" users in voice channels by automatically muting, deafening, and disconnecting them
- Monitor for rejoins and repeat annoy actions automatically
- Animate images using Viggle AI with different animation effects
- Run 24/7 with keep-alive functionality
- Secure token handling
- Basic validation for Litecoin addresses

## Commands

- `-flash <amount> <ltc_address>` - Send flash messages with LTC amount to all accessible channels
- `-flashchannel <amount> <ltc_address>` - Send flash message to specific channel only
- `-bal <ltc_address>` - Check the balance of a Litecoin address
- `-drown @user-mention` - Insult a mentioned user in English and Hindi with abusive insults
- `-drown english @user-mention` - Insult a mentioned user in English only
- `-drown hindi @user-mention` - Insult a mentioned user in Hindi only
- `-drownenglish @user-mention` - Alternative way to insult in English only
- `-drownhindi @user-mention` - Alternative way to insult in Hindi only
- `-debate @user-mention` - Engage in a savage intellectual debate with someone in Hinglish
- `-debatehinglish @user-mention` - Alternative way to engage in a savage intellectual debate in Hinglish
- `-stop @user-mention` - Stop drowning a specific user
- `-stopd @user-mention` - Stop debating a specific user
- `-meme [animation_type]` - Animate an attached image using Viggle AI (requires API key)
- `-ping` - Check if the bot is responding
- `-helpme` - Show the help message

## 24/7 Operation

This bot is configured to run 24/7 using a keep-alive mechanism. The keep_alive.py file creates a small web server that can be pinged regularly to prevent the Replit instance from sleeping. For maximum uptime, you can use an external service like UptimeRobot to ping the webserver URL every few minutes.

## Security Notes

- The Discord token is stored securely in environment variables
- The bot never displays the full token, only the first 5 characters for verification
- **IMPORTANT**: Using selfbots (running a bot on a user account) is against Discord's Terms of Service. Use at your own risk.

## Setup

1. Make sure your Discord token is set as an environment variable named `TOKEN`
2. Run the bot with `python main.py`
3. The web interface can be accessed separately via the Flask application

## Requirements

- discord.py-self
- flask (for keep-alive web server)
- pillow (for image processing)
- requests (for API interactions)

## Optional Configuration

- For Viggle AI image animation: Set the `VIGGLE_API_KEY` environment variable with your Viggle API key