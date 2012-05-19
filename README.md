python-smscru
=============

Python interface and cli for smsc.ru api

Installation:
-------------

	python setup.py install


API usage:
----------

    from pysmscru import SMSC

    smsc = SMSC(login=LOGIN, password=PASSWORD, sender=DEFAULT_SENDER)
    
    result = smsc.send_sms(['79169999999',], "Hello, world!")
    
    print result


CLI usage:
----------

Copy smscru.conf.example to /etc/smscru.conf and set your login and password.

	$ smscpy.py send 79169999999 "Hello, world!"
	
	

