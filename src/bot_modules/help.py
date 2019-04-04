import inspect
import logging
import config
import util
from hook import Hook

logger = logging.getLogger(__name__)

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    Hook.get("public!help").attach(help_message)
    Hook.get("public!about").attach(about_message)
    Hook.get("public!report").attach(report)


async def help_message(message, args):
    """
    Gives help with commands.
    `help` gives a list of all the commands you can use.
    `help <command>` gives information about how to use a command, if you can use it.
    """
    command_list = [c[c.find("!")+1:] for c in Hook.list() if (
                        (c.startswith("public!") and util.check_command_permissions(message, "public")) or
                        (c.startswith("admin!") and util.check_command_permissions(message, "admin")) or
                        (c.startswith("owner!") and util.check_command_permissions(message, "owner"))
                    )]
    if args.strip() == "":
        # no command provided
        help_msg = "Available commands: *" + ", ".join(command_list) + \
                   "*\nUse `help <command>` for help with a specific command."
    elif args.strip().lower() in command_list:
        # help for a specific command, command_list already filters commands the user can use
        cmd = args.strip().lower()
        command_methods = []
        command_methods.extend(Hook.get("public!" + cmd).methods())
        command_methods.extend(Hook.get("admin!" + cmd).methods())
        help_msg = "**" + config.get_response_token(message.server) + cmd + "**" + "\n"
        help_msg += ("\n"+"\u2E3B"*16+"\n").join(inspect.getdoc(method) for method in command_methods if inspect.getdoc(method) != "")
    else:
        # unknown command
        help_msg = "I don't know what you mean! Use `help` for help."

    await client.send_message(message.channel, help_msg)


async def about_message(message, args):
    """
    Gives information about Notte (that's me!).
    """
    msg = "Hi, I'm Notte! " + util.get_emote("notte_smile") + " I'm a bot made by Struct to help out with everything Dragalia Lost.\n" \
          "You can find my source code here: <https://gitlab.com/VStruct/notte>\n" \
          "Special thanks to AlphaDK for all of his help and feedback!\n" \
          "If you find a bug, want a feature, or have something else to say, you can use `" + \
          config.get_response_token(message.server) + "report`, and I'll let " + \
          config.get_global_config()["owner_name"] + " know."

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
                      ("" if (channel.is_private or author.nick is None) else " ({0})".format(author.nick))
        location = "a direct message" if channel.is_private else ("#{0} ({1})".format(channel.name, message.server.name))

        await client.send_message(client.get_channel(config.get_global_config()["report_channel"]),
                                  "{0} in {1} reports:\n{2}".format(author_name, location, args))
    except Exception:
        await client.send_message(client.get_channel(config.get_global_config()["report_channel"]), "Report generated exception: " + args)
        raise
    finally:
        await client.send_message(message.channel, "Thanks for the report! I've let " + config.get_global_config()["owner_name"] + " know.")


Hook.get("on_init").attach(on_init)
