import datetime
import sys
import time
import traceback

import bs4
import requests
import telegram
import telegram.ext
import tweepy

CHAT_ID = int("")
TOKEN = ""
PASSWORD = ""

API_KEY = ""
API_KEY_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""

BOT = telegram.Bot(TOKEN)

pong = True
run_program = True

CLIENT = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_KEY_SECRET,
                       access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET)

URL = "https://housing.igc.or.kr/about/cafeteria_menu.do"


def send_message(text, chat_id=CHAT_ID):
    BOT.send_message(chat_id, text)


def send_error_message():
    global pong

    stack_traces = traceback.format_exc().splitlines()
    message = stack_traces[1].strip() + "()\n\n" + stack_traces[2].strip() + "\n\n"

    if len(stack_traces) > 4:
        message += stack_traces[3].strip() + "()\n\n" + stack_traces[4].strip() + "\n\n"

    send_message(message + stack_traces[-1])
    pong = True


def ping(update, _):
    global pong

    # noinspection PyBroadException
    try:
        if update.effective_chat.id == CHAT_ID:
            pong = True
    except Exception:
        send_error_message()


def pause(update, context):
    global run_program

    # noinspection PyBroadException
    try:
        if update.effective_chat.id != CHAT_ID:
            return

        # noinspection PyBroadException
        try:
            password = context.args[0]
        except Exception:
            send_message("Syntax: /pause [password]")
            return

        if password != PASSWORD:
            send_message("Incorrect password")
            return

        run_program = False
        send_message("Program paused")
    except Exception:
        send_error_message()


def resume(update, context):
    global run_program

    # noinspection PyBroadException
    try:
        if update.effective_chat.id != CHAT_ID:
            return

        # noinspection PyBroadException
        try:
            password = context.args[0]
        except Exception:
            send_message("Syntax: /resume [password]")
            return

        if password != PASSWORD:
            send_message("Incorrect password")
            return

        run_program = True
        send_message("Program resumed")
    except Exception:
        send_error_message()


def find(tag, name, class_=None, id_=None):
    if class_ is None:
        if id_ is None:
            return tag.find(name, recursive=False)

        return tag.find(name, id=id_, recursive=False)

    return tag.find(name, class_=class_, recursive=False)


def find_all(tag, name, class_=None):
    if class_ is None:
        return tag.find_all(name, recursive=False)

    return tag.find_all(name, class_=class_, recursive=False)


def get_sub_cont():
    soup = bs4.BeautifulSoup(requests.get(URL).text, "html.parser")
    container = find(soup.body, "div", "container sub_bg")
    sub_contents = find(container, "div", "sub_contents")
    inner = find(sub_contents, "div", "inner")
    sub_cont = find(inner, "div", "sub_cont cafeteria")

    return sub_cont


def get_date(sub_cont):
    change_week = find(sub_cont, "div", "change_week")
    week = find(change_week, "div", "week")
    first_day = find(week, "span", "first_day")
    date = first_day.string.strip()

    return date


def get_li_list(sub_cont):
    menu = find(sub_cont, "ul", "menu clearFix")

    if menu is None:
        return None

    li_list = find_all(menu, "li")

    return li_list


def get_menu_time(list_wrap):
    title = find(list_wrap, "div", "title")
    time_ = find(title, "div", "time")
    cell = find(time_, "div", "cell")
    dl = find(cell, "dl")
    dd = find(dl, "dd")
    menu_time = dd.string.strip()

    return menu_time


def get_text(list_wrap):
    text = ""

    title = find(list_wrap, "div", "title")

    name = find(title, "div", "name")
    cell = find(name, "div", "cell")
    text += cell.string.strip() + "\n\n"

    con = find(list_wrap, "div", "con")
    list_ = find(con, "div", "list clearFix bar_none")
    dl_list = find_all(list_, "dl")

    for dl in dl_list:
        dd = find(dl, "dd")
        dt = find(dl, "dt")
        text += "• " + dd.string.strip() + " " + dt.string.strip() + "\n"

    return text


def send_tweet(text, tweet_id=None):
    lines = text.strip().splitlines()
    count = 0
    real_text = ""

    for line in lines:
        line_count = 1

        for character in line:
            if character.isascii():
                line_count += 1
            else:
                line_count += 2

        count += line_count

        if count > 280:
            response = CLIENT.create_tweet(text=real_text, in_reply_to_tweet_id=tweet_id)

            count = line_count
            real_text = ""
            tweet_id = response.data["id"]

        real_text += line + "\n"

    if real_text != "":
        response = CLIENT.create_tweet(text=real_text, in_reply_to_tweet_id=tweet_id)
        tweet_id = response.data["id"]

    return tweet_id


def tweet_menu(minutes):
    sub_cont = get_sub_cont()
    date = get_date(sub_cont)
    li_list = get_li_list(sub_cont)

    if li_list is None:
        return

    tweet_id = None

    for li in li_list:
        list_wrap = find(li, "div", "list_wrap")
        menu_time = get_menu_time(list_wrap).split("~")[0].split(":")

        if 0 < (int(menu_time[0]) * 60 + int(menu_time[1])) - minutes < 60:
            text = date + " " + get_text(list_wrap)
            tweet_id = send_tweet(text, tweet_id)


def main():
    global run_program, pong

    # noinspection PyBroadException
    try:
        tweet = True
        check_running = True

        updater = telegram.ext.Updater(TOKEN)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(telegram.ext.CommandHandler("ping", ping))
        dispatcher.add_handler(telegram.ext.CommandHandler("pause", pause))
        dispatcher.add_handler(telegram.ext.CommandHandler("resume", resume))

        updater.start_polling()
        send_message("Program started")
    except Exception:
        send_error_message()
        send_message("Program stopped")
        sys.exit(-1)

    while True:
        # noinspection PyBroadException
        try:
            time.sleep(3)

            if not run_program:
                continue

            now = datetime.datetime.now()
            hour = now.hour
            minute = now.minute

            if minute % 30 == 0:
                if tweet:
                    tweet = False
                    tweet_menu(hour * 60 + minute)
            else:
                tweet = True

            if hour in [9, 15, 21]:
                if check_running:
                    check_running = False
                    send_message("Program running")
            else:
                check_running = True

            if pong:
                pong = False
                send_message("Pong")
        except Exception:
            send_error_message()


if __name__ == "__main__":
    main()
