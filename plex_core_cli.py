#!/usr/bin/env python3

from plexcore import plexcore, session
from plexemail import get_email_contacts_dict
from optparse import OptionParser
import requests

def _print_format_names( plex_emails, header_name = 'PLEX' ):
    print( '\n'.join([
                      'YOU HAVE %d %s FRIENDS' % ( len( plex_emails ), header_name.upper( ) ),
                      '---' ] ) )
    if len( plex_emails ) == 0: return
    email_contacts_dict = get_email_contacts_dict( plex_emails )
    num_with_names = len( list( filter( lambda tup: tup[0] is not None, email_contacts_dict ) ) )
    num_wo_names = len( email_contacts_dict ) - num_with_names
    print ('\n'.join([ '%d HAVE FOUND NAMES, %d DO NOT HAVE FOUND NAMES' % (
        num_with_names, num_wo_names ), '' ]) )
    if num_with_names != 0:
        if num_with_names == 1:
            print( '\n'.join([ '%d %s FRIEND WITH NAMES' % ( num_with_names, header_name.upper( ) ), '' ]))
        else:
            print( '\n'.join([ '%d %s FRIENDS WITH NAMES' % ( num_with_names, header_name.upper( ) ), '' ]))
        #
        max_len_name = max(map(lambda tup: len( tup[ 0 ] ),
                               filter(lambda tup: tup[0] is not None, email_contacts_dict ) ) )
        num, rem = divmod( max_len_name, 5 )
        if rem != 0 or num == 0: num += 1
        num_spac = 5 * num
        #
        max_len_email = max(map(lambda tup: len( tup[ 1 ] ),
                                filter(lambda tup: tup[0] is not None, email_contacts_dict ) ) )
        num, rem = divmod( max_len_email, 5 )
        if rem != 0 or num == 0: num += 1
        num_spac_email = 5 * num            
        #    
        str_format_name = '%%-%02ds' % num_spac
        str_format_email = '%%-%02ds' % num_spac_email
        fmt_line = '%s  |  %s' % ( str_format_name, str_format_email )
        print( fmt_line % ( 'NAME', 'EMAIL' ) )
        print( ''.join([
                    ''.join( ['-'] * ( num_spac + 2 ) ), '|',
                    ''.join( ['-'] * ( num_spac_email + 2 ) ) ]) )
        for name, email in sorted(filter(lambda tup: tup[0] is not None, email_contacts_dict ), key = lambda tup: tup[0].split()[-1] ):
            print( fmt_line % ( name, email ) )
        if num_wo_names != 0: print('\n')
        
    if num_wo_names != 0:
        if num_wo_names == 1:
            print( '\n'.join([ '%d %s FRIEND WITHOUT NAMES' % ( num_wo_names, header_name.upper( ) ), '' ]))
        else:
            print( '\n'.join([ '%d %s FRIENDS WITHOUT NAMES' % ( num_wo_names, header_name.upper( ) ), '' ]))
            
        max_len_email = max(map(lambda tup: len( tup[ 1 ] ),
                                filter(lambda tup: tup[0] is None, email_contacts_dict ) ) )
        num, rem = divmod( max_len_email, 5 )
        if rem != 0 or num == 0: num += 1
        num_spac_email = 5 * num
            
        str_format = '%%-%02ds' % num_spac_email
        print( str_format % 'EMAIL' )
        print( ''.join( ['-'] * num_spac_email ) )
        for _, email in sorted(filter(lambda tup: tup[0] is None, email_contacts_dict ), key = lambda tup: tup[1] ):
            print( str_format % email )

def main( ):
    parser = OptionParser( )
    parser.add_option( '--username', dest='username', type=str, action='store',
                      help = 'Your plex username.' )
    parser.add_option( '--password', dest='password', type=str, action='store',
                      help = 'Your plex password.' )
    parser.add_option( '--friends', dest='do_friends', action='store_true',
                      default = False,
                      help = 'Get list of guests of your Plex server.')
    parser.add_option( '--mappedfriends', dest='do_mapped_friends', action='store_true', default = False,
                      help = 'Get list of guests with mapping, of your Plex server.')
    parser.add_option( '--addmapping', dest='do_addmapping',
                      action = 'store_true', default = False,
                      help = 'If chosen, then add extra friends from Plex friends.' )
    parser.add_option( '--guestemail', dest='guest_email', action = 'store', type=str,
                      help = 'Name of the Plex guest email.' )
    parser.add_option( '--newemails', dest='new_emails', action = 'store', type = str,
                      help = 'Name of the new emails associated with the Plex guest email.')
    parser.add_option( '--replace_existing', dest='do_replace_existing', action = 'store_true', default = False,
                      help = 'If chosen, replace existing email to send newsletter to.')
    opts, args = parser.parse_args( )
    assert(len(list(
        filter(lambda tok: tok is True, (
            opts.do_friends, opts.do_addmapping,
            opts.do_mapped_friends ) ) ) ) == 1 )
    if any(map(lambda tok: tok is None, ( opts.username, opts.password ) ) ):
        var = plexcore.checkServerCredentials(
            doLocal = False, verify = False, checkWorkingServer = False )
        if var is None:
            print( 'COULD NOT FIND PLEX SERVER CREDENTIALS OR INVALID USERNAME/PASSWORD COMBO' )
            return
        _, token = var
    else:
        assert(all(map(lambda tok: tok is not None, ( opts.username, opts.password ) ) ) ), "must have both username and password"
        token = plexcore.getTokenForUsernamePassword( opts.username, opts.password, verify = False )
        if token is None:
            print( 'INVALID USERNAME/PASSWORD COMBO.' )
            return
        
    if opts.do_friends:
        plex_emails = sorted( set( plexcore.get_email_contacts( token, verify = False ) ) )
        _print_format_names( plex_emails, header_name = 'PLEX' )

    elif opts.do_mapped_friends:
        mapped_emails = sorted( set( plexcore.get_mapped_email_contacts( token, verify = True ) ) )
        _print_format_names( mapped_emails, header_name = 'MAPPED PLEX' )

    elif opts.do_addmapping:
        plex_emails = sorted( set( plexcore.get_email_contacts( token, verify = False ) ) )
        assert(all(map(lambda tok: tok is not None, ( opts.guest_email, opts.new_emails ) ) ) )
        assert( opts.guest_email in plex_emails )
        new_emails = sorted( set( map(lambda tok: tok.strip(), opts.new_emails.split(','))) )
        assert( len( set( new_emails ) & set( plex_emails ) ) == 0 )
        plexcore.add_mapping( opts.guest_email, plex_emails, new_emails,
                              opts.do_replace_existing )
        
if __name__=='__main__':
    main( )
