from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import praw
import prawcore
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

reddit = praw.Reddit('SMRedditBot')  # change the ini var
subredditdata = None
submissiondata = []


def help(bot, update):
    message = '/all : access frontpage and fetches the hottest posts\n'\
        '/subreddit <arg> : access the subreddit and fetches the hottest posts\n'

    update.message.reply_text(message)


def reset():
    subredditdata = None
    submissiondata = []


def all(bot, update):
    chatid = update.message.chat_id
    frontpage = reddit.front.hot(limit=5)
    i = 1
    message = "Fresh from r/all\n\n"
    for submission in frontpage:
        if i > 3:
            break
        elif submission.stickied or submission.over_18:
            continue
        else:
            message += 'Title: {}\nUpvotes: {}\nLink: {}\n\n' \
                .format(submission.title, submission.score, submission.shortlink)
            i = i + 1
    bot.send_message(chatid, text=message, disable_web_page_preview=True)

def subreddit(bot, update):
    _, query = update.message.text.split()
    chatid = update.message.chat_id
    subreddit = reddit.subreddit(query)
    try:
        if subreddit.over18:
            bot.send_message(chatid, text='Hey! This subreddit is NSFW!')
        else:
            subredditdata = subreddit.hot(limit=5)
            i = 1
            message = 'Fresh from r/{}\n\n'.format(query)
            for submission in subredditdata:
                if i > 3:
                    break
                elif submission.stickied or submission.over_18:
                    continue
                else:
                    message += 'Title: {}\nUpvotes: {}\nLink: {}\n\n'\
                        .format(submission.title, submission.score, submission.shortlink)
                    i = i + 1
            bot.send_message(chatid, text=message, disable_web_page_preview=True)
    except prawcore.exceptions.Redirect:
        bot.send_message(chatid, text="Subreddit {} does not exist!".format(query))
    except prawcore.exceptions.NotFound:
        bot.send_message(chatid, text="Subreddit {} does not exist!".format(query))


def main():
    updater = Updater(open('.\\TelegramTokenKey.txt').read())
    updater.dispatcher.add_handler(CommandHandler('all', all))
    updater.dispatcher.add_handler(CommandHandler('subreddit', subreddit))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()