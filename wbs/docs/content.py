from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import collections
import markdown
import os
import yaml

class WbsDocsContent ():

	def __init__ (self, master, content_path):

		self.master = master

		self.markdown = markdown.Markdown (
			extensions = [
				"codehilite",
				"partial_gfm",
				"meta",
			])

		self.content = (
			self.load_section (
				None,
				content_path,
				""))

	def load_section (self, section_parent, section_path, section_name):

		# load section index

		print (
			"Load section '%s' (%s)" % (
				section_name,
				section_path))

		index_path = "%s/index" % section_path

		with codecs.open (
			filename = index_path,
			encoding = "utf-8") \
		as file_handle:

			index_markdown = (
				file_handle.read ())

		index_html = (
			self.markdown.convert (
				index_markdown))

		index_meta = self.markdown.Meta

		section = WbsDocsSection (

			name = section_name,
			parent = section_parent,

			meta = index_meta,
			markdown = index_markdown,
			html = index_html,

		)

		# load section children

		for entry_name in sorted (os.listdir (section_path)):

			if entry_name == "index":
				continue

			entry_path = "%s/%s" % (section_path, entry_name)

			if os.path.isdir (entry_path):

				section.children [entry_name] = (
					self.load_section (
						section,
						entry_path,
						entry_name,
					)
				)

			elif os.path.isfile (entry_path):

				section.children [entry_name] = (
					self.load_document (
						section,
						entry_path,
						entry_name,
					)
				)

			else:

				raise Exception ()

		# return

		return section

	def load_document (self, document_parent, document_path, document_name):

		# load document

		with codecs.open (
			filename = document_path,
			encoding = "utf-8") \
		as file_handle:

			document_markdown = (
				file_handle.read ())

		document_html = self.markdown.convert (document_markdown)
		document_meta = self.markdown.Meta

		document = WbsDocsDocument (

			name = document_name,
			parent = document_parent,

			meta = document_meta,
			markdown = document_markdown,
			html = document_html,

		)

		# return

		return document

	def find_entry (self, content_name):

		if content_name == "":
			return self.content

		current_entry = self.content

		for part in content_name.split ("/"):

			if not part in current_entry.children:
				return None

			current_entry = (
				current_entry.children [part])

		return current_entry

class WbsDocsSection ():

	__slots__ = [

		"name",
		"parent",
		"children",

		"meta",
		"title",

		"markdown",
		"html",

	]

	def __init__ (

		self,

		name,
		parent,

		meta,
		markdown,
		html,

	):

		self.type = "section"
		self.parent = parent
		self.children = collections.OrderedDict ()

		self.name = name

		if parent and parent.name:
			self.full_name = "%s/%s" % (parent.full_name, name)
		else:
			self.full_name = name

		self.meta = meta
		self.long_title = meta ["long-title"] [0]
		self.short_title = meta ["short-title"] [0]
		self.description = meta.get ("description", [""]) [0]

		self.markdown = markdown
		self.html = html

	def simple (self):

		return dict (

			type = "section",
			name = self.name,
			full_name = self.full_name,

			long_title = self.long_title,
			short_title = self.short_title,

			children = [
				child.simple ()
				for child in self.children.values ()
			],

		)

	def chain (self):

		if self.parent:
			parent_chain = self.parent.chain ()
		else:
			parent_chain = list ()

		parent_chain.append (self)

		return parent_chain

	def can_view (self, groups):

		require_group = (
			self.meta.get ("require-group", [ None ]) [0])

		if require_group and not require_group in groups:
			return False

		if not self.parent:
			return True

		return self.parent.can_view (groups)

class WbsDocsDocument ():

	__slots__ = [

		"type",
		"name",
		"parent",
		"children",

		"meta",
		"markdown",
		"html",

	]

	def __init__ (

		self,

		name,
		parent,

		meta,
		markdown,
		html,

	):

		self.type = "document"
		self.parent = parent
		self.children = collections.OrderedDict ()

		self.name = name
		self.full_name = "%s/%s" % (parent.full_name, name)

		self.meta = meta

		self.long_title = meta ["long-title"] [0]
		self.short_title = meta ["short-title"] [0]
		self.description = meta.get ("description", [""]) [0]

		self.markdown = markdown
		self.html = html

	def simple (self):

		return dict (

			type = "document",
			name = self.name,

			long_title = self.long_title,
			short_title = self.short_title,

		)

	def chain (self):

		if self.parent:
			parent_chain = self.parent.chain ()
		else:
			parent_chain = list ()

		parent_chain.append (self)

		return parent_chain

	def can_view (self, groups):

		require_group = (
			self.meta.get ("require-group", [ None ]) [0])

		if require_group and not require_group in groups:
			return False

		if not self.parent:
			return True

		return self.parent.can_view (groups)

# ex: noet ts=4 filetype=python
