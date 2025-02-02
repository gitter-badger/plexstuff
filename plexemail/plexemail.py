import os, sys, titlecase, datetime, re, time, requests, mimetypes, logging
import mutagen.mp3, mutagen.mp4, glob, multiprocessing, re, httplib2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage

from plexcore import session, plexcore, mainDir, get_lastupdated_string
from plexcore import get_formatted_size, get_formatted_duration
from plexemail import send_email_lowlevel, send_email_localsmtp, emailAddress, emailName

def send_email_movie_torrent( movieName, data, isJackett = False, verify = True ):
    assert( emailAddress is not None ), "Error, email address must not be None"
    if emailName is None:
        emailString = emailAddress
        name = 'Friend'
    else:
        emailString = '%s <%s>' % ( emailName, emailAddress )
        name = emailName.split( )[ 0 ].strip( )
    dtstring = datetime.datetime.now( ).strftime('%d %B %Y, %I:%M %p')
    msg = MIMEMultipart( )
    msg['From'] = emailString
    msg['To']  = emailString
    if emailName is not None:
        msg['Subject'] = '%s, can you download this movie, %s, requested on %s?' % (
           emailName.split()[0],  movieName, dtstring )
    else:
        msg['Subject'] = 'Can you download this movie, %s, requested on %s?' % (
            movieName, dtstring )
    if not isJackett:
        torfile = '%s.torrent' % '_'.join( movieName.split( ) ) # change to get to work
        torfile_mystr = '%s.torrent' % '\_'.join( movieName.split( ) ) # change to get to work
        #
        tup_formatting = ( name, '%s.' % torfile_mystr, '%s.' % dtstring )
        wholestr = open( os.path.join(
            mainDir, 'resources',
            'plextmdb_sendmovie_torrent.tex' ), 'r' ).read( )
        wholestr = wholestr % tup_formatting
        htmlString = plexcore.latexToHTML( wholestr )
        htmlString = htmlString.replace('strong>', 'B>')
        body = MIMEText( htmlString, 'html', 'utf-8' )
        att = MIMEApplication( data, _subtype = 'torrent' )
        att.add_header(
            'content-disposition', 'attachment',
            filename = torfile )
        msg.attach( body )
        msg.attach( att )
    else:
        mag_link = data
        wholestr = open( os.path.join(
            mainDir, 'resources',
            'plextmdb_sendmovie_magnet.tex' ), 'r' ).read( )
        tup_formatting = (
            name, mag_link, movieName, dtstring )
        htmlString = plexcore.latexToHTML( wholestr )
        htmlString = htmlString.replace('strong>', 'B>')
        body = MIMEText( htmlString, 'html', 'utf-8' )
        msg.attach( body )
    #
    ## now send the email
    send_email_lowlevel( msg, verify = verify )
    return 'SUCCESS'

def send_email_movie_none( movieName, verify = True ):
    assert( emailAddress is not None ), "Error, email address must not be None"
    if emailName is None:
        emailString = emailAddress
        name = 'Friend'
    else:
        emailString = '%s <%s>' % ( emailName, emailAddress )
        name = emailName.split( )[ 0 ].strip( )
    dtstring = datetime.datetime.now( ).strftime('%d %B %Y, %I:%M %p')
    msg = MIMEMultipart( )
    msg['From'] = emailString
    msg['To']  = emailString
    if emailName is not None:
        msg['Subject'] = '%s, can you download this movie, %s, requested on %s?' % (
           emailName.split()[0],  movieName, dtstring )
    else:
        msg['Subject'] = 'Can you download this movie, %s, requested on %s?' % (
            movieName, dtstring )
    #
    wholestr = open( os.path.join( mainDir, 'resources',
                                   'plextmdb_sendmovie_none.tex' ), 'r' ).read( )
    tup_formatting = ( name, movieName, dtstring )
    wholestr = wholestr % tup_formatting
    htmlString = plexcore.latexToHTML( wholestr )
    htmlString = htmlString.replace('strong>', 'B>')
    body = MIMEText( htmlString, 'html', 'utf-8' )
    msg.attach( body )
    #
    send_email_lowlevel( msg, verify = verify )
    return 'SUCCESS'

def get_summary_body( token, nameSection = False, fullURL = 'http://localhost:32400' ):
    # allrows = plexcore.get_allrows( )
    tup_formatting = (
        get_lastupdated_string( dt = plexcore.get_updated_at(
            token, fullURLWithPort = fullURL ) ), #0
        get_summary_data_freshair_remote( fullURLWithPort = fullURL, token = token ), #1
        _get_itemized_string( get_summary_data_thisamericanlife_remote(
            fullURLWithPort = fullURL,
            token = token ) ), #2
        get_summary_data_music_remote( fullURLWithPort = fullURL, token = token ), #3
        _get_itemized_string( get_summary_data_movies_remote(
            fullURLWithPort = fullURL, token = token ) ), #4
        get_summary_data_television_remote( fullURLWithPort = fullURL, token = token ), #5
    )
    wholestr = open( os.path.join( mainDir, 'resources', 'plexstuff_body_template.tex' ), 'r' ).read( )
    wholestr = wholestr % tup_formatting
    if nameSection:
        wholestr = '\n'.join([ '\section{Summary}', wholestr ])
    return wholestr

def send_individual_email_perproc( input_tuple ):
    mainHTML, access_token, email, name = input_tuple
    while True:
        try:
            send_individual_email( mainHTML, access_token, email, name = name )
            return
        except Exception as e:
            if name is None:
                print('Problem sending to %s. Trying again...' % email)
            else:
                print('Problem sending to %s <%s>. Trying again...' % ( name, email ) )
    
def test_email( subject = None, htmlstring = None, verify = True ):
    assert( emailAddress is not None ), "Error, email address must not be None"
    if emailName is None: emailString = emailAddress
    else: emailString = '%s <%s>' % ( emailName, emailAddress )
    fromEmail = emailString
    if subject is None:
        subject = titlecase.titlecase( 'Plex Email Newsletter For %s' % mydate.strftime( '%B %Y' ) )
    msg = MIMEMultipart( )
    msg['From'] = fromEmail
    msg['Subject'] = subject
    msg['To'] = emailAddress
    if htmlstring is None: body = MIMEText( 'This is a test.' )
    else: body = MIMEText( htmlstring, 'html', 'utf-8' )
    msg.attach( body )
    send_email_lowlevel( msg, verify = verify )

def send_individual_email_full( mainHTML, subject, email, name = None, attach = None,
                               attachName = None, attachType = 'txt', verify = True ):
    assert( emailAddress is not None ), "Error, email address must not be None"
    if emailName is None: emailString = emailAddress
    else: emailString = '%s <%s>' % ( emailName, emailAddress )
    fromEmail = emailString
    msg = MIMEMultipart( )
    msg['From'] = fromEmail
    msg['Subject'] = subject
    if name is None:
        msg['To'] = email
        htmlstring = mainHTML
    else:
        msg['To'] = '%s <%s>' % ( name, email )
        firstname = name.split()[0].strip()
        htmlstring = re.sub( 'Hello Friend,', 'Hello %s,' % firstname, mainHTML )
    body = MIMEText( htmlstring, 'html', 'utf-8' )
    msg.attach( body )
    if attach is not None and attachName is not None:
        att = MIMEApplication( attach, _subtype = 'text' )
        att.add_header( 'content-disposition', 'attachment', filename = attachName )
        msg.attach( att )
    send_email_lowlevel( msg, verify = verify )

def send_individual_email_full_withsingleattach(
        mainHTML, subject, email, name = None,
        attachData = None, attachName = None,
        verify = True ):
    assert( emailAddress is not None ), "Error, email address must not be None"
    if emailName is None: emailString = emailAddress
    else: emailString = '%s <%s>' % ( emailName, emailAddress )
    fromEmail = emailString
    msg = MIMEMultipart( )
    msg['From'] = fromEmail
    msg['Subject'] = subject
    if name is None:
        msg['To'] = email
        htmlstring = mainHTML
    else:
        msg['To'] = '%s <%s>' % ( name, email )
        firstname = name.split()[0].strip()
        htmlstring = re.sub( 'Hello Friend,', 'Hello %s,' % firstname, mainHTML )
    body = MIMEText( htmlstring, 'html', 'utf-8' )
    msg.attach( body )
    if attachData is not None:
        assert( attachName is not None )
        attachName = os.path.basename( attachName )
        content_type, encoding = mimetypes.guess_type(attachName)
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        att = MIMEApplication( attachData, _subtype = sub_type )
        att.add_header( 'content-disposition', 'attachment', filename = attachName )
        msg.attach( att )
    send_email_lowlevel( msg, verify = verify )
        
def send_individual_email_full_withattachs(
        mainHTML, subject, email, name = None,
        attachNames = None, attachDatas = None ):
    assert( emailAddress is not None ), "Error, email address must not be None"
    if emailName is None: fromEmail = emailAddress
    else: fromEmail = '%s <%s>' % ( emailName, emailAddress )
    msg = MIMEMultipart( )
    msg['From'] = fromEmail
    msg['Subject'] = subject
    if name is None:
        msg['To'] = email
        htmlstring = mainHTML
    else:
        msg['To'] = '%s <%s>' % ( name, email )
        firstname = name.split()[0].strip()
        htmlstring = re.sub( 'Hello Friend,', 'Hello %s,' % firstname, mainHTML )
    body = MIMEText( htmlstring, 'html', 'utf-8' )
    msg.attach( body )
    if attachNames is not None:
        assert( attachDatas is not None )
        for attachName, data in filter(None, zip( attachNames, attachDatas ) ):
            #
            ## gotten code from https://developers.google.com/gmail/api/guides/sending
            attachName = os.path.basename( attachName )
            content_type, encoding = mimetypes.guess_type(attachName)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            main_type, sub_type = content_type.split('/', 1)
            if main_type == 'text': att = MIMEText(data, _subtype=sub_type)
            elif main_type == 'image': att = MIMEImage(data, _subtype=sub_type)
            elif main_type == 'audio': att = MIMEAudio(data, _subtype=sub_type)
            else:
                att = MIMEBase(main_type, sub_type)
                att.set_payload(data)
            att.add_header( 'content-disposition', 'attachment', filename = attachName )
            msg.attach( att )
    #send_email_lowlevel( msg )
    send_email_localsmtp( msg ) # google has problems sending "big" emails (lots of attachments)

def send_individual_email(
        mainHTML, email, name = None,
        mydate = datetime.datetime.now().date(),
        verify = True ):
    assert( emailAddress is not None ), "Error, email address must not be None"
    if emailName is None: fromEmail = emailAddress
    else: fromEmail = '%s <%s>' % ( emailName, emailAddress )
    subject = titlecase.titlecase( 'Plex Email Newsletter For %s' % mydate.strftime( '%B %Y' ) )
    msg = MIMEMultipart( )
    msg['From'] = fromEmail
    msg['Subject'] = subject
    if name is None:
        msg['To'] = email
        htmlstring = mainHTML
    else:
        msg['To'] = '%s <%s>' % ( name, email )
        firstname = name.split()[0].strip()
        htmlstring = re.sub( 'Hello Friend,', 'Hello %s,' % firstname, mainHTML )
    #
    body = MIMEText( htmlstring, 'html', 'utf-8' )
    msg.attach( body )
    send_email_lowlevel( msg, verify = verify )

def get_summary_html( preambleText = '', postambleText = '', pngDataDict = { },
                      name = None, token = None, doLocal = True ):
    data = plexcore.checkServerCredentials( doLocal = doLocal, verify = False )
    if data is None:
        print('Sorry, now we need to provide an user name and password. Please get one!')
        return
    fullURL, token = data
    nameSection = False
    if len(preambleText.strip()) != 0:
        nameSection = True
    if name is None:
        name = 'Friend'
    tup_formatting = (
        name,
        preambleText,
        get_summary_body( token, nameSection = nameSection, fullURL = fullURL ),
        postambleText,
    )
    wholestr = open( os.path.join( mainDir, 'resources', 'plexstuff_template.tex' ), 'r' ).read( )
    wholestr = wholestr % tup_formatting
    wholestr = wholestr.replace('textbf|', 'textbf{')
    wholestr = wholestr.replace('ZZX|', '}')
    htmlString = plexcore.latexToHTML( wholestr )
    htmlString = htmlString.replace('strong>', 'B>')
    #
    ## now process PNG IMG data
    htmlString = plexcore.processValidHTMLWithPNG( htmlString, pngDataDict )
    return htmlString

def _get_itemized_string( stringtup ):
    mainstring, maindict = stringtup
    stringelems = [ mainstring, '\\begin{itemize}' ]
    for itm in sorted( maindict ):
        stringelems.append( '\item \\textbf|%sZZX|: %s' % ( itm, maindict[itm] ) )
    stringelems.append('\\end{itemize}')
    return '\n'.join( stringelems )

def _get_artistalbum( filename ):
    if os.path.basename( filename ).endswith( '.m4a' ):
        mp4tag = mutagen.mp4.MP4( filename )
        if not all([ key in mp4tag for key in ( '\xa9alb', '\xa9ART' ) ]):
            return None
        album = max(mp4tag['\xa9alb']).strip()
        artist = max(mp4tag['\xa9ART']).strip()        
    elif os.path.basename( filename ).endswith( '.mp3' ):
        mp3tag = mutagen.mp3.MP3( filename )
        if not all ([ key in mp3tag for key in ( 'TPE1', 'TALB' )]):
            return None
        album = max(mp3tag['TALB'].text).strip( )
        artist = max(mp3tag['TPE1'].text).strip( )
    else:
        return None
    if len(album) == 0:
        return None
    if len(artist) == 0:
        return None
    return ( artist, album )

def _get_album_prifile( prifile ):
    if os.path.basename( prifile ).endswith( '.mp3' ):
        mp3tag = mutagen.mp3.MP3( prifile )
        if not all ([ key in mp3tag for key in ( 'TPE1', 'TALB' )]):
            return None
        album = max(mp3tag['TALB'].text).strip( )
        return ( prifile, album )
    elif os.path.basename( prifile ).endswith( '.m4a' ):
        mp4tag = mutagen.mp4.MP4( prifile )
        if '\xa9ART' not in mp4tag: return None
        album = max( mp4tag['\xa9ART'] ).strip( )
        return ( prifile, album )
    else: return None

def get_summary_data_music_remote(
    token, fullURL = 'http://localhost:32400' ):
    libraries_dict = plexcore.get_libraries( token, fullURL = fullURL, do_full = True )
    if libraries_dict is None: return None
    keynums = set(filter(lambda keynum: libraries_dict[ keynum ][ 1 ] == 'artist', libraries_dict ) )
    if len( keynums ) == 0: return None
    sinceDate = plexcore.get_current_date_newsletter( )
    datas = list(map(lambda keynum: plexcore.get_library_stats( keynum, token, fullURL = fullURL ), keynums))
    mainstring = 'There are %d songs made by %d artists in %d albums.' % (
        sum(list(map(lambda data: data[ 'num_songs' ], datas))),
        sum(list(map(lambda data: data[ 'num_artists' ], datas))),
        sum(list(map(lambda data: data[ 'num_albums' ], datas))))
    sizestring = 'The total size of music media is %s.' % get_formatted_size(
        sum(list(map(lambda data: data[ 'totsize' ], datas))))
    durstring = 'The total duration of music media is %s.' % get_formatted_duration(
        sum(list(map(lambda data: data[ 'totdur' ], datas))))
    if sinceDate is not None:
        datas_since = list(filter(
            lambda data_since: data_since[ 'num_songs' ] > 0,
            map(lambda keynum: plexcore.get_library_stats(
                keynum, token, fullURL = fullURL, sinceDate = sinceDate ), keynums ) ) )
        if len( datas_since ) != 0:
            num_songs_since = sum(list(map(lambda data_since: data_since[ 'num_songs' ], datas_since)))
            num_artists_since = sum(list(map(lambda data_since: data_since[ 'num_artists' ], datas_since)))
            num_albums_since = sum(list(map(lambda data_since: data_since[ 'num_albums' ], datas_since)))
            totsize_since = sum(list(map(lambda data_since: data_since[ 'totsize'], datas_since)))
            totdur_since = sum(list(map(lambda data_since: data_since[ 'totdur' ], datas_since)))
            mainstring_since = ' '.join([
                'Since %s, I have added %d songs made by %d artists in %d albums.' % (
                    sinceDate.strftime( '%B %d, %Y' ),
                    num_songs_since, num_artists_since, num_albums_since ),
                #
                'The total size of music media I added is %s.' %
                get_formatted_size( totsize_since ),
                #
                'The total duration of music media I added is %s.' %
                get_formatted_duration( totdur_since ) ] )
            musicstring = ' '.join([ mainstring, sizestring, durstring, mainstring_since ])
            return musicstring
    musicstring = ' '.join([ mainstring, sizestring, durstring ])
    return musicstring

def get_summary_data_television_remote(
        token, fullURL = 'http://localhost:32400' ):
    libraries_dict = plexcore.get_libraries( token, fullURL = fullURL, do_full = True )
    if libraries_dict is None: return None
    keynums = set(filter(lambda keynum: libraries_dict[ keynum ][ 1 ] == 'show', libraries_dict ) )
    if len( keynums ) == 0: return None
    #
    sinceDate = plexcore.get_current_date_newsletter( )
    datas = list(map(lambda keynum: plexcore.get_library_stats( keynum, token, fullURL = fullURL ),
                     keynums))
    sizestring = 'The total size of TV media is %s.' % ( 
        get_formatted_size( sum(list(map(lambda data: data[ 'totsize' ], datas)))))
    durstring = 'The total duration of TV media is %s.' % (
        get_formatted_duration( sum(list(map(lambda data: data[ 'totdur' ], datas)))))
    mainstring = 'There are %d TV episodes in %d TV shows.' % (
        sum(list(map(lambda data: data[ 'num_tveps' ], datas))),
        sum(list(map(lambda data: data[ 'num_tvshows' ], datas))))
    if sinceDate is not None:
        datas_since = list(filter(
            lambda data_since: data_since[ 'num_tveps' ] > 0,
            map(lambda keynum: plexcore.get_library_stats(
                keynum, token, fullURL = fullURL, sinceDate = sinceDate ), keynums) ) )
        if len( datas_since ) > 0:
            mainstring_since = ' '.join([
                'Since %s, I have added %d TV files in %d TV shows.' % (
                    sinceDate.strftime('%B %d, %Y'),
                    sum(list(map(lambda data_since: data_since[ 'num_tveps' ], datas_since))),
                    sum(list(map(lambda data_since: data_since[ 'num_tvshows' ], datas_since)))),
                'The total size of TV media I added is %s.' %
                get_formatted_size(
                    sum(list(map(lambda data_since: data_since[ 'totsize' ], datas_since)))),
                'The total duration of TV media I added is %s.' %
                get_formatted_duration(
                    sum(list(map(lambda data_since: data_since[ 'totdur' ], datas_since)))) ])
            tvstring = ' '.join([ mainstring, sizestring, durstring, mainstring_since ])
            return tvstring
    tvstring = ' '.join([ mainstring, sizestring, durstring ])
    return tvstring

def get_summary_data_movies_remote( token, fullURL = 'http://localhost:32400' ):
    libraries_dict = plexcore.get_libraries( token, fullURL = fullURL )
    if libraries_dict is None: return None
    keynums = set(filter(lambda keynum: libraries_dict[ keynum ][ 1 ] == 'movie', libraries_dict ) )
    if len( keynums ) == 0: return None
    #
    sinceDate = plexcore.get_current_date_newsletter( )
    datas = list(map(lambda keynum: plexcore.get_library_stats( keynum, token, fullURL = fullURL ), keynums ) )
    num_movies_since = -1
    sorted_by_genres = { }
    sorted_by_genres_since = { }
    for data in datas:
        data_sorted_by_genre = data[ 'genres' ]
        for genre in data_sorted_by_genre:
            if genre not in sorted_by_genres:
                sorted_by_genres[ genre ] = data_sorted_by_genre[ genre ].copy( )
                continue
            sorted_by_genres[ genre ][ 'totum'  ] += data_sorted_by_genre[ genre ][ 'totnum'  ]
            sorted_by_genres[ genre ][ 'totdur' ] += data_sorted_by_genre[ genre ][ 'totdur'  ]
            sorted_by_genres[ genre ][ 'totsize'] += data_sorted_by_genre[ genre ][ 'totsize' ]
    
    if sinceDate is not None:
        datas_since = list(filter(
            lambda data_since: data_since[ 'num_movies' ] > 0,
            map(lambda keynum: plexcore.get_library_stats(
                keynum, token, fullURL = fullURL, sinceDate = sinceDate ), keynums ) ) )
        if len( datas_since ) != 0:
            num_movies_since = sum(list(map(lambda data_since: data_since[ 'num_movies' ], datas_since ) ) )
            categories_since = set(chain.from_iterable(map(lambda data_since: data_since[ 'genres' ].keys( ) ) ) )
            totsize_since = sum(list(map(lambda data_since: data_since[ 'totsize' ], datas_since ) ) )
            totdur_since = sum(list(map(lambda data_since: data_since[ 'totdur' ], datas_since ) ) )
            mainstring_since = ' '.join([
                'Since %s, I have added %d movies in %d categories.' % (
                    sinceDate.strftime('%B %d, %Y'), num_movies_since, len( categories_since ) ),
                #
                'The total size of movie media I added is %s.' %
                get_formatted_size( totsize_since ),
                #
                'The total duration of movie media I added is %s.' %
                get_formatted_duration( totdur_since ) ] )
            for data_since in datas_since:
                data_since_sorted_by_genre = data_since[ 'genres' ]
                for genre in data_since_sorted_by_genre:
                    if genre not in sorted_by_genres_since:
                        sorted_by_genres_since[ genre ] = data_since_sorted_by_genre[ genre ].copy( )
                        continue
                    sorted_by_genres_since[ genre ][ 'totum'  ] += data_since_sorted_by_genre[ genre ][ 'totnum'  ]
                    sorted_by_genres_since[ genre ][ 'totdur' ] += data_since_sorted_by_genre[ genre ][ 'totdur'  ]
                    sorted_by_genres_since[ genre ][ 'totsize'] += data_since_sorted_by_genre[ genre ][ 'totsize' ]
            
    categories = set( sorted_by_genres.keys( ) )
    num_movies = sum(list(map(lambda data: data[ 'num_movies' ], datas ) ) )
    totdur = sum(list(map(lambda data: data[ 'totdur' ], datas ) ) )
    totsize = sum(list(map(lambda data: data[ 'totsize' ], datas ) ) )
    mainstring = 'There are %d movies in %d categories.' % (
        num_movies, len( categories ) )
    sizestring = 'The total size of movie media is %s.' % get_formatted_size( totsize )
    durstring = 'The total duration of movie media is %s.' % get_formatted_duration( totdur )
    #
    ## get last 7 movies that I have added
    lastN_movies = plexcore.get_lastN_movies( 7, token, fullURL = fullURL )
    lastNstrings = [ '', '',
                     'Here are the last %d movies I have added.' % len( lastN_movies ),
                     '\\begin{itemize}' ]
    for title, year, date, url in lastN_movies:
        if url is None:
            lastNstrings.append( '\item %s (%d), added on %s.' %
                                 ( title, year, date.strftime( '%d %B %Y' ) ) )
        else:
            lastNstrings.append( '\item \href{%s}{%s (%d)}, added on %s.' %
                                 ( url, title, year, date.strftime( '%d %B %Y' ) ) )
    lastNstrings.append( '\end{itemize}' )
    lastNstring = '\n'.join( lastNstrings )
    finalstring = 'Here is a summary by category.'
    if sinceDate is not None and num_movies_since > 0:
        movstring = ' '.join([ mainstring, sizestring, durstring, mainstring_since,
                               lastNstring, finalstring ])
    else:
        movstring = ' '.join([ mainstring, sizestring, durstring, lastNstring, finalstring ])
    movstrings = [ movstring, ]
    catmovstrings = {}
    for cat in sorted( categories ):
        num_movies = sorted_by_genres[ cat ][ 'totnum'  ]
        totdur     = sorted_by_genres[ cat ][ 'totdur'  ]
        totsize    = sorted_by_genres[ cat ][ 'totsize' ]
        mainstring = 'There are %d movies in this category.' % num_movies
        sizestring = 'The total size of movie media here is %s.' % get_formatted_size( totsize )
        durstring = 'The total duration of movie media here is %s.' % get_formatted_duration( totdur )
        if sinceDate is not None and cat in sorted_by_genres_since and num_movies > 0:
            num_movies_since = sorted_by_genres_since[ cat ][ 'totnum'  ]
            totdur_since     = sorted_by_genres_since[ cat ][ 'totdur'  ]
            totsize_since    = sorted_by_genres_since[ cat ][ 'totsize' ]
            mainstring_since = ' '.join([
                'Since %s, I have added %d movies in this category.' %
                ( sinceDate.strftime( '%B %d, %Y' ), num_movies_since ),
                'The total size of movie media I added here is %s.' %
                get_formatted_size( totsize_since ),
                'The total duration of movie media I added here is %s.' %
                get_formatted_duration( totdur_since ) ] )
            movstring = ' '.join([ mainstring, sizestring, durstring, mainstring_since ])
        else:
            movstring = ' '.join([ mainstring, sizestring, durstring ])
        catmovstrings[ cat ] = movstring    
    movstrings.append( catmovstrings )    
    return movstrings
