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
    access_levels = ["public", "admin", "owner"]
    commands = {}
    for level in access_levels:
        commands[level] = sorted(c[c.find("!")+1:] for c in hook.Hook.list() if c.startswith(level+"!"))

    if args.strip() == "":
        # no command provided
        help_msg = "**Available Commands**\n"
        for level in access_levels:
            if util.check_command_permissions(message, level):
                help_msg += "{0} Commands\n\t*{1}*\n".format(level.title(), ", ".join(sorted(commands[level])))
        help_msg += "\nUse `help <command>` for help with a specific command."
    else:
        # help for a specific command
        command = args.strip().lower()
        command_methods = []
        for level in access_levels:
            if util.check_command_permissions(message, level):
                if args.strip().lower() in commands[level]:
                    command_methods.extend(hook.Hook.get("{0}!{1}".format(level, command)).methods())

        if len(command_methods) == 0:
            # unknown command
            help_msg = "I don't know what you mean! Use `help` for help."
        else:
            # known command
            help_sections = list(filter(None, map(inspect.getdoc, command_methods)))
            if help_sections:
                # help available
                separator = "\n" + "\u2E3B" * 16 + "\n"
                help_msg = "**" + config.get_prefix(message.guild) + command + "**" + "\n"
                help_msg += separator.join(help_sections)
            else:
                # no help available
                help_msg = "No help is available for that command."

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
