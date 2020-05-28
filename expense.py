class ExpenseBot:
    ''' This object eases markdown and display of welcome message
    '''

    WELCOME_BLOCK = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "Hello Haroun!  Welcome to expenseBot, your friendly expense manager- how may I be of service? :grin:\n\n"
                "*Please see options below:*"
            ),
        },
    }

    DIVIDER_BLOCK = {"type": "divider"}

    OPTIONS_BLOCK = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    " *Choose from the following options* :arrow_down:\n"
                    "*Add* :heavy_plus_sign: : Add an expense to your list\n"
                    "*Remove* :heavy_minus_sign: : Remove an expense from your list \n"
                    "*View* :eyes: : View your current itemized expenses \n"
                    "*Total* :heavy_check_mark: : Display the current expense total owed\n"
                    "*Clear* :cl: : Clear all expenses \n"
                ),
            },
        }


    def __init__(self, channel):
        self.channel = channel
        self.username = "expenseBot"
        self.timestamp = ''
        self.icon_emoji = ":moneybag:"

    def get_welcomeMessage_payload(self):
        return {
                "ts": self.timestamp,
                "channel": self.channel,
                "username": self.username,
                "icon_emoji": self.icon_emoji,
                "blocks": [
                    self.WELCOME_BLOCK,
                    self.DIVIDER_BLOCK,
                    self.OPTIONS_BLOCK,
                ],
            }
