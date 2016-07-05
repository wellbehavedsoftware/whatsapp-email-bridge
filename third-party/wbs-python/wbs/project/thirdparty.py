from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import signal
import subprocess
import sys

try:

	import git
	import yaml

except ImportError:

	pass

import wbs.yamlx as yamlx
from wbs.output import log

def read_index ():

	return yamlx.load_data (
		"third-party/third-party-index")

def build (* names):

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.load ()
	third_party_setup.build (* names)

def fetch ():

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.load ()
	third_party_setup.fetch (* names)

def merge ():

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.load ()
	third_party_setup.merge (* names)

def pull (* names):

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.load ()
	third_party_setup.pull (* names)

def push (* names):

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.load ()
	third_party_setup.push (* names)

def update (* names):

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.load ()
	third_party_setup.update (* names)

class ThirdPartySetup (object):

	def __init__ (self):

		self.project_path = (
			os.path.abspath ("."))

		self.project_name = (
			os.path.basename (
				self.project_path))

		self.stashed = False

	def load (self):

		self.third_party_index = (
			read_index ())

		if os.path.exists (".git"):

			self.git_repo = (
				git.Repo ("."))

		else:

			self.git_repo = None

	def fetch (self, * names):

		log.notice (
			"About to fetch third party libraries")

		try:

			self.create_remotes ()
			self.fetch_remotes (* names)

			log.notice (
				"All done")

		except KeyboardInterrupt:

			log.notice (
				"Aborting due to user request")

	def update (self, * names):

		log.notice (
			"About to update third party libraries")

		try:

			self.stash_changes ()
			self.update_libraries (* names)

			log.notice (
				"All done")

		except KeyboardInterrupt:

			log.notice (
				"Aborting due to user request")

		finally:

			self.unstash_changes ()

	def pull (self, * names):

		log.notice (
			"About to pull third party libraries")

		try:

			self.create_remotes (* names)
			self.fetch_remotes (* names)
			self.stash_changes ()
			self.update_libraries (* names)

			log.notice (
				"All done")

		except KeyboardInterrupt:

			log.notice (
				"Aborting due to user request")

		finally:

			self.unstash_changes ()

	def push (self, * names):

		log.notice (
			"About to push third party libraries")

		try:

			self.stash_changes ()
			self.push_remotes (* names)

			log.notice (
				"All done")

		except KeyboardInterrupt:

			log.notice (
				"Aborting due to user request")

		finally:

			self.unstash_changes ()

	def build (self, * names):

		log.notice (
			"About to build third party libraries")

		self.pre_build_libraries (* names)

		try:

			self.stash_changes ()
			self.build_libraries (* names)

			log.notice (
				"All done")

		except KeyboardInterrupt:

			log.notice (
				"Aborting due to user request")

		finally:

			self.unstash_changes ()

	def merge (self, * names):

		log.notice (
			"About to merge third party libraries")

		try:

			self.stash_changes ()
			self.merge_libraries (* names)

			log.notice (
				"All done")

		except KeyboardInterrupt:

			log.notice (
				"Aborting due to user request")

		finally:

			self.unstash_changes ()

	def create_remotes (self, * names):

		remotes_index = dict ([
			(remote.name, remote)
			for remote
			in self.git_repo.remotes
		])

		for library_name, library_data \
		in self.third_party_index.items ():

			if names and library_name not in names:
				continue

			if library_name in remotes_index:
				continue

			with log.status (
				"Create missing remote for %s" % (
					library_name)):

				remotes_index [library_name] = (
					self.git_repo.create_remote (
						library_name,
						library_data ["url"]))

	def fetch_remotes (self, * names):

		for library_name, library_data \
		in self.third_party_index.items ():

			if names and library_name not in names:
				continue

			if "version" in library_data:

				with log.status (
					"Fetch remote: %s (%s)" % (
						library_name,
						library_data ["version"])):

					self.git_repo.remotes [library_name].fetch (
						"refs/tags/%s:refs/remotes/%s/%s" % (
							library_data ["version"],
							library_name,
							library_data ["version"]))

			elif "branch" in library_data:

				with log.status (
					"Fetch remote: %s (%s)" % (
						library_name,
						library_data ["branch"])):

					self.git_repo.remotes [library_name].fetch (
						"refs/heads/%s:refs/%s/%s" % (
							library_data ["branch"],
							library_name,
							library_data ["branch"]),
						no_tags = True)

			else:

				raise Exception ()

		log.notice (
			"Fetched %s remotes" % (
				len (self.third_party_index)))

	def push_remotes (self, * names):

		num_pushed = 0
		num_failed = 0

		for library_name, library_data \
		in self.third_party_index.items ():

			if names and library_name not in names:
				continue

			if "push" not in library_data:
				continue

			library_prefix = (
				"third-party/%s" % (
					library_name))

			try:

				with log.status (
					"Pushing changes for %s" % (
						library_name)):

					if library_data ["push"] == "simple":

						subprocess.check_call (
							[
								"git",
								"subtree",
								"push",
								"--prefix",
								library_prefix,
								library_name,
								library_data ["branch"],
								"--squash",
								"--message",
								"push changes from %s" % (
									self.project_name),
							],
							stderr = subprocess.STDOUT)

						subprocess.check_call (
							[
								"git",
								"subtree",
								"pull",
								"--prefix",
								library_prefix,
								library_name,
								library_data ["branch"],
								"--squash",
								"--message",
								"pull for push of %s" % (
									library_name),
							],
							stderr = subprocess.STDOUT)

					else:

						raise Exception ()

				num_pushed += 1

			except subprocess.CalledProcessError as error:

				log.notice (
					"Push failed!")

				log.output (
					error.output)

				num_failed += 1

		if num_failed:

			print (
				"Pushed %s libraries with %s failures" % (
					num_pushed + num_failed,
					num_failed))

		elif num_pushed:

			print (
				"Pushed %s libraries" % (
					num_pushed))

	def handle_interrupt (self, * arguments):

		log.notice (
			"Aborting...")

		self.interrupted = True

	def stash_changes (self):

		if not self.git_repo:
			return

		if self.stashed:
			return

		self.interrupted = False

		saved_signal = (
			signal.signal (
				signal.SIGINT,
				self.handle_interrupt))

		log.notice (
			"Stashing local changes")

		self.stashed_head_tree = (
			self.git_repo.head.commit.tree)

		self.stashed_index_tree = (
			self.git_repo.index.write_tree ())

		self.stashed_index_commit = (
			git.Commit.create_from_tree (
				self.git_repo,
				self.stashed_index_tree,
				"Stashed index"))

		self.stashed_index_tag = (
			git.Tag.create (
				self.git_repo,
				"wbs/stashed-index",
				self.stashed_index_commit,
				force = True))

		self.git_repo.git.add (
			"--all",
			"third-party")

		self.stashed_working_tree = (
			self.git_repo.index.write_tree ())

		self.stashed_working_commit = (
			git.Commit.create_from_tree (
				self.git_repo,
				self.stashed_working_tree,
				"Stashed working tree"))

		self.stashed_working_tag = (
			git.Tag.create (
				self.git_repo,
				"wbs/stashed-working",
				self.stashed_working_commit,
				force = True))

		self.git_repo.index.reset (
			working_tree = True)

		self.stashed = True

		signal.signal (
			signal.SIGINT,
			saved_signal)

		if self.interrupted:
			raise KeyboardInterrupt ()

	def unstash_changes (self):

		if not self.git_repo:
			return

		if not self.stashed:
			return

		log.notice (
			"Unstashing local changes")

		merged_working_index = (
			git.IndexFile.from_tree (
				self.git_repo,
				self.stashed_head_tree,
				self.stashed_working_tree,
				self.git_repo.head.commit.tree))

		self.git_repo.index.reset (
			merged_working_index.write_tree (),
			working_tree = True)

		merged_index = (
			git.IndexFile.from_tree (
				self.git_repo,
				self.stashed_head_tree,
				self.stashed_index_tree,
				self.git_repo.head.commit.tree))

		self.git_repo.index.reset (
			merged_index.write_tree ())

		self.stashed = False

	def update_libraries (self, * names):

		for library_name, library_data \
		in self.third_party_index.items ():

			if names and library_name not in names:
				continue

			self.update_library (
				library_name,
				library_data)

	def update_library (self, library_name, library_data):

		library_path = (
			"%s/third-party/%s" % (
				self.project_path,
				library_name))

		library_prefix = (
			"third-party/%s" % (
				library_name))

		if "version" in library_data:

			library_version = (
				library_data ["version"])

		elif "branch" in library_data:

			library_version = (
				library_data ["branch"])

		else:

			raise Exception ()

		if not os.path.isdir (
			library_path):

			log.notice (
				"First time import library: %s" % (
					library_name))

			subprocess.check_call ([
				"git",
				"subtree",
				"add",
				"--prefix",
				library_prefix,
				library_data ["url"],
				library_version,
				"--squash",
			])

		else:

			local_tree = (
				self.git_repo
					.head
					.commit
					.tree ["third-party"] [library_name])

			git_remote = (
				self.git_repo.remotes [
					library_name])

			remote_ref = (
				git_remote.refs [
					library_version])

			remote_commit = (
				remote_ref.commit)

			remote_tree = (
				remote_commit.tree)

			if local_tree == remote_tree:
				return

			library_version = (
				library_data.get (
					"version",
					library_data.get (
						"branch")))

			self.update_library_version (
				library_name,
				library_data,
				library_prefix,
				library_version,
				remote_commit)

	def update_library_version (
			self,
			library_name,
			library_data,
			library_prefix,
			library_version,
			remote_commit):

		try:

			with log.status (
				"Update library: %s" % (
					library_name)):

				output = (
					subprocess.check_output (
						[
							"git",
							"subtree",
							"merge",
							"--prefix", library_prefix,
							unicode (remote_commit),
							"--squash",
							"--message",
							"update %s to %s" % (
								library_name,
								library_version),
						],
						stderr = subprocess.STDOUT))

				if len (output):

					log.keep_status ()

					log.output (
						output)

		except subprocess.CalledProcessError as error:

			log.notice (
				"Update failed!")

			log.output (
				error.output)

	def pre_build_libraries (self, * names):

		for library_name, library_data \
		in self.third_party_index.items ():

			if names and library_name not in names:
				continue

			if not "symlink" in library_data:
				continue

			symlink_path = (
				"%s/%s" % (
					self.project_path,
					library_data ["symlink"]))

			if os.path.exists (symlink_path):
				continue

			symlink_directory_path = (
				os.path.dirname (
					symlink_path))

			if not os.path.lexists (
				symlink_directory_path):

				os.makedirs (
					symlink_directory_path)

			symlink_target = (
				"%sthird-party/%s" % (
					"../" * (library_data ["symlink"].count ("/")),
					library_name))

			os.symlink (
				symlink_target,
				symlink_path)

	def build_libraries (self, * names):

		num_built = 0
		num_failed = 0

		for library_name, library_data \
		in self.third_party_index.items ():

			if names and library_name not in names:
				continue

			library_path = (
				"%s/third-party/%s" % (
					self.project_path,
					library_name))

			# ------ work out build

			if "build" in library_data:

				build_data = (
					library_data ["build"])

			elif (

				library_data.get ("auto") == "python"

				and os.path.isfile (
					"%s/setup.py" % library_path)

			):

				python_site_packages = (
					"%s/work/lib/python2.7/site-packages" % (
						self.project_path))

				if not os.path.isdir (
					python_site_packages):

					os.makedirs (
						python_site_packages)

				build_data = {
					"command": " ".join ([
						"python setup.py install",
						"--prefix %s/work" % self.project_path,
					]),
					"environment": {
						"PYTHONPATH": python_site_packages,
					},
				}

			else:

				continue

			if isinstance (build_data, unicode):

				build_data = {
					"command": build_data,
				}

			build_data.setdefault (
				"environment",
				{})

			# ---------- perform build

			try:

				with log.status (
					"Building library: %s" % (
						library_name)):

					subprocess.check_output (
						build_data ["command"],
						shell = True,
						stderr = subprocess.STDOUT,
						env = dict (
							os.environ,
							** build_data ["environment"]),
						cwd = library_path)

				num_built += 1

			except subprocess.CalledProcessError as error:

				log.notice (
					"Build failed!")

				log.output (
					error.output)

				num_failed += 1

		if num_failed:

			log.notice (
				"Built %s remotes with %s failures" % (
					num_built,
					num_failed))

		elif num_built:

			log.notice (
				"Built %s remotes" % (
					num_built))

	def merge_libraries (self, * names):

		num_merged = 0
		num_failed = 0

		for library_name, library_data \
		in self.third_party_index.items ():

			if names and library_name not in names:
				continue

			if not "merge" in library_data:
				continue

			library_path = (
				"%s/third-party/%s" % (
					self.project_path,
					library_name))

			try:

				for library_merge in library_data ["merge"]:

					with log.status (
						"Merging library: %s (%s -> %s)" % (
							library_name,
							library_merge ["source"],
							library_merge ["target"])):

						unmerged_path = (
							".merged/%s" % (
								library_merge ["target"]))

						if os.path.exists (
							"%s/%s" % (
								self.project_path,
								unmerged_path)):

							unmerged_tree = (
								self.git_repo.head.commit.tree [
									unmerged_path])

						else:

							unmerged_tree = (
								self.git_repo.tree (
									"4b825dc642cb6eb9a060e54bf8d69288fbee4904"))

						target_path = (
							"%s" % (
								library_merge ["target"] [1:]))

						if os.path.exists (
							"%s/%s" % (
								self.project_path,
								target_path)):

							target_tree = (
								self.git_repo.head.commit.tree [
									target_path])

						else:

							target_tree = (
								self.git_repo.tree (
									"4b825dc642cb6eb9a060e54bf8d69288fbee4904"))

						source_path = (
							"third-party/%s%s" % (
								library_name,
								library_merge ["source"]))

						source_tree = (
							self.git_repo.head.commit.tree [
								source_path])

						log.notice (
							"SOURCE TREE: " + unicode (source_tree))

						def expand_parents (item):

							parts = item.rsplit ("/", 1)

							if len (parts) == 2:
								return ([]
									+ expand_parents (parts [0])
									+ ["/" + parts [1]]
								)

							else:
								return parts

						includes = set (map (
							lambda include: "third-party/%s%s%s" % (
								library_name,
								library_merge ["source"],
								include),
							[
								item2
								for item1 in library_merge.get ("include", [])
								for item2 in expand_parents (item1)
							]))

						excludes = set (map (
							lambda exclude: "third-party/%s%s%s" % (
								library_name,
								library_merge ["source"],
								exclude),
							library_merge.get ("exclude", [])))

						if includes or excludes:

							source_index = (
								git.IndexFile.from_tree (
									self.git_repo,
									"4b825dc642cb6eb9a060e54bf8d69288fbee4904"))

							def predicate (item, depth):
								return not excludes \
								or item not in excludes

							def prune (item, depth):
								return (
									includes
									and item.path not in includes
								) or (
									excludes
									and item.path in excludes
								)

							source_prune_length = len (
								"third-party/%s%s/" % (
									library_name,
									library_merge ["source"]))

							for item in source_tree.traverse (
									predicate = lambda i, d: True,
									prune = prune):

								source_index.add (
									[ git.Blob (
										self.git_repo,
										item.binsha,
										item.mode,
										item.path [source_prune_length : ]),
									])

							source_tree = (
								source_index.write_tree ())

						merged_index = (
							git.IndexFile.from_tree (
								self.git_repo,
								unmerged_tree,
								target_tree,
								source_tree))

						merged_tree = (
							merged_index.write_tree ())

						log.notice (
							"MERGED TREE: " + unicode (merged_tree))

						if os.path.exists (
							"%s/%s" % (
								self.project_path,
								target_path)):

							self.git_repo.git.rm (
								"--force",
								"-r",
								target_path)

						self.git_repo.git.read_tree (
							unicode (merged_tree),
							"--prefix",
							target_path)

						self.git_repo.git.read_tree (
							unicode (source_tree),
							"--prefix",
							unmerged_path)

						log.notice (
							"INDEX TREE: " + unicode (
								self.git_repo.index.write_tree ()))

				if len (self.git_repo.index.diff ()):

					self.git_repo.index.commit (
						"Auto-merge changes from %s" % (
							library_name))

					num_merged += 1

			except subprocess.CalledProcessError as error:

				log.notice (
					"Merge failed!")

				log.output (
					error.output)

				num_failed += 1

		if num_failed:

			log.notice (
				"Merged %s libraries with %s failures" % (
					num_merged,
					num_failed))

		elif num_merged:

			log.notice (
				"Merged %s libraries" % (
					num_merged))

# ex: noet ts=4 filetype=python
