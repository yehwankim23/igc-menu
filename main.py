import datetime
import time

import bs4
import requests
import tweepy

API_KEY = ""
API_KEY_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""

CLIENT = tweepy.Client(consumer_key=API_KEY, consumer_secret=API_KEY_SECRET,
                       access_token=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET)

URL = "https://housing.igc.or.kr/about/cafeteria_menu.do"


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
    li_list = find_all(menu, "li")

    return li_list


def get_menu(list_wrap):
    title = find(list_wrap, "div", "title")
    name = find(title, "div", "name")
    cell = find(name, "div", "cell")
    menu = cell.string.strip()

    return menu


def get_text(list_wrap):
    text = ""

    title = find(list_wrap, "div", "title")
    time_ = find(title, "div", "time")
    cell = find(time_, "div", "cell")
    dl_list = find_all(cell, "dl")

    dd = find(dl_list[0], "dd")
    text += dd.string.strip() + "\n"

    dd = find(dl_list[1], "dd")
    text += "₩ " + dd.contents[1].strip() + "\n\n"

    con = find(list_wrap, "div", "con")
    list_ = find(con, "div", "list clearFix bar_none")
    dl_list = find_all(list_, "dl")

    for dl in dl_list:
        dt = find(dl, "dt")
        dd = find(dl, "dd")
        text += "• " + dt.string.strip() + " / " + dd.string.strip() + "\n"

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

    response = CLIENT.create_tweet(text=real_text, in_reply_to_tweet_id=tweet_id)
    tweet_id = response.data["id"]

    return tweet_id


def tweet_menu(dinner):
    sub_cont = get_sub_cont()
    date = get_date(sub_cont)
    li_list = get_li_list(sub_cont)

    tweet_id = None

    for li in li_list:
        list_wrap = find(li, "div", "list_wrap")
        menu = get_menu(list_wrap)

        if (menu != "Dinner") is dinner:
            continue

        text = date + "\n" + menu + "\n" + get_text(list_wrap)
        tweet_id = send_tweet(text, tweet_id)


def main():
    tweet = True
    tweet_error = True

    while True:
        # noinspection PyBroadException
        try:
            time.sleep(30)
            now = datetime.datetime.now()

            if now.minute != 0:
                continue

            hour = now.hour

            if hour == 11:
                if not tweet:
                    continue

                tweet = False
                tweet_menu(False)
            elif hour == 17:
                if not tweet:
                    continue

                tweet = False
                tweet_menu(True)
            else:
                tweet = True
                continue

            tweet_error = True
        except Exception:
            if tweet_error:
                tweet_error = False
                CLIENT.create_tweet(text="An error occurred. Please fix me :(")


if __name__ == "__main__":
    main()
