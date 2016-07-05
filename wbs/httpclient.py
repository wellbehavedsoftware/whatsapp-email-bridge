from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib

def urlencode (data):

	if isinstance (data, str):
		return data

	elif isinstance (data, unicode):
		return data.encode ("utf-8")

	elif isinstance (data, dict):
		return urllib.urlencode (data)

	else:
		return "Cannot url encode %s" % type (data)

# ex: noet ts=4 filetype=yaml
