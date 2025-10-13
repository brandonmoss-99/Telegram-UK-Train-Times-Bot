FROM python:3.14.0-slim-bookworm

LABEL org.opencontainers.image.source=https://github.com/brandonmoss-99/Telegram-UK-Train-Times-Bot

RUN apt-get update && apt-get install tini

# Create a working directory. Instruct Docker to use this path as the default
# location for all subsequent commands. Don't have to type full filepaths anymore,
# can use relative paths based on the working directory
WORKDIR /tBot

# Copy requirements.txt file, containing dependencies that pip will need to install
# for the python program to function properly
COPY requirements.txt requirements.txt

# Execute pip3 install of required dependencies
RUN pip3 install -r requirements.txt

COPY ./src ./src

ENTRYPOINT [ "/usr/bin/tini", "--", "python", "src/bot.py" ]
