
<h1 align="center">
  <br>
  <img src="./stuff/img.png" width="200">
  <br>
  Different Sounds, Random Radio Discord BOT
  <br>
</h1>

## About The Project

Just listen music that your algorithm not choose

## Commands

- .help: Displays all available commands
- .join: This command makes the bot access the voice channel
- .stop: This command makes the bot end the radio session
- .start: This command makes the bot start the radio session
- .new: This command makes the bot pass to new song
- .iwant: This command makes the bot play music based on a specific request
- .shuffle: This command makes the bot returns to play music random again 

## Quick Start

Follow the next steps

```bash
# Clone this repository
$ git clone https://github.com/raulgalis/differentsounds

# Go into the repository and install the requirements.txt
$ cd differentsounds
$ pip install -r requirements.txt

# Add your private API key for Discogs Account and Discord Aplication
load_dotenv()
API_KEY = os.getenv('discogs')
token = os.getenv('discord')

# Run main.py
$ python main.py
```