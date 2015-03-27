import wiki
import browse

import click
import fuzzywuzzy
import fuzzywuzzy.process

wiki_options = { "_" : None }


def get_wiki():
	if not wiki_options["_"]:
		wiki_options["_"] = wiki.MWiki.find_wiki()
	return wiki_options["_"]


@click.group()
@click.option("--wiki", "-w", default=".")
def mwiki(wiki):
	wiki_options["wiki"] = wiki


@mwiki.command("entries")
def entries():
	wiki = get_wiki()
	for entry in wiki.entries():
		print(entry)


def browse_entries(stdscr, wiki, browse_stack):
	pass


@mwiki.command("open")
@click.argument("name")
def open(name):
	wiki = get_wiki()
	app = browse.MWikiApp(wiki)
	app.open(name)
	#app.run()
	#browse.browse(wiki, name)


@mwiki.command("edit")
@click.argument("name")
def edit(name):
	wiki = get_wiki()
	browse.edit_entry(wiki, name)


@mwiki.command("search")
@click.argument("string")
def search(string):
	wiki = get_wiki()
	entries = wiki.entries()
	results = fuzzywuzzy.process.extract(string, entries)
	for entry, score in results:
		print(str(score) + "\t" + entry)


if __name__ == "__main__":
	try:
		mwiki()
	except Exception as e:
		print(e)


