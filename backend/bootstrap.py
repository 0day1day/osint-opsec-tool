#!/usr/bin/python

import datetime


import opsecHeader
from opsecHeader import Color
from sources import Twitter, Reddit, StackExchange, Facebook, Wordpress


def main():
    current_minute = datetime.datetime.now().minute
    five_min_interval = (int(current_minute) / 5) - 1
    one_digit_minute = int(str(current_minute)[-1])

    print(Color.YELLOW + "####################################################################################")
    print('''   ___  __   _____    __  _____     ___  ___  __    __  ___   _____  ___  ___  __  
  /___\/ _\  \_   \/\ \ \/__   \   /___\/ _ \/ _\  /__\/ __\ /__   \/___\/___\/ /  
 //  //\ \    / /\/  \/ /  / /\/  //  // /_)/\ \  /_\ / /      / /\//  ///  // /   
/ \_// _\ \/\/ /_/ /\  /  / /    / \_// ___/ _\ \//__/ /___   / / / \_// \_// /___ 
\___/  \__/\____/\_\ \/   \/     \___/\/     \__/\__/\____/   \/  \___/\___/\____/ 
                                                                                   ''')
    print("                     OSINT OPSEC Tool " + opsecHeader.version + " - By @hyprwired")
    print("####################################################################################" + Color.ENDC)

    print(Color.HEADER + "[*] User Specific Search" + Color.ENDC)
    print("[-] Attempting site/user specific search...")
    print("[-] Trying user #" + str(one_digit_minute) + "...")

    # Twitter
    twitter = Twitter()
    user = twitter.get_user(one_digit_minute)
    if user is not None:    
        twitter.get_user_tweets(user)
    else:
        print("[-] No Twitter user #" + str(one_digit_minute))

    # Reddit
    reddit = Reddit()
    author = reddit.get_user(one_digit_minute)
    if author is not None:
        reddit.get_user_comments(author)
    else:
        print("[-] No Reddit user #" + str(one_digit_minute))

    # StackExchange
    stack_exchange = StackExchange()
    account_id = stack_exchange.get_user(one_digit_minute)
    if account_id is not None:    
        stack_exchange.get_user_posts(account_id)
    else:
        print("[-] No StackExchange user #" + str(one_digit_minute))


    print(Color.HEADER + "[*] General Search" + Color.ENDC)
    if (current_minute % 5) == 0:
        print("[-] Attempting general site search...")
        try:
            twitter_keyword = opsecHeader.get_user_keywords('all','twitter')[five_min_interval]
            twitter.search_twitter(twitter_keyword)
        except IndexError:
            print("[-] No twitter keyword at index #: " + str(five_min_interval))
       
        try:
            facebook_keyword = opsecHeader.get_user_keywords('all','facebook')[five_min_interval]
            facebook = Facebook()
            facebook.search_facebook(facebook_keyword)
        except IndexError:
            print("[-] No Facebook keyword at index #: " + str(five_min_interval))

        try:
            wordpress_keyword = opsecHeader.get_user_keywords('all','wordpress')[five_min_interval]
            wordpress = Wordpress()
            wordpress.search_wordpress(wordpress_keyword)
        except IndexError:
            print("[-] No Wordpress keyword at index #: " + str(five_min_interval))
    else:
        print("[-] Minute not a multiple of 5, not attempting general site search to avoid throttling...")

if __name__ == "__main__":
    main()
