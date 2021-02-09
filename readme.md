# telegram-railTime-bot

A telegram bot script written in Python for fetching and displaying UK train times and station notice boards

## Dependencies
 - [Python 3.8+](https://www.python.org/downloads/) - May work with earlier versions, but I haven't tested it on older than Python 3.8.5

See requirements.txt for additional dependencies

## Usage

To run the script, call it, passing in your Telegram bot token and National Rail API token:

```bash
$ python3 bot.py [OPTIONS]...
```

See also `python3 bot.py --help`.

### Options

Required:

`-t` or `--bottoken`: Telegram Bot token to use for connection to the API.

`-r` or `--railtoken`: National Rail token to use for connection to the API.

Optional:

`-n` or `--next`: Max number of trains to fetch per update [1-10]

`--help`: Display help

## Compatibility
I've been running this bot successfully on MacOS 10.14.6, and Ubuntu 20.04.1 LTS. I haven't tested its functionality on Windows
