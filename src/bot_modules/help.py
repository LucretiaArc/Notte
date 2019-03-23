import inspect
from hook import Hook

client = None
config = None


async def on_init(discord_client, module_config):
    global client, config
    client = discord_client
    config = module_config

    Hook.get("public!help").attach(help_message)


async def help_message(message, args):
    """
    Gives help with commands.
    `help` gives a list of all the commands you can use.
    `help <command>` gives information about how to use a command.
    """
    command_list = [c[7:] for c in Hook.list() if c.startswith("public!")]
    if args.strip() == "":
        # no command provided
        help_msg = "Available commands: *" + ", ".join(command_list) + \
                   "*\nUse `help <command>` for help with a specific command."
    elif args.strip().lower() in command_list:
        # help for a specific command
        cmd = args.strip().lower()
        help_msg = "**" + config["token"] + cmd + "**" + "\n"
        help_msg += ("\n"+"\u2E3B"*16+"\n").join(
            inspect.getdoc(method) for method in Hook.get("public!" + cmd).methods() if inspect.getdoc(method) != ""
        )
    else:
        # unknown command
        help_msg = "I don't know what you mean! Use `help` for help."

    await client.send_message(message.channel, help_msg)


Hook.get("on_init").attach(on_init)
