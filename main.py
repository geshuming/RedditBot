from telegram.ext import Updater, CommandHandler
import praw
import prawcore
import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

reddit = praw.Reddit('Bot')  # change the ini var
TOKEN='token' # telegram api key
PORT = os.environ.get('PORT')
NAME = "bot"

def help(bot, update):
    message = '/all : access frontpage and fetches the hottest posts\n'\
        '/subreddit <subreddit> : access the subreddit and fetches the hottest posts\n'\
        '/fetch <subreddit> : fetches a fresh unseen post from the subreddit <subreddit>\n'\
        '/reset <subreddit> : resets already seen posts'

    update.message.reply_text(message)

def help(bot, update):
    message = 'Hello! I am RedditBot! Whatcha planning to do today?\n\n'\
        '/(r, get, fetch) <subreddit> : fetches a post from <subreddit>\n'\
        '/reset <subreddit> : resets already seen posts in <subreddit>\n'

    update.message.reply_text(message)


def fetchfreshpost(bot, update):
    _, *query = update.message.text.split()
    if not query or query[0] == 'all':
        sendfreshpost(bot, update, reddit.front)
    else:
        check = checksubreddit(query[0])
        if check > 0:
            errorhandler(bot, update, check)
        else:
            sendfreshpost(bot,update, reddit.subreddit(query[0]))


def sendfreshpost(bot, update, sr):
    srlist = sr.hot(limit=15)
    sent = False
    for submission in srlist:
        if submission.stickied or submission.over_18 or submission.hidden:
            continue
        else:
            submission.hide()
            if submission.url.endswith(('.jpg', '.png')):
                # reddit-hosted images / imgur-hosted images
                update.message.reply_photo(photo=submission.url,
                                           caption='Title: {}'.format(submission.title),
                                           quote=True)
                sent = True
                break
            elif 'gyfcat' in submission.url:
                # gyfcat-hosted gifs
                update.message.reply_video(video=submission.url + '.mp4',
                                           caption='Title: {}'.format(submission.title),
                                           quote=True)
                sent = True
                break
            elif submission.url.endswith(('.gif', '.gifv')):
                # imgur-hosted gifs
                update.message.reply_video(video=submission.url[0:submission.url.find('.gif')] + '.mp4',
                                           caption='Title: {}'.format(submission.title),
                                           quote=True)
                sent = True
                break
            else:
                # any other media
                update.message.reply_text(text='Title: {}\nURL: {}\n'
                                          .format(submission.title, submission.url), quote=True)
                sent = True
                break
    if not sent:
        update.message.reply_text(text='Sorry, we seem to have ran out of fresh content')


def errorhandler(bot, update, error=0):
    if error == 1:
        update.message.reply_text("Sorry, the subreddit is NSFW!", quote=True)
    elif error == 2:
        update.message.reply_text("Sorry, the subreddit does not exist!", quote=True)
    else:
        update.message.reply_text("Unknown error", quote=True)


def checksubreddit(sub):
    try:
        sr = reddit.subreddit(sub)
        if sr.over18:
            return 1
        elif sr.subscribers < 1000:
            return 2
        else:
            return 0
    except prawcore.exceptions.Redirect or prawcore.exceptions.NotFound:
        return 2


def reset(bot, update):
    _, *query = update.message.text.split()
    if not query or query[0] == 'all':
        srlist = reddit.front.hot(limit=15)
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


def main():
    updater = Updater(TOKEN)
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_handler(CommandHandler(['r', 'fetch', 'get'], fetchfreshpost))
    updater.dispatcher.add_handler(CommandHandler('reset', reset))
    updater.bot.set_webhook("https://" + NAME + ".herokuapp.com/" + TOKEN)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
