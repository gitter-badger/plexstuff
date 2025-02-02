#!/usr/bin/env python3

import sys, signal
# code to handle Ctrl+C, convenience method for command line tools
def signal_handler( signal, frame ):
    print( "You pressed Ctrl+C. Exiting...")
    sys.exit( 0 )
signal.signal( signal.SIGINT, signal_handler )
import re, codecs, requests, zipfile, os, logging, time
from fabric import Connection
from termcolor import colored
from io import BytesIO
from itertools import chain
from pathos.multiprocessing import Pool
from optparse import OptionParser

from plexcore import subscene, plexcore_deluge
from plextmdb import plextmdb_subtitles

def get_items_yts( name, maxnum = 10 ):
    assert( maxnum >= 5 )
    items = plextmdb_subtitles.get_subtitles_yts( name )
    if items is None: return None
    return list( map(lambda item: { 'title' : item['name'], 'zipurl' : item['url'],
                                    'content' : 'yts' }, items[:maxnum] ) )

def get_items_subscene( name, maxnum = 20, extra_strings = [ ] ):
    assert( maxnum >= 5 )
    subtitles_map = plextmdb_subtitles.get_subtitles_subscene( name, extra_strings = extra_strings )
    if subtitles_map is None: return None
    return list( map(lambda title: { 'title' : title, 'srtdata' : subtitles_map[ title ],
                                     'content' : 'subscene' },
                     sorted( subtitles_map )[:maxnum] ) )

def get_items_opensubtitles( name, maxnum = 20, extra_strings = [ ] ):
    assert( maxnum >= 5 )
    subtitles_map = plextmdb_subtitles.get_subtitles_opensubtitles( name, extra_strings = extra_strings )
    if subtitles_map is None: return None
    return list( map(lambda title: { 'title' : title,
                                     'srtdata' : subtitles_map[ title ],
                                     'content' : 'opensubtitles' },
                     sorted( subtitles_map )[:maxnum] ) )

def get_movie_subtitle_items( items, filename = 'eng.srt', do_send = False ):
    if do_send:
        client, status = plexcore_deluge.get_deluge_client( )
        if status != 'SUCCESS':
            print( "error, could not find remote server to push subtitle info.")
            return
        username = client.username
        password = client.password
        server = client.host
        conn = Connection(
            server, user = username,
            connect_kwargs = { 'password' : password } )
    
    coloration_dict = { 'yts' : 'red',
                        'subscene' : 'green',
                        'opensubtitles' : 'blue' }
    if len( items ) == 0: return
    sortdict = { idx + 1 : item for ( idx, item ) in enumerate( items ) }
    bs = 'Choose movie subtitle:\n%s\n' % '\n'.join(
        map(lambda idx: '%d: %s' % ( idx, colored( sortdict[ idx ][ 'title' ],
                                                   coloration_dict[ sortdict[ idx ][ 'content' ] ] ) ),
            sorted( sortdict ) ) )
    iidx = input( bs )
    if iidx.lower( ).strip( ) == 'qq':
        print( 'Abort the search for subtitles. Exit...' )
        return
    try:
        iidx = int( iidx.strip( ) )
        if iidx not in sortdict:
            print('Error, need to choose one of the movie names. Exiting...')
            return
        content = sortdict[ iidx ][ 'content' ]
        if content == 'yts': # yts
            zipurl = sortdict[ iidx ][ 'zipurl' ]
            with zipfile.ZipFile( BytesIO( requests.get( zipurl ).content ), 'r') as zf:
                name = max( zf.namelist( ) )
                if not do_send:
                    with open( filename, 'wb' ) as openfile:
                        openfile.write( zf.read( name ) )
                else:
                    with BytesIO( ) as io_obj:
                        io_obj.write( zf.read( name ) )
                        r = conn.put( io_obj, os.path.basename( filename ) )
        elif content == 'subscene': # subscene
            suburl = sortdict[ iidx ][ 'srtdata' ]
            zipcontent = subscene.get_subscene_zipped_content( suburl )
            with zipfile.ZipFile( BytesIO( zipcontent ), 'r') as zf:
                name = max( zf.namelist( ) )
                if not do_send:
                    with open( filename, 'wb' ) as openfile:
                        openfile.write( zf.read( name ) )
                else:
                    with BytesIO( ) as io_obj:
                        io_obj.write( zf.read( name ) )
                        r = conn.put( io_obj, os.path.basename( filename ) )
        elif content == 'opensubtitles': # opensubtitles
            zipurl = sortdict[ iidx ][ 'srtdata' ]
            with zipfile.ZipFile( BytesIO( requests.get( zipurl ).content ), 'r') as zf:
                name = max( filter(lambda nm: nm.endswith('.srt'), zf.namelist( ) ) )
                if not do_send:
                    with open( filename, 'wb' ) as openfile:
                        openfile.write( zf.read( name ) )
                else:
                    with BytesIO( ) as io_obj:
                        io_obj.write( zf.read( name ) )
                        r = conn.put( io_obj, os.path.basename( filename ) )
    except Exception as e:
        print('Error, did not give a valid integer value. Exiting...')
        return

if __name__=='__main__':
    parser = OptionParser( )
    parser.add_option('-n', '--name', dest='name', type=str, action='store',
                      help = 'Name of the movie file to get.')
    parser.add_option('-m', '--maxnum', dest='maxnum', type=int, action='store', default = 10,
                      help = 'Maximum number of torrents to look through. Default is 10.')
    parser.add_option('-f', '--filename', dest='filename', action='store', type=str, default = 'eng.srt',
                      help = 'Name of the subtitle file. Default is eng.srt.')
    parser.add_option('-b', '--bypass', dest='do_bypass', action='store_true', default = False,
                      help = 'If chosen, then bypass yts subtitles.')
    parser.add_option('-k', '--keywords', dest='keywords', action='store', type=str,
                      help = ' '.join([
                          'Optional definition of a list of keywords to look for,',
                          'in the subscene search for movie subtitles.' ]) )
    parser.add_option('-s', '--send', dest='do_send', action='store_true', default = False,
                      help = 'If chosen, then send the file to remote host.' )
    parser.add_option('--info', dest='do_info', action='store_true', default = False,
                      help = 'If chosen, run in info mode.' )
    
    opts, args = parser.parse_args( )
    assert( opts.name is not None )
    assert( os.path.basename( opts.filename ).endswith('.srt' ) )
    logger = logging.getLogger( )
    if opts.do_info: logger.setLogger( logging.INFO )
    keywords_set = { }
    if opts.keywords is not None:
        keywords_set = set(map(lambda tok: tok.lower( ),
                               filter(lambda tok: len( tok.strip( ) ) != 0,
                                      opts.keywords.strip().split(','))))
    #
    ## now calculation with multiprocessing
    time0 = time.time( )
    pool = Pool( processes = 3 )
    if not opts.do_bypass:
        jobs = [ pool.apply_async( get_items_yts, args = ( opts.name, opts.maxnum ) ) ]
    else: jobs = [ ]
    jobs += list(map(
        lambda func: pool.apply_async( func, args = ( opts.name, opts.maxnum, keywords_set ) ),
        ( get_items_subscene, get_items_opensubtitles ) ) )
    items_lists = [ ]
    for job in jobs:
        try:
            items = job.get( )
            if items is None: continue
            items_lists.append( items )
        except: pass
    items = list( chain.from_iterable( items_lists ) )
    logging.info( 'search for movie subtitles took %0.3f seconds.' % ( time.time( ) - time0 ) )    
    if len( items ) != 0:
        get_movie_subtitle_items(
            items, filename = opts.filename, do_send = opts.do_send )
