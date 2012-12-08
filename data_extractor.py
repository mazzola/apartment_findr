#!/usr/bin/env python
# encoding: utf-8

import pymongo
import urllib2
from pymongo import MongoClient

three_taps_search_url = "http://3taps.net/search?category=RHFR&regionCode=USA-NYM-MAN&authToken=3231dd4e4ef940efbe719e30d2481c42"

# Extracts data from the 3taps api into database db
def extract_3taps_data(db):
    response = urllib2.urlopen(three_taps_search_url)
    print response.read()
    
#    apartments = db.apartments


def main():
    connection = MongoClient()
    db = connection.apartment_database

    extract_3taps_data(db)

if __name__ == '__main__':
	main()
