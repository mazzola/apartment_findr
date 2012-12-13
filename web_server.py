#!/usr/bin/env python
# encoding: utf-8
"""
movie_service.py: a RESTful movie data service

Score calculation, read functions for apartments and businesses, do the home handler
"""
import os
import codecs
import json
import bson
import re
import urlparse
import pymongo
from pymongo import MongoClient

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from bson.objectid import ObjectId
from bson.json_util import dumps
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)


### Movie Web Service implementation ###

class AptService(tornado.web.Application):
    """The apartment Service Web Application"""
    def __init__(self, db):
        handlers = [
            (r"/", HomeHandler),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "/templates/"}),
            (r"/results", ResultsHandler),
            (r"/apartment/([0-9a-z]+)(\..+)?", ApartmentHandler),
            (r"/business/([0-9a-z]+)(\..+)?", BusinessHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "templates"),
            debug=True,
            autoescape=None,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = db
        
class BaseHandler(tornado.web.RequestHandler):
    """Functions common to all handlers"""
    @property
    def db(self):
        return self.application.db
        
    @property
    def base_uri(self):
        """Returns the Web service's base URI (e.g., http://localhost:8888)"""
        protocol = self.request.protocol
        host = self.request.headers.get('Host')
        return protocol + "://" + host
        
    def write_error(self, status_code, **kwargs):
        """Attach human-readable msg to error messages"""
        self.finish("Error %d - %s" % (status_code, kwargs['message']))
    def accept_header(self):
    	"""Returns the headers associated with an HTTP Request"""
    	h = self.request.headers.get_list('Accept')
    	print "Headers: ", h
    	return h


class HomeHandler(BaseHandler):
    def get(self):
        self.render("index.html")
        
class ResultsHandler(BaseHandler):
    def get(self):
    	weights = []
    	for c in['food', 'shopping', 'nightlife', 'active', 'education', 'arts', 'restaurants', 'beauty']:
    		weights.append(self.get_arguments(c))
    	#listings = self.db.search(weights)
    	listings = [{'title':1,'score':2,'pic':'http://images.craigslist.org/3G63F63H65Gd5E75M7cc97a6776566c861baf.jpg','bedrooms':4,'price':5,'bathrooms':6,'url':'http://ithaca.craigslist.org/apa/3466893060.html','VIII':8,'description':9}]
        self.render("results.html", listings=listings)
        
class ApartmentHandler(BaseHandler):
    def get(self, id, format):
        listing = self.db.get_apartment(id)
        #listing = {'title':'2BD/1BA','score':87,'pic':'http://images.craigslist.org/3G63F63H65Gd5E75M7cc97a6776566c861baf.jpg',
    	#	'bedrooms':2,'price':'$700','bathrooms':1,'url':'http://ithaca.craigslist.org/apa/3466893060.html','VIII':8, 
    	#	'description':'950 sq feet of pure, unadulterated college', 'foodscore':90, 'shoppingscore':93,'activescore':91,'retaurantscore':92,'beautyscore':84,'nightlifescore':95,'educationscore':87,'artsscore':82,}
        if format == ".json":
            del listing['_id']
            self.write(dict(apartment=listing))
        elif format is None:
            self.render("apartment.html", listing=listing)
        
class BusinessHandler(BaseHandler):
    def get(self, id, format):
        # TODO replace with db call like this
        #business = self.db.get_business(id)
    	business = {'name':'Stella\'s', 'type':'food', 'address':'401 College Ave, Ithaca, NY'}
    	apartments = [{'title':1,'score':2,'pic':'http://images.craigslist.org/3G63F63H65Gd5E75M7cc97a6776566c861baf.jpg',
    	'bedrooms':4,'price':5,'bathrooms':6,'url':'http://ithaca.craigslist.org/apa/3466893060.html','VIII':8,'description':9}]

        if format == ".json":
            self.write(dict(business=business))
        else:
            self.render("business.html", business = business, apartments = apartments)

## Database Controller
class FindrDatabase(object):
    def __init__(self):
        print "Initializing database"
        conn = MongoClient()
        self.db = conn.findr_database
        self.apartments = self.db.apartments
        self.businesses = self.db.businesses

    def get_apartment(self, id):
        apartment = self.apartments.find_one({"_id" : ObjectId(id)})
        if apartment is None:
            raise tornado.web.HTTPError(404)
        return apartment

    def get_business(self, id):
        business = self.businesses.find_one({"_id" : ObjectId(id)})
        if businesses is None:
            raise tornado.web.HTTPError(404)
        return apartment

    def search(self, weights):
        apartments = self.apartments.find()
        for apartment in apartments:
            pass
            # Calculate score for every apartment using wieghted average

        # Search through all the apartments for the top 10
        best_apartments = []
        return best_apartments

### Script entry point ###

def main():
    tornado.options.parse_command_line()
    # Set up the database
    db = FindrDatabase()
    # Set up the Web application, pass the database
    apt_webservice = AptService(db)
    # Set up HTTP server, pass Web application
    try:
        http_server = tornado.httpserver.HTTPServer(apt_webservice)
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print "\nStopping service gracefully..."
    finally:
        tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()
