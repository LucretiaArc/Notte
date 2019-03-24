import discord
import inspect
import logging
from hook import Hook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = None
config = None


async def on_init(discord_client, module_config):
    global client, config
    client = discord_client
    config = module_config

    Hook.get("public!help").attach(help_message)
    Hook.get("public!about").attach(about_message)
    Hook.get("public!report").attach(report)


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


async def about_message(message, args):
    """
    Gives information about Notte (that's me!).
    """
    msg = "Hi, I'm Notte! I'm a bot made by Struct to help out with everything Dragalia Lost.\n" \
          "Special thanks to AlphaDK for all of his help and feedback!\n" \
          "If you find a bug, want a feature, or have something else to say, you can use `" + \
          config["token"] + "report`, and I'll let " + config["owner_name"] + " know."

    await client.send_message(message.channel, msg)


async def report(message, args):
    """
    If you find a bug, have a feature request, or some other feedback, use `report <message>`.
    """

    if len(args.strip()) == 0:
        await client.send_message(message.channel, "I need something to report! Type a message after the command.")
        return

    try:
        author = message.author
        channel = message.channel

        author_name = "{0}#{1}".format(author.name, author.discriminator) + \
                      (" ({0})".format(author.nick) if author.nick is not None else "")
        location = "DMs" if channel.is_private else ("#{0} ({1})".format(channel.name, message.server.name))

        await client.send_message(discord.Object(config["report_channel"]),
                                  "{0} in {1} reports:\n{2}".format(author_name, location, args))
    except Exception:
        await client.send_message(discord.Object(config["report_channel"]), "Report generated exception: " + args)
        raise
    finally:
        await client.send_message(message.channel, "Thanks for the report! I've let " + config["owner_name"] + " know.")


Hook.get("on_init").attach(on_init)
