#!/usr/bin/python

import datetime

import opsecHeader
import twitter
import reddit
import stackexchange
import facebook
import wordpress


def main():
    minute = datetime.datetime.now().minute
    five_min_interval = (int(minute) / 5) - 1
    one_digit_minute = int(str(minute)[-1])

    print("################################")
    print("#### OPSEC Search Bootstrap ####")
    print("################################")

    print("----- User Specific Search -----")
    print("Attempting site/user specific search")

    # Twitter
    try:
        user = twitter.get_users()[one_digit_minute]
        twitter.get_user_tweets(user)
    except IndexError:
        print("No Twitter user found at index " + str(one_digit_minute))

    # Reddit
    try:
        author = reddit.get_users()[one_digit_minute]
        reddit.get_user_comments(author)
    except IndexError:
        print("No Reddit user found at index " + str(one_digit_minute))

    # StackExchange
    try:
        account_id = stackexchange.get_users()[one_digit_minute]
        stackexchange.get_user_posts(account_id)
    except IndexError:
        print("No StackExchange user found at index " + str(one_digit_minute))


    print("-------- General search --------")
    if (minute % 5) == 0:
        print("Attempting general site search...")
        try:
            keyword = opsecHeader.get_user_keywords('all',
                                                'twitter')[five_min_interval]
            twitter.search_twitter(keyword)
        except IndexError:
            print("No twitter keyword at index " + str(five_min_interval))

        try:
            keyword = opsecHeader.get_user_keywords('all',
                                                'facebook')[five_min_interval]
            facebook.search_facebook(keyword)
        except IndexError:
            print("No facebook keyword at index " + str(five_min_interval))

        try:
            keyword = opsecHeader.get_user_keywords('all',
                                                'wordpress')[five_min_interval]
            wordpress.search_wordpress(keyword)
        except IndexError:
            print("No wordpress keyword at index " + str(five_min_interval))

    else:
        print("Minute not a multiple of 5, not attempting general site search...")

if __name__ == "__main__":
    main()
