#!/usr/bin/env python
# encoding: utf-8

import pymongo
import urllib2
import json
from pymongo import MongoClient

three_taps_search_url = "http://3taps.net/search?category=RHFR&regionCode=USA-NYM-MAN&authToken=3231dd4e4ef940efbe719e30d2481c42&annotations={source_map_google:*%20AND%20source_loc:newyork}"

# Extracts data from the 3taps api into database db
def extract_3taps_data(db):
    response = urllib2.urlopen(three_taps_search_url)
    print "Getting data from 3taps..."
    response_dict = json.loads(response.read())
    apartment_dict = response_dict["results"]

    print "Storing data in mongodb"
    apartments = db.apartments
    for apartment in apartment_dict:
        apartments.insert(apartment)

def main():
    connection = MongoClient()
    db = connection.apartment_database

    extract_3taps_data(db)

if __name__ == '__main__':
	main()
