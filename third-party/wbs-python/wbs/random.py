from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import string

def generate_random (length, characters = string.ascii_lowercase):

	return "".join ([
		random.choice (characters)
		for _ in range (length)
	])

def generate_salt (length = 6):

	return generate_random (
		length,
		"".join ([
			string.ascii_letters,
			string.digits,
			"./",
		]))

def generate_mac_address (prefix = ""):

	ret = prefix

	while len (ret) < 17:
		ret += ":" + generate_random (2, "0123456789abcdef")

	if len (ret) > 17:
		raise Exception ()

	return ret

def generate_password ():

	return generate_random (20)

# ex: noet ts=4 filetype=yaml
