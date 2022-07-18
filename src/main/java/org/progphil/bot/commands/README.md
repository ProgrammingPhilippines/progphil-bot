<div align="center">
    Commands via Nexus 🌃
</div>

#

### How to make a command?

Nexus is a class-based Javacord framework wherein each commands have to be encapsulated into their command containing 
the command's data such as its name, description and options. You can also include middlewares, afterwares, servers and 
other related data even localization. You can refer to the links below for more information about how to make one.
- For simple commands, please refer to PingCommand.
- For advanced or more complex commands, please refer to [Nexus' README](https://github.com/ShindouMihou/Nexus/).

### Including a command to the bot.

After you have created your command, you can then have it automatically registered to Discord by including it on the `CommandRepository` 
class which can be found on the `org.progphil.bot.repositories` package which contains a repository of all the commands that are to be 
pushed to Discord's database.

All the commands will be automatically pushed during startup through a batch update, so any commands not included in that list will be 
removed and any commands included will be updated or included in the slash commands of the bot.