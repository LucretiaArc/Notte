import inspect
import logging
import config
import util
import discord
import hook

logger = logging.getLogger(__name__)

client = None


async def on_init(discord_client):
    global client
    client = discord_client

    hook.Hook.get("public!help").attach(help_message)
    hook.Hook.get("public!about").attach(about_message)
    hook.Hook.get("public!report").attach(report)


async def help_message(message, args):
    """
    Gives help with commands.
    `help` gives a list of all the commands you can use.
    `help <command>` gives information about how to use a command, if you can use it.
    """
    command_list = [c[c.find("!")+1:] for c in hook.Hook.list() if (
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
        command_methods.extend(hook.Hook.get("public!" + cmd).methods())
        command_methods.extend(hook.Hook.get("admin!" + cmd).methods())
        help_msg = "**" + config.get_prefix(message.guild) + cmd + "**" + "\n"
        help_msg += ("\n"+"\u2E3B"*16+"\n").join(inspect.getdoc(method) for method in command_methods if inspect.getdoc(method) != "")
    else:
        # unknown command
        help_msg = "I don't know what you mean! Use `help` for help."

    await message.channel.send(help_msg)


async def about_message(message, args):
    """
    Gives information about Notte (that's me!).
    """
    msg = "Hi, I'm Notte! " + util.get_emote("notte_smile") + " I'm a bot made by Struct to help out with everything Dragalia Lost.\n" \
          "You can find my source code here: <https://gitlab.com/VStruct/notte>\n" \
          "Special thanks to AlphaDK for all of his help and feedback!\n" \
          "If you find a bug, want a feature, or have something else to say, you can use `" + \
          config.get_prefix(message.guild) + "report`, and I'll let " + \
          config.get_global_config()["owner_name"] + " know."

    await message.channel.send(msg)


async def report(message, args):
    """
    If you find a bug, have a feature request, or some other feedback, use `report <message>`.
    """

    if len(args.strip()) == 0:
        await message.channel.send("I need something to report! Type a message after the command.")
        return

    try:
        author = message.author
        channel = message.channel

        author_name = "{0}#{1}".format(author.name, author.discriminator) + \
                      ("" if (isinstance(channel, discord.abc.PrivateChannel) or author.nick is None) else " ({0})".format(author.nick))
        location = "a direct message" if isinstance(channel, discord.abc.PrivateChannel) else ("#{0} ({1}), {2}".format(channel.name, channel.id, message.guild.name))

        await client.get_channel(config.get_global_config()["report_channel"]).send(
                                  "{0} in {1} reports:\n{2}".format(author_name, location, args))
    except Exception:
        await client.get_channel(config.get_global_config()["report_channel"]).send("This report generated an exception: " + args)
        raise
    finally:
        await message.channel.send("Thanks for the report! I've let " + config.get_global_config()["owner_name"] + " know.")


hook.Hook.get("on_init").attach(on_init)
