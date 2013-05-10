#!/usr/bin/python

import calendar
import email.utils
import time
import urllib2

from BeautifulSoup import BeautifulSoup
import opsecHeader


class Facebook:

    def write_latest_post(self, name, user_id, message, profile_picture, updated_time, keyword, epoch_time):
        sql = "INSERT INTO facebook (name, user_id, message, profile_picture, updated_time, keyword, epoch_time) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        opsecHeader.cur.execute(sql, (name, user_id, message, profile_picture, updated_time, keyword, epoch_time))
        opsecHeader.db.commit()

    def get_latest_post_time(self):
        result = '0'
        opsecHeader.cur.execute("SELECT MAX(epoch_time) FROM `facebook`")
        for row in opsecHeader.cur.fetchall():
            result = row[0]
        return result

    def get_profile_picture(self, user_id):
        profile_picture_string = 'https://graph.facebook.com/' + user_id + '/picture'
        url_result = urllib2.urlopen(profile_picture_string)
        result = url_result.geturl().encode('utf-8')
        url_result.close()
        return result

    def search_facebook(self, raw_keyword):
        opsecHeader.write_last_checked_time('facebook')
        keyword = urllib2.quote(raw_keyword)
        # See https://developers.facebook.com/docs/reference/api/
        #
        # Arguments:
        # q = keyword we are searching for
        # type = kind of object we are searching for e.g post
        #
        # Returns:
        # name; id (facebook.com/id for their profile)

        facebook_latest_epoch = self.get_latest_post_time()
        facebook_query_string = 'https://graph.facebook.com/search?q=' + keyword + '&type=post'
        opsecHeader.query_website_json("facebook", facebook_query_string)

        print "Parsing Facebook data..."

        facebook_results = opsecHeader.read_results_json('facebook')
        facebook_all_results = facebook_results['data']

        if facebook_all_results:
            for i in facebook_all_results:
                if 'message' in i:
                    message = i['message'].encode('utf-8')
                    name = (i['from']['name']).encode('utf-8')
                    user_id = (i['from']['id']).encode('utf-8')
                    updated_time = (i['updated_time']).encode('utf-8')
                    epoch_time = calendar.timegm((time.strptime(updated_time, '%Y-%m-%dT%H:%M:%S+0000')))

                    if int(epoch_time) > int(facebook_latest_epoch):
                        profile_picture = self.get_profile_picture(user_id)
                        self.write_latest_post(name, user_id, message, profile_picture, updated_time, keyword, epoch_time)
                        opsecHeader.send_email(keyword, "Facebook")
                        print "Updated Time: " + updated_time
                    else:
                        print "Post too old."


class Reddit:

    def write_latest_post(self, author, body, link_id, comment_id, link_title, subreddit, epoch_time_found, permalink):
        sql = 'INSERT INTO reddit (author, body, link_id, comment_id, link_title, subreddit, epoch_time, permalink) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        opsecHeader.cur.execute(sql, (author, body, link_id, comment_id, link_title, subreddit, epoch_time_found, permalink))
        opsecHeader.db.commit()

    def get_user(self, index):
        sql = "SELECT author FROM reddit_users"
        opsecHeader.cur.execute(sql)
        results = opsecHeader.cur.fetchall()
        try:
            user = results[index][0]
            return user
        except:
            return None

    def get_latest_user_epoch(self, user):
        sql = "SELECT MAX(epoch_time) FROM reddit WHERE author = %s"
        opsecHeader.cur.execute(sql, (user))
        for row in opsecHeader.cur.fetchall():
            result = row[0]
        if result is None:
            result = 0
        return result

    def get_user_comments(self, user):
        #http://www.reddit.com/dev/api

        user = urllib2.quote(user)

        reddit_query_string = 'http://www.reddit.com/user/' + user + '/overview.json'
        opsecHeader.query_website_json("reddit", reddit_query_string, opsecHeader.reddit_api_key)
        opsecHeader.write_last_checked_time('reddit')

        reddit_results = opsecHeader.read_results_json('reddit')
        try:
            reddit_all_results = reddit_results['data']['children']
        except KeyError:
            reddit_all_results = None
        epoch_time_existing = self.get_latest_user_epoch(user)

        if not reddit_all_results:
            print "No results."
        else:
            for i in reddit_all_results:
                epoch_time_found = str((i['data']['created_utc'])).encode('utf-8')[:-2]
                if int(epoch_time_found) > int(epoch_time_existing):
                    try:
                        link_id = (i['data']['link_id']).encode('utf-8')[3:]
                    except KeyError:
                        link_id = ''
                    comment_id = (i['data']['id']).encode('utf-8')
                    author = (i['data']['author']).encode('utf-8')
                    try:
                        body = (i['data']['body']).encode('utf-8')
                    except KeyError:
                        body = ''
                    try:
                        link_title = (i['data']['link_title']).encode('utf-8')
                    except KeyError:
                        link_title = ''
                    subreddit = (i['data']['subreddit']).encode('utf-8')
                    permalink = 'http://www.reddit.com/r/' + subreddit + '/comments/' + link_id + '/' + urllib2.quote(link_title) + '/' + comment_id
                    self.write_latest_post(author, body, link_id, comment_id, link_title, subreddit, epoch_time_found, permalink)

                    keywords = opsecHeader.get_user_keywords(author, 'reddit')
                    for keyword in keywords:
                        if keyword in body:
                            opsecHeader.send_email(keyword, "Reddit", author)


class StackExchange:

    def __init__(self):
        self.api_key = opsecHeader.stackexchange_api_key

    def write_latest_post(self, account_id, user_id, site, content_type, epoch_time, profile_image, url, content, display_name):
        sql = "INSERT INTO stackexchange (account_id, user_id, site, content_type, epoch_time, profile_image, url, content, display_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        opsecHeader.cur.execute(sql, (account_id, user_id, site, content_type, epoch_time, profile_image, url, content, display_name))
        opsecHeader.db.commit()

    def get_latest_post(self, user_id=None, site=None, content_type=None):
        epoch_time = '0'
        if user_id is None or site is None or content_type is None:
            return epoch_time
        elif user_id is not None and site is not None and content_type is not None:
            sql = "SELECT MAX(epoch_time) FROM `stackexchange` WHERE user_id = %s AND site = %s AND content_type = %s"
            opsecHeader.cur.execute(sql, (user_id, site, content_type))
        for row in opsecHeader.cur.fetchall():
            epoch_time = row[0]
            if(epoch_time < 1):
                epoch_time = '0'
        return epoch_time

    def get_user(self, index):
        sql = "SELECT account_id FROM stackexchange_users"
        opsecHeader.cur.execute(sql)
        results = opsecHeader.cur.fetchall()
        try:
            user = results[index][0]
            return user
        except:
            return None

    def get_user_accounts(self, stackexchange_account):
        print("Getting StackExchange user accounts...")
        associated_query_string = 'http://api.stackexchange.com/2.1/users/' + str(stackexchange_account) + '/associated?key=' + self.api_key
        opsecHeader.query_website_json("StackExchangeUserAccounts", associated_query_string)

        results = opsecHeader.read_results_json('StackExchangeUserAccounts')
        items = results['items']

        # Set default accounts to 1; non-existant accounts
        stackoverflow_user_id = 1
        serverfault_user_id = 1

        for i in items:
            site_name = i['site_name']
            user_id = i['user_id']
            print site_name
            print user_id
            if (site_name == "Stack Overflow"):
                stackoverflow_user_id = user_id
            if (site_name == "Server Fault"):
                serverfault_user_id = user_id
            account_id = i['account_id']
            print i
        self.add_accounts(account_id, stackoverflow_user_id, serverfault_user_id)

    def add_accounts(self, account_id, stackoverflow_user_id, serverfault_user_id):
        sql = "UPDATE stackexchange_users SET stackoverflow_user_id = %s, serverfault_user_id = %s WHERE account_id = %s"
        opsecHeader.cur.execute(sql, (stackoverflow_user_id, serverfault_user_id, account_id))
        opsecHeader.db.commit()

    def write_display_name(self, account_id, display_name):
        sql = "UPDATE stackexchange_users SET display_name = %s WHERE account_id = %s"
        opsecHeader.cur.execute(sql, (display_name, account_id))
        opsecHeader.db.commit()

    def get_post(self, account_id, site, user_id, content_type):
        latest_epoch_time = self.get_latest_post(user_id, site, content_type)
        query_string = 'http://api.stackexchange.com/2.1/users/' + str(user_id) + '/' + str(content_type) + 's?fromdate=' + str(latest_epoch_time) + '&order=desc&sort=creation&site=' + site + '&key=' + self.api_key
        opsecHeader.query_website_json(str(site) + str(user_id) + str(content_type), query_string)
        opsecHeader.write_last_checked_time('stackexchange')

        results = opsecHeader.read_results_json(str(site) + str(user_id) + str(content_type))
        items = results['items']
        for i in items:

            creation_date = i['creation_date']
            if(latest_epoch_time != creation_date):

                if(content_type == 'question'):
                    url = i['link']
                    html = urllib2.urlopen(url).read()
                    soup = BeautifulSoup(html)
                    dirty_content = soup.find('div', {'class': 'post-text', 'itemprop': 'description'})
                    content = ''.join(dirty_content.findAll(text=True))

                elif(content_type == 'answer'):
                    answer_id = i['answer_id']
                    url = "http://" + str(site) + ".com/a/" + str(answer_id)
                    html = urllib2.urlopen(url).read()
                    soup = BeautifulSoup(html)
                    answer_id = 'answer-' + str(answer_id)
                    div_content = soup.find('div', {'id': answer_id})
                    dirty_content = div_content.find('div', {'class': 'post-text'})
                    content = ''.join(dirty_content.findAll(text=True))

                elif(content_type == 'comment'):
                    comment_id = i['comment_id']
                    post_id = i['post_id']
                    short_url = 'http://' + str(site) + '.com/q/' + str(post_id)
                    long_url = str(urllib2.urlopen(short_url).geturl())
                    long_url = long_url.split("#")[0]
                    url = long_url + '#comment' + str(comment_id) + '_' + str(post_id)
                    html = urllib2.urlopen(url).read()
                    soup = BeautifulSoup(html)
                    comment_id_format = 'comment-' + str(comment_id)
                    try:  # Will fail if comments need to be loaded via AJAX
                        comment_tr = soup.find('tr', {'id': comment_id_format})
                        dirty_content = comment_tr.find('span', {'class': 'comment-copy'})
                        content = ''.join(dirty_content.findAll(text=True))
                    except AttributeError:
                        content = 'See website'

                profile_image = i['owner']['profile_image']
                display_name = i['owner']['display_name']

                self.write_display_name(account_id, display_name)
                self.write_latest_post(account_id, user_id, site, content_type, creation_date, profile_image, url, content, display_name)

                keywords = opsecHeader.get_user_keywords(account_id, 'stackexchange')
                for keyword in keywords:
                    if keyword in content:
                        opsecHeader.send_email(keyword, "Stack Exchange", display_name)

    def get_user_posts(self, account_id):
        user_id_sql = "SELECT stackoverflow_user_id, serverfault_user_id FROM stackexchange_users WHERE account_id = %s"
        opsecHeader.cur.execute(user_id_sql, (account_id))
        for row in opsecHeader.cur.fetchall():
            stackoverflow_user_id = row[0]
            serverfault_user_id = row[1]
        if ((stackoverflow_user_id == 0) or (serverfault_user_id == 0)):
            self.get_user_accounts(account_id)

        if (stackoverflow_user_id > 1):
            print("Checking stackoverflow")
            self.get_post(account_id, 'stackoverflow', stackoverflow_user_id, 'question')
            self.get_post(account_id, 'stackoverflow', stackoverflow_user_id, 'answer')
            self.get_post(account_id, 'stackoverflow', stackoverflow_user_id, 'comment')
        else:
            print("Account ID " + str(account_id) + " has no Stack Overflow account")
        if (serverfault_user_id > 1):
            print("Checking serverfault")
            self.get_post(account_id, 'serverfault', serverfault_user_id, 'question')
            self.get_post(account_id, 'serverfault', serverfault_user_id, 'answer')
            self.get_post(account_id, 'serverfault', serverfault_user_id, 'comment')
        else:
            print("Account ID " + str(account_id) + " has no Server Fault account")


class Twitter:

    def __init__(self):
        self.consumer_key = opsecHeader.twitter_consumer_key
        self.consumer_secret = opsecHeader.twitter_consumer_secret
        self.access_token = opsecHeader.twitter_access_token
        self.access_token_secret = opsecHeader.twitter_access_token_secret

    def write_tweet(self, twitter_id, from_user, text, created_at, keyword, location, lat, lng, epoch_time, profile_image_url_https):
        sql = "INSERT INTO twitter (twitter_id, from_user, text, created_at, keyword, location, lat, lng, epoch_time, profile_image_url_https) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        opsecHeader.cur.execute(sql, (twitter_id, from_user, text, created_at, keyword, location, lat, lng, epoch_time, profile_image_url_https))
        opsecHeader.db.commit()

    def get_latest_tweet(self, from_user=None, keyword=None):
        twitter_id, epoch_time = '0', '0'  # Default values
        if from_user is None and keyword is not None:
            sql = "SELECT twitter_id, epoch_time FROM `twitter` WHERE keyword = %s ORDER BY twitter_id desc LIMIT 1"
            opsecHeader.cur.execute(sql, (keyword))
        elif from_user is not None and keyword is None:
            sql = "SELECT twitter_id, epoch_time FROM `twitter` WHERE from_user = %s ORDER BY twitter_id desc LIMIT 1"
            opsecHeader.cur.execute(sql, (from_user))
        else:
            return None, None
        for row in opsecHeader.cur.fetchall():
            twitter_id = row[0]
            epoch_time = row[1]
        return twitter_id, epoch_time

    def get_user(self, index):
        sql = "SELECT user FROM twitter_users"
        opsecHeader.cur.execute(sql)
        results = opsecHeader.cur.fetchall()
        try:
            user = results[index][0]
            return user
        except:
            return None

    def gen_geo(self, from_user):
        geo_query_string = 'https://api.twitter.com/1.1/users/show.json?screen_name=' + from_user
        opsecHeader.query_website_oauth_json("twitterGeo", geo_query_string, self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret)
        results = opsecHeader.read_results_json('twitterGeo')
        location = (results['location']).encode('utf-8')
        if not location:
            return 'null', '0.0000000', '0.0000000'
        else:
            google_query_string = 'http://maps.googleapis.com/maps/api/geocode/json?&address=' + urllib2.quote(location) + '&sensor=false'
            opsecHeader.query_website_json("googleGeoCode", google_query_string)
            google_results = opsecHeader.read_results_json('googleGeoCode')
            google_all_results = google_results['results']
            if not google_all_results:
                return location, '0.0000000', '0.0000000'
            else:
                for i in google_all_results:
                    lat = (i['geometry']['location']['lat'])
                    lng = (i['geometry']['location']['lng'])
                    return location, lat, lng

    def get_user_tweets(self, user):
        screen_name = urllib2.quote(user)
        opsecHeader.write_last_checked_time('twitter')

        # See https://dev.twitter.com/docs/api/1/get/statuses/user_timeline
        tweet_since_date = str(self.get_latest_tweet(screen_name, None)[0])
        epoch_time_existing = self.get_latest_tweet(screen_name, None)[1]

        twitter_query_string = 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=' + screen_name + '&count=10'

        if tweet_since_date != '0':  # Twitter does not play nice with invalid since_id's
            twitter_query_string += '&since_id=' + tweet_since_date

        opsecHeader.query_website_oauth_json("twitterUserTweets", twitter_query_string, self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret)

        twitter_results = opsecHeader.read_results_json('twitterUserTweets')
        if twitter_results is not None:
            twitter_all_results = twitter_results
        else:
            twitter_all_results = None

        if not twitter_all_results:
            print "No results."
        else:
            for i in twitter_all_results:
                created_at = (i['created_at']).encode('utf-8')
                epoch_time_found = calendar.timegm((email.utils.parsedate(created_at)))
                if int(epoch_time_found) > int(epoch_time_existing):
                    twitter_id = (i['id'])
                    text = (i['text']).encode('utf-8')
                    from_user = (i['user']['screen_name']).encode('utf-8')
                    created_at = (i['created_at']).encode('utf-8')
                    profile_image_url_https = (i['user']['profile_image_url_https']).encode('utf-8')

                    try:
                        location = '?'
                        lat = i['geo']['coordinates'][0]
                        lng = i['geo']['coordinates'][1]
                        print("Got coordinates!")
                    except:
                        location, lat, lng = self.gen_geo(from_user)

                    self.write_tweet(twitter_id, from_user, text, created_at, '', location, lat, lng, epoch_time_found, profile_image_url_https)
                    keywords = opsecHeader.get_user_keywords(from_user, 'twitter')
                    for keyword in keywords:
                        if keyword in text:
                            opsecHeader.send_email(keyword, "Twitter", from_user)

    def search_twitter(self, raw_keyword):
        keyword = urllib2.quote(raw_keyword)
        opsecHeader.write_last_checked_time('twitter')

        # See https://dev.twitter.com/docs/api/1.1/get/search/tweets
        tweet_since_date = str(self.get_latest_tweet(None, keyword)[0])
        search_query_string = 'https://api.twitter.com/1.1/search/tweets.json?q=' + keyword + '&count=10&result_type=recent'

        if tweet_since_date != '0':  # Twitter does not play nice with invalid since_id's
            search_query_string += '&since_id=' + tweet_since_date

        opsecHeader.query_website_oauth_json("twitter", search_query_string, self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret)

        twitter_results = opsecHeader.read_results_json('twitter')
        twitter_all_results = twitter_results['statuses']

        if not twitter_all_results:
            print "No results."
        else:
            existing_epoch_time = self.get_latest_tweet(None, keyword)[1]

            for i in twitter_all_results:
                created_at = (i['created_at']).encode('utf-8')
                epoch_time_found = calendar.timegm((time.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')))
                if int(epoch_time_found) > int(existing_epoch_time):
                    twitter_id = (i['id'])
                    from_user = (i['user']['screen_name']).encode('utf-8')
                    text = (i['text']).encode('utf-8')
                    created_at = (i['created_at']).encode('utf-8')
                    profile_image_url_https = (i['user']['profile_image_url_https']).encode('utf-8')
                    location, lat, lng = self.gen_geo(from_user)

                    self.write_tweet(twitter_id, from_user, text, created_at, keyword, location, lat, lng, epoch_time_found, profile_image_url_https)
                    opsecHeader.send_email(keyword, "Twitter")


class Wordpress:

    def write_latest_wordpress(self, epoch_time, title, author, content, link, keyword):
        sql = "INSERT INTO wordpress (epoch_time, title, author, content, link, keyword) VALUES (%s, %s, %s, %s, %s, %s)"
        opsecHeader.cur.execute(sql, (epoch_time, title, author, content, link, keyword))
        opsecHeader.db.commit()

    def get_latest_wordpress(self):
        result = '0'
        opsecHeader.cur.execute("SELECT epoch_time FROM `wordpress` ORDER BY epoch_time desc LIMIT 1")
        for row in opsecHeader.cur.fetchall():
            result = row[0]
        return result

    def search_wordpress(self, raw_keyword):
        keyword = urllib2.quote(raw_keyword)
        opsecHeader.write_last_checked_time('wordpress')

        ############### WORDPRESS ##################
        #
        # See http://en.search.wordpress.com/?q=obama&s=date&f=json
        #
        # Arguments:
        # q = keyword to search for
        # s = sort by; we want date; not relevance
        # f = format; we want JSON

        wordpress_query_string = 'http://en.search.wordpress.com/?q=' + keyword + '&s=date&f=json'

        opsecHeader.query_website_json("wordpress", wordpress_query_string)

        wordpress_latest_epoch = self.get_latest_wordpress()
        wordpress_results = opsecHeader.read_results_json('wordpress')
        epoch_time = wordpress_results[0]['epoch_time']

        if str(wordpress_latest_epoch) == str(epoch_time):
            print "No new blog posts since last query."
        else:
            for i in wordpress_results:
                epoch_time = i['epoch_time']
                if int(wordpress_latest_epoch) < int(epoch_time):
                    title = (i['title']).encode('utf-8')
                    author = (i['author']).encode('utf-8')
                    content = (i['content']).encode('utf-8')
                    link = (i['link']).encode('utf-8')
                    self.write_latest_wordpress(epoch_time, title, author, content, link, keyword)
                    opsecHeader.send_email(keyword, "Wordpress")
