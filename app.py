from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_restful import Api, Resource
from dotenv import load_dotenv
from os import environ
from marshmallow import post_load, fields, ValidationError

load_dotenv()

# Create App instance
app = Flask(__name__)

# Add DB URI from .env
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('SQLALCHEMY_DATABASE_URI')

# Registering App w/ Services
db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)
CORS(app)
Migrate(app, db)

# Models
class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    album = db.Column(db.String(200), nullable=False)
    release_date = db.Column(db.Date)
    genre = db.Column(db.String(200))
    running_time = db.Column(db.Integer)
    likes = db.Column(db.Integer,default=0)
    dislikes = db.Column(db.Integer,default=0)


    def __repr__(self):
        return f'{self.title} {self.artist} {self.album} {self.release_date} {self.genre} {self.running_time} {self.likes} {self.dislikes}'

# Schemas
class SongSchema(ma.Schema):
    id = fields.Integer(primary_key=True)
    title = fields.String(required=True)
    artist = fields.String(required=True)
    album = fields.String(required=True)
    release_date = fields.Date()
    genre = fields.String()
    running_time = fields.Integer()
    likes = fields.Integer()
    dislikes = fields.Integer()

    class Meta:
        fields = ("id", "title", "artist", "album", "release_date", "genre", "running_time", "likes", "dislikes")
        
    @post_load
    def create_song(self, data, **kwargs):
        return Song(**data)

song_schema = SongSchema()
songs_schema = SongSchema(many=True)

# Resources
class SongListResource(Resource):
    def get(self):
        custom_response = {}
        all_songs = Song.query.all()
        custom_response["songs"] = songs_schema.dump(all_songs)
        total_running_time = 0
        for song in all_songs:
            total_running_time += song.running_time
        custom_response["total_running_time"] = round(total_running_time/60,2)
                    
        print(custom_response)
        return custom_response, 200

    def post(self):
        form_data = request.get_json()
        try:
            new_song = song_schema.load(form_data)
            db.session.add(new_song)
            db.session.commit()
            return song_schema.dump(new_song), 201
        except ValidationError as err:
            return err.messages, 400
    

class SongResource(Resource):
    def get(self, pk):
        song_from_db = Song.query.get_or_404(pk)
        return song_schema.dump(song_from_db), 200
    
    def delete(self, pk):
        song_from_db = Song.query.get_or_404(pk)
        db.session.delete(song_from_db)
        db.session.commit()
        return '', 204
    
    def put(self, pk):
        song_from_db = Song.query.get_or_404(pk)
        if 'title' in request.json:
            song_from_db.title=request.json['title']
        if 'artist' in request.json:
            song_from_db.artist=request.json['artist']
        if 'album' in request.json:
            song_from_db.album=request.json['album']
        if 'release_date' in request.json:
            song_from_db.release_date=request.json['release_date']
        if 'genre' in request.json:
            song_from_db.genre=request.json['genre']
        if 'running_time' in request.json:
            song_from_db.running_time=request.json['running_time']
        db.session.commit()
        return song_schema.dump(song_from_db), 200
    
    def patch(self, like):
        song_from_db = Song.query.get_or_404(like)
        song_from_db.likes += 1
        db.session.commit()
        return song_schema.dump(song_from_db), 200

class SongsResource(Resource):
    def patch(self, dislike):
        song_from_db = Song.query.get_or_404(dislike)
        song_from_db.dislikes -= 1
        db.session.commit()
        return song_schema.dump(song_from_db), 200
        
# Routes
api.add_resource(SongListResource, '/api/songs')
api.add_resource(SongResource, '/api/songs_like/<int:like>')
api.add_resource(SongsResource, '/api/songs_dislike/<int:dislike>')