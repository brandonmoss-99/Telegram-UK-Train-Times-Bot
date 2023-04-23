# telegram-railTime-bot

## What does this do?
This is a bot for the Telegram messaging service, with the purpose of fetching and displaying UK train times and station notice boards. It is intended to be run within a containerised solution.

## Configuration
### Environment variables
The following environment variables are used by the bot, and should be passed into the container's environment when run:
#### Required:
  - `T_TOKEN` - The Telegram Bot API token to use. Should be a String, `"12345:AAAABBBBCCCCDDDD"`
  - `RAIL_TOKEN` - The National Rail OpenLDBWS API token to use. Should be a String

#### Optional:
  - `NEXT_TRAINS_COUNT` - The max number of trains to fetch per update. Must be between 1 and 10. Defaults to 5.
  - `CACHE_TIME` - The time in seconds to cache responses from the National Rail OpenLDBWS API. Defaults to 30.

