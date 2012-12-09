"""Command line interface to the Yelp Search API."""

import json
import oauth2
import optparse
import urllib
import urllib2
import pymongo
from pymongo import MongoClient



# Setup URL params from options
url_params = {}
url_params['location'] = "31st and Broadway, NY"
#url_params['ll'] = options.point
url_params['radius_filter'] = 1000
url_params['category_filter'] = "food"
url_params['sort'] = 2

consumer_key = 'WoH7PFlWIbmnKuvGdMaNhw'
consumer_secret = 'GNCVbv7iijc2WbWp3JqA8p0VIok'
token = '_XgyWyzcARzjGI2f61fB1gZCE8P8ZT_o'
token_secret = 'U4AgG6kBapGMhPoGTqGQRFSjJ4w'


def request(host, path, url_params, consumer_key, consumer_secret, token, token_secret):
  """Returns response for API request."""
  # Unsigned URL
  encoded_params = ''
  if url_params:
    encoded_params = urllib.urlencode(url_params)
  url = 'http://%s%s?%s' % (host, path, encoded_params)
  print 'URL: %s' % (url,)

  # Sign the URL
  consumer = oauth2.Consumer(consumer_key, consumer_secret)
  oauth_request = oauth2.Request('GET', url, {})
  oauth_request.update({'oauth_nonce': oauth2.generate_nonce(),
                        'oauth_timestamp': oauth2.generate_timestamp(),
                        'oauth_token': token,
                        'oauth_consumer_key': consumer_key})

  token = oauth2.Token(token, token_secret)
  oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
  signed_url = oauth_request.to_url()
  print 'Signed URL: %s\n' % (signed_url,)

  # Connect
  try:
    conn = urllib2.urlopen(signed_url, None)
    try:
      response = json.loads(conn.read())
    finally:
      conn.close()
  except urllib2.HTTPError, error:
    response = json.loads(error.read())

  return response

response = request('api.yelp.com', '/v2/search', url_params, consumer_key, consumer_secret, token, token_secret)
print json.dumps(response, sort_keys=True, indent=2)
print response['businesses'][1]

conn = MongoClient()
db =  conn.business_database
businesses = db.businesses
business_ids = []
businesses.insert(response['businesses'])
print "In the database"
for business in businesses.find():
	print business['name'], business['rating']

