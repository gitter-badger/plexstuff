import os, sys, glob, logging, pytest
import qdarkstyle, pickle, gzip, time
from PyQt4.QtGui import QApplication
from plextmdb import plextmdb_gui, plextmdb_mygui, plextmdb_totgui
from .test_plexcore import get_token_fullURL

testDir = os.path.expanduser( '~/.config/plexstuff/tests' )

@pytest.fixture( scope="module" )
def get_movie_data_rows( request, get_token_fullURL ):
    time0 = time.time( )
    ebuild = request.config.option.do_rebuild
    doLocal = request.config.option.do_local
    verify = request.config.option.do_verify
    fullURL, token = get_token_fullURL
    if rebuild:
        #
        ## movie data rows
        movie_data_rows = plextmdb_totgui.TMDBTotGUI.fill_out_movies(
            fullURL, token, debug = True )
        pickle.dump( movie_data_rows, gzip.open(
            os.path.join( testDir, 'movie_data_rows.pkl.gz' ), 'wb' ) )
        print( 'processed and stored new movie data in %0.3f seconds.' % (
            time.time( ) - time0 ) )
    else:
        movie_data_rows = pickle.load( gzip.open(
            os.path.join( testDir, 'movie_data_rows.pkl.gz' ), 'rb' ) )
    yield movie_data_rows

@pytest.fixture( scope="module" )
def get_app( ):
    app = QApplication([])
    app.setStyleSheet( qdarkstyle.load_stylesheet_pyqt( ) )
    yield app

@pytest.fixture( scope="module" )
def get_movie_data_rows( ):
    movie_data_rows = pickle.load( gzip.open(
        os.path.join( testDir, 'movie_data_rows.pkl.gz' ), 'rb' ) )
    yield movie_data_rows

def test_tmdb_mygui( get_token_fullURL, get_movie_data_rows,
                     get_app, request ):
    verify = request.config.option.do_verify
    fullurl, token = get_token_fullURL
    app = get_app
    movie_data_rows = get_movie_data_rows
    tmdb_mygui = plextmdb_mygui.TMDBMyGUI(
        token, movie_data_rows, verify = verify )

def test_tmdb_gui( get_token_fullURL, get_movie_data_rows,
                   get_app, request ):
    verify = request.config.option.do_verify
    fullurl, token = get_token_fullURL
    app = get_app
    movie_data_rows = get_movie_data_rows
    tmdbgui = plextmdb_gui.TMDBGUI(
        token, fullurl, movie_data_rows, verify = verify )

def test_tmdb_totgui( get_token_fullURL, get_movie_data_rows,
                      get_app, request ):
    verify = request.config.option.do_verify
    fullurl, token = get_token_fullURL
    app = get_app
    movie_data_rows = get_movie_data_rows
    tmdb_totgui = plextmdb_totgui.TMDBTotGUI(
        fullurl, token, movie_data_rows = movie_data_rows,
        doLarge = True, verify = verify )

def test_tmdb_torrents( get_token_fullURL, get_app, request ):
    movie = 'Big Hero 6'
    bypass = request.config.option.do_bypass
    fullurl, token = get_token_fullURL
    app = get_app
    tmdbt = plextmdb_gui.TMDBTorrents(
        None, token, movie, bypass = bypass )
    
                        
