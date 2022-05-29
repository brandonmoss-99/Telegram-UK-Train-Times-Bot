# syntax=docker/dockerfile:1

# Inherit the Python 3 docker image
FROM python:3

# Create a working directory. Instruct Docker to use this path as the default
# location for all subsequent commands. Don't have to type full filepaths anymore,
# can use relative paths based on the working directory
WORKDIR /tBot

# Copy requirements.txt file, containing dependencies that pip will need to install
# for the python program to function properly
COPY requirements.txt requirements.txt

# Execute pip3 install of required dependencies
RUN pip3 install -r requirements.txt

# Add all source code into the image (. . = current directory to workspace directory)
#COPY . .

# Tell docker to run command
CMD exec python -u src/bot.py -t <TELEGRAM_TOKEN> -r <RAIL_TOKEN> >> output.log
