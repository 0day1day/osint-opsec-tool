#!/usr/bin/python

import calendar
import email.utils
import time
import urllib2

import opsecHeader


def write_tweet(twitter_id, from_user, text, created_at, keyword, location, lat, lng, epoch_time, profile_image_url_https):
    sql = "INSERT INTO twitter (twitter_id, from_user, text, created_at, keyword, location, lat, lng, epoch_time, profile_image_url_https) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    opsecHeader.cur.execute(sql, (twitter_id, from_user, text, created_at, keyword, location, lat, lng, epoch_time, profile_image_url_https))
    opsecHeader.db.commit()


def get_latest_tweet(from_user=None, keyword=None):
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


def get_users():
    users = []
    sql = "SELECT user FROM twitter_users"
    opsecHeader.cur.execute(sql)
    for row in opsecHeader.cur.fetchall():
        users.append(row[0])
    return users


def gen_geo(from_user):
    geo_query_string = 'https://api.twitter.com/1.1/users/show.json?screen_name=' + from_user

    opsecHeader.query_website_oauth_json("twitterGeo", geo_query_string, opsecHeader.twitter_consumer_key, opsecHeader.twitter_consumer_secret, opsecHeader.twitter_access_token, opsecHeader.twitter_access_token_secret)

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


def get_user_tweets(user):
    screen_name = urllib2.quote(user)
    opsecHeader.write_last_checked_time('twitter')

    # See https://dev.twitter.com/docs/api/1/get/statuses/user_timeline
    tweet_since_date = str(get_latest_tweet(screen_name, None)[0])
    epoch_time_existing = get_latest_tweet(screen_name, None)[1]

    twitter_query_string = 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=' + screen_name + '&count=10'

    if tweet_since_date != '0':  # Twitter does not play nice with invalid since_id's
        twitter_query_string += '&since_id=' + tweet_since_date

    opsecHeader.query_website_oauth_json("twitterUserTweets", twitter_query_string, opsecHeader.twitter_consumer_key, opsecHeader.twitter_consumer_secret, opsecHeader.twitter_access_token, opsecHeader.twitter_access_token_secret)

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
                location, lat, lng = gen_geo(from_user)

                write_tweet(twitter_id, from_user, text, created_at, '', location, lat, lng, epoch_time_found, profile_image_url_https)
                keywords = opsecHeader.get_user_keywords(from_user, 'twitter')
                for keyword in keywords:
                    if keyword in text:
                        opsecHeader.send_email(keyword, "Twitter", from_user)


def search_twitter(raw_keyword):
    keyword = urllib2.quote(raw_keyword)
    opsecHeader.write_last_checked_time('twitter')

    # See https://dev.twitter.com/docs/api/1/get/search
    tweet_since_date = str(get_latest_tweet(None, keyword)[0])
    search_query_string = 'http://search.twitter.com/search.json?q=' + keyword + '&rpp=10&result_type=recent'

    if tweet_since_date != '0':  # Twitter does not play nice with invalid since_id's
        search_query_string += '&since_id=' + tweet_since_date

    opsecHeader.query_website_json("twitter", search_query_string)

    twitter_results = opsecHeader.read_results_json('twitter')
    twitter_all_results = twitter_results['results']

    if not twitter_all_results:
        print "No results."
    else:
        existing_epoch_time = get_latest_tweet(None, keyword)[1]

        for i in twitter_all_results:
            created_at = (i['created_at']).encode('utf-8')
            epoch_time_found = calendar.timegm((time.strptime(created_at, '%a, %d %b %Y %H:%M:%S +0000')))
            if int(epoch_time_found) > int(existing_epoch_time):
                twitter_id = (i['id'])
                from_user = (i['from_user']).encode('utf-8')
                text = (i['text']).encode('utf-8')
                created_at = (i['created_at']).encode('utf-8')
                profile_image_url_https = (i['profile_image_url_https']).encode('utf-8')
                location, lat, lng = gen_geo(from_user)

                write_tweet(twitter_id, from_user, text, created_at, keyword, location, lat, lng, epoch_time_found, profile_image_url_https)
                opsecHeader.send_email(keyword, "Twitter")
