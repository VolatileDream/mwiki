#import curses
import os

import npyscreen


class MWikiScreen(npyscreen.Form):

	def __init__(self, wiki, stack):
		self.wiki = wiki
		self.value = stack
		super().__init__()
		self.add_handlers({
			"e" : self.when_edit,
		})


	def create(self):
		# self.value == browse_stack
		last_entry = self.value[-1]
		self.add(npyscreen.TitleFixedText, name = "History:", value = " > ".join(self.value) )
		self.add(npyscreen.FixedText, name = last_entry )
		self.pager = self.add(npyscreen.Pager, values = self.wiki.entry(last_entry).split('\n') )


	def when_edit(self, thing):
		last_entry = self.value[-1]
		self.find_parent_app().edit( last_entry )
		import curses
		curses.curs_set(0)
		screen = curses.initscr()
		screen.clear()
		self.pager.values = self.wiki.entry( last_entry ).split("\n")
		self.erase()
		self.refresh()


	def afterEditing(self):
		self.parentApp.setNextForm(None)


class MWikiApp(npyscreen.NPSAppManaged):

	def __init__(self, wiki):
		super().__init__()
		self.wiki = wiki
		self.stack = []


	def open(self, entry):
		self.stack.append(entry)
		self.run()


	def onStart(self):
		self.registerForm("MAIN", MWikiScreen(self.wiki, self.stack))


	def edit(self, entry):
		if self.wiki.clean_name(entry) != entry:
			raise Exception("invalid entry name: %s" % entry)
		os.spawnlp(os.P_WAIT, "sensible-editor", "sensible-editor", self.wiki.path(entry) )


class Other(object):

	def main(self):
		entry = self.stack[-1]
		#
		self.form = npyscreen.Form(name="MWiki")
		self.title = self.form.add(npyscreen.TitleText, value=entry)
		self.textbox = self.form.add(npyscreen.Pager, value="hello world\n" * 100)
		self.history = self.form.add(npyscreen.TitleText, value=' > '.join(self.stack))
		

	def wiki(self, wiki):
		self.stack = []
		self.wiki = wiki


	def edit(self, entry):
		if wiki.clean_name(entry) != entry:
			raise Exception("invalid entry name: %s" % entry)
		os.spawnlp(os.P_WAIT, "sensible-editor", "sensible-editor", wiki.path(entry) )


	def open(self, entry):
		self.stack.append( entry )
		self.run()


def edit_entry(wiki, entry):
	if wiki.clean_name(entry) != entry:
		raise Exception("invalid entry name: %s" % entry)
	os.spawnlp(os.P_WAIT, "sensible-editor", "sensible-editor", wiki.path(entry) )


def browse_entry(screen, browse_bar, content_win, wiki, browse_stack):
	entry = browse_stack[-1]
	browse_string = "> " + ' > '.join( browse_stack )

	max_y, max_x = screen.getmaxyx()

	# only the last max_x characters of history can be shown
	if len(browse_string) >= max_x:
		browse_string = browse_string[ len(browse_string) - max_x + 1 : ]

	while True:
		screen.clear()
		browse_bar.clear()
		content_win.clear()

		browse_bar.addstr( browse_string )
		content_win.addstr( "stack size: %s\n" % len(browse_stack) )
		str = [ "%s\n" % x for x in range(0,100) ]
		content_win.addstr( s )

		screen.refresh()
		key = screen.getch()

		if key == ord('q'):
			raise Exception("exit")
		elif key == ord('e'):
			curses.def_prog_mode()
			edit_entry(wiki, entry)
			curses.reset_prog_mode()
		elif key == curses.KEY_DOWN:
			content_win.scroll(1)
		elif key == curses.KEY_UP:
			content_win.scroll(-1)
		elif key == curses.KEY_LEFT and len(browse_stack) > 1:
			browse_stack.pop()
			break
		elif key == curses.KEY_RIGHT or key == curses.KEY_ENTER:
			# pop onto browse_stack + go
			browse_stack.append( "HelloWorld%s" % len(browse_stack) )
			browse_entry(screen, browse_bar, content_win, wiki, browse_stack)

	return

def browse(wiki, start):
	
	browse_stack = [ start ]
	stdscr = curses.initscr()
	stdscr.keypad(True)
	curses.cbreak()
	curses.noecho()
	curses.curs_set(0) # hide the cursor

	max_y, max_x = stdscr.getmaxyx()

	# height, width, line, cols
	browse_bar = stdscr.subwin( 1, max_x, 0, 0 )
	browse_bar.attron( curses.A_BOLD ) # highlight

	# the rest of the space of the window
	content_win = stdscr.subwin( max_y - 1, max_x, 1, 0 )

	try:
		while browse_stack:
			browse_entry(stdscr, browse_bar, content_win, wiki, browse_stack)
	except Exception as e:
		curses.endwin()
		print(e)
		print(browse_stack)
		raise



