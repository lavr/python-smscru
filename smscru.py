#!/usr/bin/python
import pysmscru
from optparse import OptionParser
import ConfigParser
import logging
import hashlib
import sys

smsc = None 

def send_message(phones, text):
    return smsc.send_sms(phones, text)

if __name__=="__main__":
    parser = OptionParser()
    parser.add_option("-c", "--config", type="string", dest="config", default='/etc/smscru.conf')
    parser.add_option("-f", "--sender", type="string", dest="sender", default='')
    parser.add_option("-v", "--debug", action="store_true", dest="debug", default=False)
    (options, args) = parser.parse_args()
    
    if options.debug:
        debuglevel = logging.DEBUG
    else:
        debuglevel = None
        
    logging.basicConfig(level=debuglevel)
    
    if args[0]=='md5':
        print hashlib.md5(args[1]).hexdigest()
        sys.exit(0)
    
    config = ConfigParser.ConfigParser()
    config.read(options.config)

    params = {}
    for section in ('common', 'http'):
        params.update(config.items(section))
        
    params['smtp'] = config.items('smtp')
        
    if options.sender:
        params['sender'] = options.sender
        
    smsc = pysmscru.SMSC(**params)
    
    if not args:
        raise "Usage: smscru.py [options] command params"

    if args[0] in ['msg', 'send-message']:
        print send_message(phones=args[1], text=args[2] )
