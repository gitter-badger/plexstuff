import os, sys, titlecase, datetime, pypandoc
import json, re, urllib, time, glob, multiprocessing
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from bs4 import BeautifulSoup

from plexcore import plexcore, mainDir, QDialogWithPrinting
from plexemail import plexemail, plexemail_basegui, emailAddress, emailName
from plexemail import get_email_contacts_dict

def _checkValidLaTeX( myString ):
    try:
        mainHTML = BeautifulSoup(
            pypandoc.convert_text( myString, 'html', format = 'latex',
                                   extra_args = [ '-s' ] ), 'lxml' )
        return True, mainHTML.prettify( )
    except RuntimeError:
        return False, None

class QLineCustom( QLineEdit ):
    def __init__( self ):
        super( QLineCustom, self ).__init__( )
        
    def returnPressed( ):
        self.setText( titlecase.titlecase( str( self.text( ) ).strip( ) ) )

class PlexEmailMyGUI( QDialogWithPrinting ):
    def __init__( self, token, doLarge = False, verify = True ):
        super( PlexEmailMyGUI, self ).__init__( None, )
        self.resolution = 1.0
        self.verify = verify
        if doLarge:
            self.resolution = 2.0
        for fontFile in glob.glob( os.path.join( mainDir, 'resources', '*.ttf' ) ):
            QFontDatabase.addApplicationFont( fontFile )
        self.setStyleSheet("""
        QWidget {
        font-family: Consolas;
        font-size: %d;
        }""" % ( int( 11 * self.resolution ) ) )
        self.setWindowTitle( 'SEND CUSTOM EMAIL' )
        qf = QFont( )
        qf.setFamily( 'Consolas' )
        qf.setPointSize( int( 11 * self.resolution ) )
        qfm = QFontMetrics( qf )
        self.mainEmailCanvas = QTextEdit( )
        self.mainEmailCanvas.setTabStopWidth( 2 * qfm.width( 'A' ) )
        self.subjectLine = QLineCustom( )
        self.statusLabel = QLabel( )
        self.checkLaTeXButton = QPushButton( '\n'.join('PRINT EMAIL'.split( ) ) )
        self.emailListButton = QPushButton( '\n'.join( 'PLEX GUESTS'.split( ) ) )
        self.emailSendButton = QPushButton( '\n'.join( 'SEND EMAIL'.split( ) ) )
        self.emailTestButton = QPushButton( '\n'.join( 'TEST EMAIL'.split( ) ) )
        self.pngAddButton = QPushButton( 'ADD PNGS' )
        self.emailSendButton.setEnabled( False )
        self.emailTestButton.setEnabled( False )
        #
        self.emails_array = get_email_contacts_dict(
            plexcore.get_mapped_email_contacts(
                token, verify = self.verify ), verify = self.verify )
        self.emails_array.append(( emailName, emailAddress ) )
        #
        self.pngWidget = plexemail_basegui.PNGWidget( self )
        self.pngWidget.hide( )
        #
        myLayout = QVBoxLayout( )
        self.setLayout( myLayout )
        #
        topWidget = QWidget( )
        topLayout = QGridLayout( )
        topWidget.setLayout( topLayout )
        topLayout.addWidget( self.checkLaTeXButton, 0, 0, 1, 2 )
        topLayout.addWidget( self.emailListButton, 0, 2, 1, 2 )
        topLayout.addWidget( self.emailSendButton, 0, 4, 1, 2 )
        topLayout.addWidget( self.emailTestButton, 0, 6, 1, 2 )
        topLayout.addWidget( self.pngAddButton, 1, 0, 1, 8 )
        topLayout.addWidget( QLabel( 'SUBJECT:' ), 2, 0, 1, 3 )
        topLayout.addWidget( self.subjectLine, 2, 2, 1, 6 )
        myLayout.addWidget( topWidget )
        #
        myLayout.addWidget( self.mainEmailCanvas )
        myLayout.addWidget( self.statusLabel )
        #
        if len( self.emails_array ) == 0:
            self.emailListButton.setEnabled( False )
            self.emailTestButton.setEnabled( False )
        self.emailListButton.clicked.connect( self.showEmails )
        self.checkLaTeXButton.clicked.connect( self.checkLaTeX )
        self.emailSendButton.clicked.connect( self.sendEmail )
        self.emailTestButton.clicked.connect( self.testEmail )
        self.pngAddButton.clicked.connect( self.addPNGs )
        #
        quitAction = QAction( self )
        quitAction.setShortcuts([ 'Ctrl+Q', 'Esc' ])
        quitAction.triggered.connect( sys.exit )
        self.addAction( quitAction )
        #
        self.setFixedWidth( 55 * qfm.width( 'A' ) )
        self.setFixedHeight( 33 * qfm.height( ) )
        self.show( )

    def contextMenuEvent( self, event ):
        menu = QMenu( self )
        screenGrabAction = QAction( 'screenGrab', menu )
        screenGrabAction.triggered.connect( self.screenGrab )
        menu.addAction( screenGrabAction )
        menu.popup( QCursor.pos( ) )

    def addPNGs( self ):
        self.pngWidget.show( )
        # self.pngAddButton.setEnabled( False )

    def showEmails( self ):
        qdl = QDialog( self )
        qdl.setModal( True )
        qdl.setWindowTitle( 'PLEX MAPPED GUEST EMAILS' )
        myLayout = QVBoxLayout( )
        qdl.setLayout( myLayout )
        qte = QTextEdit( qdl )
        myLayout.addWidget( qte )
        qte.setReadOnly( True )
        qf = QFont( )
        qf.setFamily( 'Consolas' )
        qf.setPointSize( int( 11 * self.resolution ) )
        qfm = QFontMetrics( qf )
        lines = [ ]
        for idx, ( name, email ) in enumerate(
                sorted( self.emails_array,
                        key = lambda tup: tup[0].split()[-1] ) ):
            if name is None:
                lines.append( '%02d: %s' % ( idx + 1, email ) )
            else:
                lines.append( '%02d: %s <%s>' % ( idx + 1, name, email ) )
        qdl.setFixedWidth( 1.50 * max(map(lambda line: qfm.width(line.strip()), lines)))
        qdl.setFixedHeight( 1.15 * len( self.emails_array ) * qfm.height( ) )
        qte.setPlainText( '\n'.join( lines ) )
        qdl.show( )
        result = qdl.exec_( )

    def checkLaTeX( self ):
        self.statusLabel.setText( '' )
        myStr = self.mainEmailCanvas.toPlainText( ).strip( )
        if len( myStr ) == 0:
            self.emailSendButton.setEnabled( False )
            self.statusLabel.setText( 'INVALID LaTeX' )
            return
        mainText = r"""
        \documentclass{article}
        \usepackage{amsmath, amsfonts, graphicx, hyperref}
        
        \begin{document}
        
        Hello Friend,

        %s
        
        \end{document}
        """ % myStr
        html = plexcore.latexToHTML( mainText )
        if html is None:
            self.emailSendButton.setEnabled( False )
            self.emailTestButton.setEnabled( False )
            self.statusLabel.setText( 'INVALID LaTeX' )
            return
        html = plexcore.processValidHTMLWithPNG(
            html, self.pngWidget.getAllDataAsDict( ),
            doEmbed = True )
        self.emailSendButton.setEnabled( True )
        self.emailTestButton.setEnabled( True )
        self.statusLabel.setText( 'VALID LaTeX' )
        #
        qdl = QDialog( self )
        qdl.setWindowTitle( 'HTML EMAIL BODY' )
        qdl.setModal( True )
        qte = QTextEdit( qdl )
        qte.setReadOnly( True )
        qdlLayout = QVBoxLayout( )
        qdl.setLayout( qdlLayout )
        qdlLayout.addWidget( qte )
        qf = QFont( )
        qf.setFamily( 'Consolas' )
        qf.setPointSize( int( 11 * self.resolution ) )
        qfm = QFontMetrics( qf )
        qdl.setFixedWidth( 85 * qfm.width( 'A' ) )
        qdl.setFixedHeight( 550 )
        qte.setHtml( html )
        qdl.show( )
        def _close( ):
            qdl.close( )
        closeAction = QAction( self )
        closeAction.setShortcuts( [ 'Esc' ] )
        closeAction.triggered.connect( _close )
        #
        ##
        result = qdl.exec_( )

    def getHTML( self ):
        mainText = r"""
        \documentclass{article}
        \usepackage{amsmath, amsfonts, graphicx, hyperref}
        
        \begin{document}
        
        Hello Friend,

        %s
        
        \end{document}
        """ % self.mainEmailCanvas.toPlainText( ).strip( )
        status, html = _checkValidLaTeX( mainText )
        html = plexcore.processValidHTMLWithPNG( html, self.pngWidget.getAllDataAsDict( ) )
        return status, html

    def toHTML( self, filename ):
        self.statusLabel.setText( 'TO HTML FILE' )
        status, html = self.getHTML( )
        
    def sendEmail( self ):
        self.statusLabel.setText( 'SENDING EMAIL' )
        status, html = self.getHTML( )
        if not status:
            self.emailSendButton.setEnabled( False )
            self.statusLabel.setText( 'INVALID LaTeX' )
            return
        subject = titlecase.titlecase( str( self.subjectLine.text( ) ).strip( ) )
        if len(subject) == 0:
            subject = 'GENERIC SUBJECT FOR %s' % datetime.datetime.now( ).strftime( '%B-%m-%d' )
        for name, email in self.emails_array:
            plexemail.send_individual_email_full( html, subject, email, name = name, )
        self.statusLabel.setText( 'EMAILS SENT' )

    def testEmail( self ):
        self.statusLabel.setText( 'SENDING EMAIL TO %s.' % emailAddress.upper( ) )
        status, html = self.getHTML( )
        if not status:
            self.emailSendButton.setEnabled( False )
            self.statusLabel.setText( 'INVALID LaTeX' )
            return
        subject = titlecase.titlecase( str( self.subjectLine.text( ) ).strip( ) )
        if len(subject) == 0:
            subject = 'GENERIC SUBJECT FOR %s' % datetime.datetime.now( ).strftime( '%B-%m-%d' )
        #
        plexemail.send_individual_email_full(
            html, subject, emailAddress, name = emailName )
        self.statusLabel.setText( 'EMAILS SENT TO %s.' % emailAddress.upper( ) )

if __name__=='__main__':
    app = QApplication([])
    
