from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import with_statement

import os
import subprocess
import sys

try:

	import git
	import yaml

except ImportError:

	pass

import wbs.yamlx as yamlx

def read_index ():

	return yamlx.load_data (
		"third-party/third-party-index")

def setup ():

	third_party_index = (
		read_index ())

	git_repo = (
		git.Repo (
			"."))

	sys.stdout.write (
		"About to set up third party libraries\n")

	# create remotes

	remotes_index = dict ([
		(remote.name, remote)
		for remote
		in git_repo.remotes
	])

	for project_name, project_data \
	in third_party_index.items ():

		if not project_name in remotes_index:

			sys.stdout.write (
				"Create missing remote for %s\n" % (
					project_name))

			remotes_index [project_name] = (
				git_repo.create_remote (
					project_name,
					project_data ["url"]))

	# fetch remotes

	for project_name, project_data \
	in third_party_index.items ():

		remote_version = (
			project_data ["version"])

		sys.stdout.write (
			"Fetch remote: %s (%s)\n" % (
				project_name,
				remote_version))

		git_repo.remotes [project_name].fetch (
			"%s:refs/%s/%s" % (
				remote_version,
				project_name,
				remote_version))

		sys.stdout.write (
			"\x1b[1A\x1b[K")

	sys.stdout.write (
		"Fetched %s remotes\n" % (
			len (third_party_index)))

	# stash changes

	if git_repo.is_dirty ():

		sys.stdout.write (
			"Stashing local changes\n")

		git_repo.git.stash (
			"save")

		stashed = True

	else:

		stashed = False

	try:

		for project_name, project_data \
		in third_party_index.items ():

			project_path = (
				"third-party/%s" % (
					project_name))

			if not os.path.isdir (
				project_path):

				sys.stdout.write (
					"First time import library: %s\n" % (
						project_name))

				subprocess.check_call ([
					"git",
					"subtree",
					"add",
					"--prefix", project_path,
					project_data ["url"],
					project_data ["version"],
					"--squash",
				])

			else:

				local_tree = (
					git_repo
						.head
						.commit
						.tree ["third-party"] [project_name])

				git_remote = (
					git_repo.remotes [
						project_name])

				if project_data ["version"] in git_remote.refs:

					remote_ref = (
						git_remote.refs [
							project_data ["version"]])

					remote_commit = (
						remote_ref.commit)

				else:

					remote_commit = (
						git_repo.commit (
							project_data ["version"]))

				remote_tree = (
					remote_commit.tree)

				if local_tree == remote_tree:
					continue

				sys.stdout.write (
					"Update library: %s\n" % (
						project_name))

				subprocess.check_call ([
					"git",
					"subtree",
					"merge",
					"--prefix",
					project_path,
					unicode (remote_commit),
					"--squash",
					"--message",
					"update %s to %s" % (
						project_name,
						project_data ["version"]),
				])

	finally:

		if stashed:

			sys.stdout.write (
				"Unstashing local changes\n")

			git_repo.git.stash (
				"pop")

	print (
		"All done")

# ex: noet ts=4 filetype=python
