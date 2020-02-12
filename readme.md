# Notte
A Discord bot that provides information about Dragalia Lost, a mobile game developed by Cygames and published by Nintendo.

## Prerequisites
* Python 3.7
* Discord bot user

## Installing

Perform all of the following steps in the environment you will be using to run the bot.

1. Download all required packages using pip

    ```
    pip install -r requirements.txt
    ```
    
2. Create an environment variable `DISCORD_CLIENT_TOKEN` containing your discord bot user's client token

3. Run main.py
    
    ```
    python3 ./src/main.py
    ```
## Directory Structure

| Directory | Content |
| --- | --- |
| /src | Application code |
| /config | Static bot configuration files. |
| /assets | Assets used by the bot for functionality. |
| /data | Contains all data written by the bot to disk, except for log files. Automatically generated at runtime. |
| /data/config | Dynamic bot configuration files. |
| /data/icons | Icons automatically downloaded for use in the summoning simulator module. |
| /extras | Extras which aren't important for functionality (e.g. the bot's avatar). |