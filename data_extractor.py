#!/usr/bin/env python
# encoding: utf-8

import pymongo
import urllib2
import json
import yelp_api
from pymongo import MongoClient

three_taps_search_url = "http://3taps.net/search?category=RHFR&regionCode=USA-NYM-MAN&authToken=3231dd4e4ef940efbe719e30d2481c42&annotations={source_map_google:*%20AND%20source_loc:newyork}"
three_taps_test_url = "http://3taps.net/search?category=RHFR&regionCode=USA-NYM-MAN&authToken=3231dd4e4ef940efbe719e30d2481c42&annotations={source_map_google:*%20AND%20source_loc:newyork}"


# Extracts data from the 3taps api into an in memory dict
def extract_3taps_data():
    # TODO change this to production/search URL
    response = urllib2.urlopen(three_taps_test_url)
    print "Getting data from 3taps..."
    response_dict = json.loads(response.read())
    raw_apartment_dict = response_dict["results"]
    # Refine the results to get title, number of bedrooms, price, post url, picture and description
    refined_apartment_dict = {}
    
    for raw_apartment in raw_apartment_dict:
        refined_apartment = {}
        title = raw_apartment['annotations']['heading']
        refined_apartment.update({'title':title})
        bedrooms = raw_apartment['annotations']['bedrooms']
        refined_apartment.update({'bedrooms':bedrooms})
        price = raw_apartment['price']
        refined_apartment.update({'price':price})
        post_url = raw_apartment['sourceUrl']
        refined_apartment.update({'url':post_url})
        description = raw_apartment['body']
        refined_apartment.update({'description':description})
        if (raw_apartment['hasImage']):
            picture = raw_apartment['images'][0]['full']
            refined_apartment.update({'pic':picture})

        refined_apartment_dict.append(refined_apartment)

# Takes an apartment dict and a business dictonary and inserts all the
# entries into a mongodb
def import_into_db(apartment_dict, businesses_dict, db):
    print "Storing data in mongodb"
    apartments = db.apartments
    apartments.insert(apartment_dict)

    businesses = db.businesses
    businesses.insert(businesses_dict)
    print "Done creating database!"


def main():
    connection = MongoClient()
    db = connection.findr_database
    #extract_3taps_data()

if __name__ == '__main__':
	main()
