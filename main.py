from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import praw
import prawcore
import logging
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

reddit = praw.Reddit('SMRedditBot')  # change the ini var
subredditdata = None
submissiondata = []


def help(bot, update):
    message = '/all : access frontpage and fetches the hottest posts\n'\
        '/subreddit <subreddit> : access the subreddit and fetches the hottest posts\n'\
        '/fetch <subreddit> : fetches a fresh unseen post from the subreddit <subreddit>\n'\
        '/reset <subreddit> : resets already seen posts'

    update.message.reply_text(message)

# deprecated
def reset():
    subredditdata = None
    submissiondata = []


def viewmedia(bot, chat_id, submission):
    if submission.url.endswith(('.jpg','.png')):
        bot.send_photo(chat_id, submission.url, caption='Title: {}'.format(submission.title))
    else:
        bot.send_message(chat_id, text='Title: {}\nURL: {}\n'
                         .format(submission.title, submission.shortlink),
                         disable_web_page_preview=True)


def view(bot, update):
    chatid = update.message.chat_id
    _, query = update.message.text.split()
    try:
        number = int(query) - 1
        if number < 0 or number >= len(submissiondata):
            bot.send_message(chatid, text='Invalid post number!', disable_web_page_preview=True)
        elif submissiondata:
            submission = submissiondata[number]
            viewmedia(bot, chatid, submission)
        else:
            bot.send_message(chatid, text='Pick a subreddit first', disable_web_page_preview=True)
    except Exception as e:
        print(e)
        bot.send_message(chatid, text='Invalid post number!', disable_web_page_preview=True)


def all(bot, update):
    chatid = update.message.chat_id
    frontpage = reddit.front.hot(limit=5)
    i = 1
    message = 'Fresh from r/all\n\n'
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


def getsubreddit(bot, update):
    _, query = update.message.text.split()
    chatid = update.message.chat_id
    try:
        subreddit = reddit.subreddit(query)
        if subreddit.over18:
            bot.send_message(chatid, text='Hey! This subreddit is NSFW!')
        else:
            reset()
            subredditdata = subreddit.hot(limit=5)
            i = 1
            message = 'Fresh from r/{}\n\n'.format(query)
            for submission in subredditdata:
                if i > 3:
                    break
                elif submission.stickied or submission.over_18:
                    continue
                else:
                    submissiondata.append(submission)
                    message += 'Title: {}\nUpvotes: {}\nLink: {}\n\n'\
                        .format(submission.title, submission.score, submission.shortlink)
                    i = i + 1
            bot.send_message(chatid, text=message, disable_web_page_preview=True)
    except prawcore.exceptions.Redirect:
        bot.send_message(chatid, text="Subreddit {} does not exist!".format(query))
    except prawcore.exceptions.NotFound:
        bot.send_message(chatid, text="Subreddit {} does not exist!".format(query))


def resetposts(bot, update):
    _, *query = update.message.text.split()
    if not query or query[0] == 'all':
        srlist = reddit.front.hot(limit=10)
        for submission in srlist:
            if submission.hidden:
                submission.unhide()
        bot.send_message(update.message.chat_id, text='All done!')
    else:
        try:
            srlist = reddit.subreddit(query[0]).hot(limit=10)
            for submission in srlist:
                if submission.hidden:
                    submission.unhide()
            bot.send_message(update.message.chat_id, text='All done!')
        except prawcore.exceptions.Redirect or prawcore.exceptions.NotFound:
            bot.send_message(update.message.chat_id, text="The subreddit /r/{} does not exist!".format(query[0]))


def sendfreshpost(bot, update, sr):
    srlist = sr.hot(limit=10)
    sent = False
    for submission in srlist:
        if submission.stickied or submission.over_18 or submission.hidden:
            continue
        else:
            submission.hide()
            viewmedia(bot, update.message.chat_id, submission)
            sent = True
            break
    if not sent:
        bot.send_message(update.message.chat_id, text='Sorry, we seem to have ran out of fresh content')


def fetchfresh(bot, update):
    _, *query = update.message.text.split()
    if not query or query[0] == 'all':
        sendfreshpost(bot, update, reddit.front)
    else:
        try:
            sr = reddit.subreddit(query[0])
            if sr.over18:
                bot.send_message(update.message.chat_id, text="Sorry, the subreddit /r/{} is NSFW".format(query[0]))
            elif sr.subscribers < 1000:
                bot.send_message(update.message.chat_id, text="The subreddit /r/{} does not exist!".format(query[0]))
            else:
                sendfreshpost(bot, update, sr)
        except prawcore.exceptions.Redirect or prawcore.exceptions.NotFound:
            bot.send_message(update.message.chat_id, text="The subreddit /r/{} does not exist!".format(query[0]))


def main():
    updater = Updater(open('.\\TelegramTokenKey.txt').read())
    updater.dispatcher.add_handler(CommandHandler('all', all))
    updater.dispatcher.add_handler(CommandHandler('subreddit', getsubreddit))
    updater.dispatcher.add_handler(CommandHandler('fetch', fetchfresh))
    updater.dispatcher.add_handler(CommandHandler('reset', resetposts))
    updater.dispatcher.add_handler(CommandHandler('view', view))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
