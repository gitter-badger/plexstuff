import os, requests, json, sys
from functools import reduce
from sqlalchemy import Column, String

_mainDir = reduce(lambda x,y: os.path.dirname( x ), range( 2 ),
                  os.path.abspath( __file__ ) )
sys.path.append( _mainDir )

from plexcore import session, create_all, PlexConfig, Base
from sqlalchemy import String, Column

class ShowsToExclude( Base ): # these are shows you want to exclude
    """
    This SQLAlchemy_ ORM class contains the list of shows to exclude from analysis. These shows must exist on the Plex_ server. Stored into the ``showstoexclude`` table in the SQLite3_ configuration database.

    Attributes:
        show: the show, that exists on the Plex_ server, to exclude from analysis and update.

    .. _TVDB: https://api.thetvdb.com/swagger
    .. _SQLAlchemy: https://www.sqlalchemy.org
    .. _Plex: https://plex.tv
    .. _SQLite3: https://www.sqlite.org/index.html
    """
    
    #
    ## create the table using Base.metadata.create_all( _engine )
    __tablename__ = 'showstoexclude'
    __table_args__ = { 'extend_existing': True }
    show = Column( String( 65536 ), index = True, primary_key = True )

#
## commit all tables (implicit check on whether in READTHEDOCS variable is set
create_all( )
    
def save_tvdb_api( username: str, apikey: str, userkey: str, verify = True ):
    """
    Saves the information on the TVDB_ API access into the ``tvdb`` configuration service in the ``plexconfig`` table. Details of how to set up the configuration in :ref:`TVDB API configuation <The Television Database (TVDB) API>`, which uses ``plex_config_gui.py``.

    :param str username: the TVDB_ API username.
    :param str apikey: the TVDB_ API key.
    :param str userkey: the TVDB_ API user key.
    :param bool verify: optional argument, whether to verify SSL connections. Default is ``True``.

    :returns: a satus :py:class:`string <str>`. If successful, returns ``"SUCCESS"``. If unsuccessful, returns ``"FAILURE, COULD NOT SAVE TVDB API STUFF"``.
    :rtype: str
    """
    #
    ## first check if works
    isValid = check_tvdb_api( username, apikey, userkey, verify = verify )
    if not isValid: return 'FAILURE, COULD NOT SAVE TVDB API STUFF'
    query = session.query( PlexConfig ).filter( PlexConfig.service == 'tvdb' )
    val = query.first( )
    if val is not None:
        session.delete( val )
        session.commit( )
    newval = PlexConfig( service = 'tvdb',
                         data = {
                             'apikey' : apikey,
                             'username' : username,
                             'userkey' : userkey } )
    session.add( newval )
    session.commit( )
    return 'SUCCESS'

def check_tvdb_api( username, apikey, userkey, verify = True ) -> bool:
    token = get_token( verify = verify,
                       data = {  'apikey' : apikey,
                                 'username' : username,
                                 'userkey' : userkey } )
    if token is None: return False
    return True

def get_tvdb_api( ) -> dict:
    """
    Returns the :py:class:`dictionary <dict>` of TVDB_ API credentials (see  :ref:`TVDB API configuation <The Television Database (TVDB) API>`), taken from the ``tvdb`` configuration service in the ``plexconfig`` table. The form of the dictionary is,

    .. code-block:: python

       {
         'username' : USERNAME, # the TVDB API user name
         'apikey'   : APIKEY,   # the TVDB API key
         'userkey'  : USERKEY   # THE TVDB API user key
       }

    :returns: the :py:class:`dictionary <dict>` of TVDB_ API credentials.
    :rtype: dict
    :raises: ValuerError: if the TVDB_ API credentials are not found in the ``plexconfig`` table.
    
    """
    query = session.query( PlexConfig ).filter( PlexConfig.service == 'tvdb' )
    val = query.first( )
    if val is None:
        raise ValueError("ERROR, NO TVDB API CREDENTIALS FOUND")
    data = val.data
    return { 'username' : data['username'],
             'apikey' : data['apikey'],
             'userkey' : data['userkey'] }

def get_token( verify: bool = True, data = None ) -> str:
    """
    Returns the TVDB_ API token that allows access to the TVDB_ database. If there are errors, then returns :py:class:`None`.

    :param bool verify: optional argument, whether to verify SSL connections. Default is ``True``.
    :param dict data: optional argument. If provided, must be a dictionary containing the TVDB_ API credentials as described in :py:meth:`get_tvdb_api( ) <plextvdb.plextvdb.get_tvdb_api>`. Otherwise, returns the dictionary returned by :py:meth:`get_tvdb_api( ) <plextvdb.plextvdb.get_tvdb_api>`.

    :returns: the TVDB_ API :py:class:`string <str>` token, otherwise returns :py:class:`None` if there are errors.
    :rtype: str
    """
    if data is None:
        try: data = get_tvdb_api( )
        except: return None
    headers = { 'Content-Type' : 'application/json' }
    response = requests.post( 'https://api.thetvdb.com/login',
                              data = json.dumps( data ),
                              verify = verify, headers = headers )
    if response.status_code != 200: return None
    return response.json( )[ 'token' ]

def refresh_token( token: str, verify: bool = True ):
    """
    Refreshes the TVDB_ API token.

    :param str token: a previous valid TVDB_ API access token.
    :param bool verify:  optional argument, whether to verify SSL connections. Default is ``True``.
    :returns: a new TVDB_ API :py:class:`string <str>` token. If there are others, returns :py:class:`None`.
    :rtype: str
    """
    headers = { 'Content-Type' : 'application/json',
                'Authorization' : 'Bearer %s' % token }
    response = requests.get( 'https://api.thetvdb.com/refresh_token',
                             headers = headers, verify = verify )
    if response.status_code != 200: return None
    return response.json( )['token']
