# -*- coding: utf-8 -*-
#------------------------------------------------------------
# Download Tools
# Based on the code from VideoMonkey XBMC Plugin
#------------------------------------------------------------
# pelisalacarta 4
# Copyright 2015 tvalacarta@gmail.com
#
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
#------------------------------------------------------------
# This file is part of pelisalacarta 4.
#
# pelisalacarta 4 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pelisalacarta 4 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pelisalacarta 4.  If not, see <http://www.gnu.org/licenses/>.
#------------------------------------------------------------
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os
import base64
import zipfile
import tempfile
from email.message import Message




def mail(to, subject, text):
   msg = MIMEMultipart()
   mailuser=base64.b64decode('cGVsaXNhbGFjYXJ0YS5sb2dAZ21haWwuY29t')
   msg['From'] = mailuser
   msg['To'] = to
   msg['Subject'] = subject
   smtpport='587'
   smtpserver='smtp.gmail.com'  
   mailpasswd=base64.b64decode('MjMwMTE5NzM=')
   
   
   msg.attach(MIMEText(text, 'plain'))
   
   mailServer = smtplib.SMTP(smtpserver, int(smtpport))
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(mailuser, mailpasswd)
   mailServer.set_debuglevel(True)
   mailServer.sendmail(mailuser, to, msg.as_string())
   # Should be mailServer.quit(), but that crashes...
   mailServer.close()
   

def send_file_zipped(to, subject, text, attach):
    zf = tempfile.TemporaryFile(prefix='mail', suffix='.zip')
    zip = zipfile.ZipFile(zf, 'w')
    zip.write(attach)
    zip.close()
    zf.seek(0)
    mailuser=base64.b64decode('cGVsaXNhbGFjYXJ0YS5sb2dAZ21haWwuY29t')
    smtpserver='smtp.gmail.com'
    smtpport='587'
    mailpasswd=base64.b64decode('MjMwMTE5NzM=')
    
    # Create the message
    themsg = MIMEMultipart()
    themsg['Subject'] = subject
    themsg['To'] = to
    themsg['From'] = mailuser
    themsg.preamble = 'I am not using a MIME-aware mail reader.\n'
    msg = MIMEBase('application', 'zip')
    msg.set_payload(zf.read())
    Encoders.encode_base64(msg)
    msg.add_header('Content-Disposition', 'attachment', 
                   filename=attach + '.zip')
    themsg.attach(msg)
    themsg = themsg.as_string()

    # send the message
    smtp = smtplib.SMTP(smtpserver, int(smtpport))
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(to, mailpasswd)
    smtp.sendmail(mailuser, to, themsg)
    smtp.close()   

    	  
    	  
