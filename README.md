# ProgPhil Bot

![status](https://github.com/ProgrammingPhilippines/progphil-bot/actions/workflows/main.yml/badge.svg)
![status](https://github.com/ProgrammingPhilippines/progphil-bot/actions/workflows/docker-ci.yml/badge.svg)
[![License: MIT](https://img.shields.io/github/license/ProgrammingPhilippines/progphil-bot)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/discord/748554476398444635?style=plastic)](https://discord.gg/MmWwgXQezf)

### Built with
[![python](https://img.shields.io/badge/python-python-green)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-discord.py-blue)](https://discordpy.readthedocs.io/en/stable/)

# Getting Started	

Follow these instructions to set up the bot on your Discord server.

### Prerequisites

Required tools/programs used for development:

- python 3.8 or later (check your version with ``python --version``)
- poetry (install with ``pip3 install poetry`` or by using the [official installer](https://python-poetry.org/docs/#installing-with-the-official-installer)).

### Installation

1. Create a new Discord application on the [Discord Developer Portal](https://discord.com/developers/applications) and set the required permissions for the bot.
2. Grab the secret token for the bot from the "Bot" tab of your Discord application.
3. After setting up your bot in the discord portal it's time to clone the repository.
```
git clone https://github.com/ProgrammingPhilippines/progphil-bot
```
4. After you clone the repository, go to the project and install the dependencies using the command below:
```
cd progphil-bot

poetry install
```
5. Create a .env file and make sure to add all necessary envrinment variables, see `.env.example` file
6. If you haven't encounter any conflict or errors when intalling dependencies, then the bot is now ready; run the bot using the command below:
```
poetry run progphil
```
Congrats! If you want to contribute to this project read the [Development](/#Development) section.

### Development
Read the [Development Guide](https://github.com/ProgrammingPhilippines/progphil-bot/wiki/Development-Guide) for an in-depth look at the development process and guidelines for contributing to the ProgPhil Bot project.

# Contributing

Want to contribute to the project? Check out the [available issues](https://github.com/ProgrammingPhilippines/progphil-bot/issues) and start coding!

1. Fork the repository.
2. Create your feature branch.
3. Commit your changes `git commit -m "you amazing commit"`.
4. Push the branch `git push -u origin your-feature-branch`.
5. Open a pull request.

Make sure to familiarize yourself with the project's development guidelines before making any contributions. The [Development Guide](https://github.com/ProgrammingPhilippines/progphil-bot/wiki/Development-Guide) provides an in-depth look at the development process and guidelines for contributing to the ProgPhil Bot project. This includes information on the project's code of conduct, testing procedures, and best practices for submitting pull requests. By reading and understanding the Development Guide, you can ensure that your contributions align with the project's goals and standards.

# Community

- Kanban board [here](https://github.com/orgs/ProgrammingPhilippines/projects/2/views/1)
- Discussions at [our Discord server](https://discord.gg/MmWwgXQezf)
  - Reach out to the admins to get access to the progphil-bot channel

### License

[MIT](https://choosealicense.com/licenses/mit/)
