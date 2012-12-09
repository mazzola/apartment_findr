#!/usr/bin/env python
# encoding: utf-8
"""
movie_service.py: a RESTful movie data service

Score calculation, read functions for apartments and businesses, do the home handler
"""
import os
import codecs
import json
import re
import urlparse

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("movies", default="data/movies.csv", help="movies data file")
define("actors", default="data/actors.csv", help="actors data file")
define("mappings", default="data/movie_actors.csv", help="key mapping file")

### Movie Web Service implementation ###

class MovieService(tornado.web.Application):
    """The Movie Service Web Application"""
    def __init__(self, db):
        handlers = [
            (r"/", HomeHandler),
            (r"/actors(\..+)?", ActorListHandler),
            (r"/actors/(\d+)(\..+)?", ActorResourceHandler),
            (r"/movies(\..+)?", MovieListHandler),
            (r"/movies/(\d+)(\..+)?", MovieResourceHandler),
            (r"/movies/(\d+)/actors(\..+)?", MoviesActorsListHandler),
            (r"/search(\..+)?", QueryHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
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
        self.write("<html><body><h1>INFO/CS 4302 Homework 6</h1></body></html>")

class ActorListHandler(BaseHandler):
    def get(self, format):
        actors = self.db.list_actors(self.base_uri)
        if format is None:
            self.redirect("/actors.json")
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("actor_list.xml", actors=actors)
        elif format == ".json":
            self.write(dict(actors=actors))
        else:
            self.write_error(401, message="Format %s not supported" % format)

class MoviesActorsListHandler(ActorListHandler):
    def get(self, movie_id, format):
        actors = self.db.list_actors(self.base_uri, movie_id = movie_id)
        if format is None:
            redirect_uri = "/movies/%s/actors.json" % movie_id 
            self.redirect(redirect_uri)
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("actor_list.xml", actors=actors)
        elif format == ".json":
            self.write(dict(actors=actors))
        else:
            self.write_error(401, message="Format %s not supported" % format)

class MovieListHandler(BaseHandler):
    SUPPORTED_METHODS = ("GET", "POST")
    def get(self, format):
        movies = self.db.list_movies(self.base_uri)
        if format is None:
            self.redirect("/movies.json")
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("movie_list.xml", movies=movies)
        elif format == ".json":
            self.write(dict(movies=movies))
    
    def post(self, format):
        new_movie = json.loads(self.request.body)
        new_movie_id = self.db.create_movie(new_movie[1])
        self.set_status(201)
        self.set_header("Location", self.base_uri + "/movies/" + new_movie_id)

class ActorResourceHandler(BaseHandler):
    def get(self, actor_id, format):
        actor_resource = self.db.get_actor(actor_id, self.base_uri)
        h = self.accept_header()
        if format is None:
            self.redirect("/actors/%s.json" % actor_id) # default
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("actor.xml", actor=actor_resource)
        elif format == ".rdf":
            self.set_header("Content-Type", "application/rdf+xml")
            self.render("actor.rdf", actor=actor_resource)
        elif format == ".ttl":
            self.set_header("Content-Type", "text/turtle")
            self.render("actor.ttl", actor=actor_resource)
        elif format == ".json":
            self.write(actor_resource) # Tornado handles JSON automatically

class MovieResourceHandler(BaseHandler):
    SUPPORTED_METHODS = ("PUT", "GET", "DELETE")

    def get(self, movie_id, format):
        movie_resource = self.db.get_movie(movie_id, self.base_uri)
        if format is None:
            self.redirect("/movies/%s.json" % movie_id) # default
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("movie.xml", movie=movie_resource)
        elif format == ".rdf":
            self.set_header("Content-Type", "application/rdf+xml")
            self.render("movie.rdf", movie=movie_resource)
        elif format == ".ttl":
            self.set_header("Content-Type", "text/turtle")
            self.render("movie.ttl", movie=movie_resource)
        elif format == ".json":
            self.write(movie_resource) # Tornado handles JSON automatically

    def put(self, movie_id, format):
        if movie_id in self.db.movies:
            print "Updating movie %s" % movie_id
            new_movie = json.loads(self.request.body)
            self.db.update_movie(movie_id, new_movie[1])
    
    def delete(self, movie_id, format):
        if movie_id in self.db.movies:
            print "Deleting movie %s" % movie_id
            self.db.delete_movie(movie_id)

class QueryHandler(BaseHandler):
    
    def get(self, format):
        query_string = urlparse.parse_qs(self.request.query)['q'][0]
        results = self.db.find(query_string, self.base_uri)
        if format is None:
            redirect_uri = "search.json?q=%s" % query_string
            self.redirect(redirect_uri)
        elif format == ".xml":
            self.set_header("Content-Type", "application/xml")
            self.render("search-results.xml", results = results)
        elif format == ".json":
            self.write(dict(results=results))

### A dummy in-memory database implementation ###

class MovieDatabase(object):
    """A dummy in-memory database for handling movie data."""
    def __init__(self, movies_csv, actors_csv, mapping_csv):
        print "Loading data into memory...."
        mapping_data = self.read_from_csv(mapping_csv)
        movie_data = self.read_from_csv(movies_csv)
        actor_data = self.read_from_csv(actors_csv)
        self.movies = {}
        for movie in movie_data:
            self.movies[movie['id']] = movie
            actors = [actor['actor_id'] for actor in mapping_data
                            if actor['movie_id'] == movie['id']]
            self.movies[movie['id']]['actors'] = actors
        self.actors = {}
        for actor in actor_data:
            self.actors[actor['id']] = actor
            movies = [movie['movie_id'] for movie in mapping_data
                            if movie['actor_id'] == actor['id']]
            self.actors[actor['id']]['movies'] = movies
        
    # Simple regex search over all entities
    
    def find(self, query_string, base_uri):
        """Find entities matching a given query string"""
        results = []
        for actor in self.actors.values():
            if actor.has_key('name'):
               if re.search(query_string, actor['name'],
                            re.IGNORECASE) is not None:
                   print "found query string in actor name"
                   results.append(dict(type="actor",
                                 uri=base_uri + "/actors/" + actor['id']))
        for movie in self.movies.values():
            match = False
            if movie.has_key('title'):
                if re.search(query_string, movie['title'],
                   re.IGNORECASE) is not None:
                    match = True
            if movie.has_key('synopsis'):
                if re.search(query_string, movie['synopsis'],
                   re.IGNORECASE) is not None:
                    match = True
            if match:
                results.append(dict(type="movie",
                              uri=base_uri + "/movies/" + movie['id']))                
        print "Found %d results for query %s" % (len(results), query_string)
        return results
    
    # ACTOR CRUD operations
    
    def get_actor(self, actor_id, base_uri):
        """Returns data about an actor with IDs converted to URIs"""
        actor = self.actors[actor_id]
        actor_resource = {}
        actor_resource['uri'] = base_uri + "/actors/" + actor_id
        if actor.has_key('name'):
            actor_resource['name'] = actor['name']
        if actor.has_key('birth_date'):
            actor_resource['birth_date'] = actor['birth_date']
        if actor.has_key('movies'):
            actor_resource['movies'] = [(base_uri + "/movies/" + movie_id)
                                        for movie_id in actor['movies']] 
        return actor_resource

    def list_actors(self, base_uri, movie_id = None):
        """Returns a list of actors with IDs converted to URIs"""
        if movie_id is None:
            actors = self.actors.values()
        else:
            actors = [actor for actor in self.actors.values()
                            if movie_id in actor['movies']]
        actor_list = []
        for actor in actors:
            entry = {}
            entry['uri'] = base_uri + "/actors/" + actor['id']
            if actor.has_key('name'):
                entry['name'] = actor['name']
            actor_list.append(entry)
        return actor_list
    
    # Movie CRUD operations
    def get_movie(self, movie_id, base_uri):
        """Returns data about a movie with IDs converted to URIs"""
        movie = self.movies[movie_id]
        movie_resource = {}
        movie_resource['uri'] = base_uri + "/movies/" + movie_id
        if movie.has_key('title'):
            movie_resource['title'] = movie['title']
        if movie.has_key('synopsis'):
            movie_resource['synopsis'] = movie['synopsis']
        if movie.has_key('actors'):
            movie_resource['actors'] = [(base_uri + "/actors/" + actor_id)
                                        for actor_id in movie['actors']] 
        return movie_resource

    def list_movies(self, base_uri):
        """Returns a list of movies with IDs converted to URIs"""
        movie_list = []
        for movie in self.movies.values():
            entry = {}
            entry['uri'] = base_uri + "/movies/" + movie['id']
            if movie.has_key('title'):
                entry['title'] = movie['title']
            movie_list.append(entry)
        return movie_list

    def create_movie(self, movie):
        """Creates a new movie and returns the assigned ID"""
        max_id = sorted([int(movie_id) for movie_id in self.movies])[-1]
        new_id = str(max_id + 1)
        self.movies[new_id] = movie
        return new_id

    def update_movie(self, movie_id, movie):
        """Updates a movie with a given id"""
        self.movies[movie_id] = movie
    
    def delete_movie(self, movie_id):
        """Deletes a movie and references to this movie"""
        del self.movies[movie_id]
        for actor in self.actors.values():
            if movie_id in actor['movies']:
                print "Deleting movie reference from actor %s" % actor['id']
                actor['movies'].remove(movie_id)
    
    # Data import
    
    def read_from_csv(self, csv_file):
        """Reads CSV entries into a list containing a set of dictionaries.
        CSV header row entries are taken as dictionary keys"""
        data = []
        with codecs.open(csv_file, 'r', encoding='utf-8') as csvfile:
            header = None
            for i, line in enumerate(csvfile):
                line_split = [x.strip() for x in line.split("|")]
                line_data = [x for x in line_split if len(x) > 0]
                if i == 0:
                    header = line_data
                else:
                    entry = {}
                    for i,datum in enumerate(line_data):
                        entry[header[i]] = datum
                    data.append(entry)
        print "Loaded %d entries from %s" % (len(data), csv_file)
        return data
                    
### Script entry point ###

def main():
    tornado.options.parse_command_line()
    # Set up the database
    db = MovieDatabase(options.movies, options.actors, options.mappings)
    # Set up the Web application, pass the database
    movie_webservice = MovieService(db)
    # Set up HTTP server, pass Web application
    try:
        http_server = tornado.httpserver.HTTPServer(movie_webservice)
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print "\nStopping service gracefull..."
    finally:
        tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()