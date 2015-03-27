
WIKI_DIR=".mini-wiki.d"

import os
import string
import re

def recursive_lookup(name):
	path = os.getcwd()

	while path:
		lookup = path + "/" + name
		if os.path.isdir( lookup ):
			return lookup
		else:
			# recursively look up the current directory structure
			last_segment = path.rfind("/")
			path = path[:last_segment]

	return None


class MWiki(object):

	VALID_CHARACTERS = "@_-:^|~%s%s" % (string.ascii_letters, string.digits)
	LINK_REGEX = re.compile("#([" + re.escape(VALID_CHARACTERS) + "]+)")

	@staticmethod
	def create_wiki(path):
		path = path + "/" + WIKI_DIR
		if os.path.isdir(path):
			raise Error("directory already exists")
		os.mkdirs(path) # create parent directories as required
		return MWiki(path)


	@staticmethod
	def find_wiki():
		path = recursive_lookup(WIKI_DIR)
		if path:
			return MWiki(path)
		return None


	def __init__(self, wiki_dir):
		if wiki_dir[0] != "/":
			wiki_dir = os.getcwd() + "/" + wiki_dir
		self.dir = wiki_dir


	def clean_name(self, name):
		valid_letters = [ x for x in name if x in MWiki.VALID_CHARACTERS ]
		return "".join( valid_letters )


	def path(self, entry):
		return self.dir + "/" + self.clean_name(entry)


	def entries(self):
		files = os.listdir(self.dir)
		not_hidden = []
		# hidden files are configuration for MWiki
		for f in files:
			if f[0] != ".":
				not_hidden.append(f)
		return not_hidden


	def entry(self, item):
		content = None
		with open( self.dir + "/" + self.clean_name(item) ) as f:
			content = f.readlines()
		return "".join(content)


	def __iter__(self):
		for item in self.entries():
			yield (item, self.entry(item))


