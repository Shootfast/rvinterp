from rv import commands, rvtypes, extra_commands
import sys
sys.path.append("/apps/Linux64/python2.6/lib/python2.6/site-packages") # for PyQt4

from code import InteractiveInterpreter
from PyQt4 import QtCore, QtGui


# stolen from http://svn.osgeo.org/qgis/trunk/qgis/python/console.py


class OutputCatcher:
	def __init__(self):
		self.data = ''
	def write(self, data):
		self.data += data
	def get_and_clean_data(self):
		tmp = self.data
		self.data = ''
		return tmp
	def flush(self):
		pass


class PythonEdit(QtGui.QTextEdit, InteractiveInterpreter):
	def __init__(self, parent=None):
		QtGui.QTextEdit.__init__(self, parent)
		InteractiveInterpreter.__init__(self, locals=None)

		self.stdout = OutputCatcher()

		self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
		self.setAcceptDrops(False)
		self.setMinimumSize(30, 30)
		self.setUndoRedoEnabled(False)
		self.setAcceptRichText(False)
		monofont = QtGui.QFont("Monospace")
		monofont.setStyleHint(QtGui.QFont.TypeWriter)
		self.setFont(monofont)

		self.buffer = []

		self.displayPrompt(False)

		self.history = QtCore.QStringList()
		self.historyIndex = 0


	def displayPrompt(self, more=False):
		"""
		Show the required prompt to the user
		"""
		self.currentPrompt = "... " if more else ">>> "
		self.currentPromptLength = len(self.currentPrompt)
		self.insertTaggedLine(self.currentPrompt, 0)
		self.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

	def isCursorInEditZone(self):
		"""
		Check whether the user has the text cursor in the bottom line of text input
		"""
		cursor = self.textCursor()
		pos = cursor.position()
		block = self.document().lastBlock()
		last = block.position() + self.currentPromptLength
		return pos >= last

	def currentCommand(self):
		"""
		Return the content of the current command line
		"""
		cursor = self.textCursor()
		block = cursor.block()
		text = block.text()
		return text.right(text.length()-self.currentPromptLength)

	def showPrevious(self):
		"""
		Show the previous command in the history
		"""
		cursor = self.textCursor()
		if self.historyIndex < len(self.history) and not self.history.isEmpty():
			cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.MoveAnchor)
			cursor.movePosition(QtGui.QTextCursor.StartOfBlock, QtGui.QTextCursor.KeepAnchor)
			cursor.removeSelectedText()
			cursor.insertText(self.currentPrompt)
			self.historyIndex += 1
			if self.historyIndex == len(self.history):
				self.insertPlainText("")
			else:
				self.insertPlainText(self.history[self.historyIndex])
		self.setTextCursor(cursor)

	def showNext(self):
		"""
		Show the next command in the history
		"""
		cursor = self.textCursor()
		if self.historyIndex > 0 and not self.history.isEmpty():
			cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.MoveAnchor)
			cursor.movePosition(QtGui.QTextCursor.StartOfBlock, QtGui.QTextCursor.KeepAnchor)
			cursor.removeSelectedText()
			cursor.insertText(self.currentPrompt)
			self.historyIndex -= 1
			if self.historyIndex == len(self.history):
				self.insertPlainText("")
			else:
				self.insertPlainText(self.history[self.historyIndex])
		self.setTextCursor(cursor)

	def updateHistory(self, command):
		"""
		Add the entered command to the history
		"""
		if isinstance(command, QtCore.QStringList):
			for line in command:
				self.history.append(line)
		elif not command == "":
			if len(self.history) <= 0 or \
			not command == self.history[-1]:
				self.history.append(command)
		self.historyIndex = len(self.history)



	def keyPressEvent(self, e):
		"""
		Callback for when user presses a key
		"""
		cursor = self.textCursor()
		
		if not self.isCursorInEditZone() and e.text() != "":
			cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
			self.setTextCursor(cursor)

		# if Ctrl A is pressed, go to start of prompt
		if e.modifiers() & QtCore.Qt.ControlModifier and e.key() == QtCore.Qt.Key_A:
			cursor.movePosition(QtGui.QTextCursor.StartOfBlock, QtGui.QTextCursor.MoveAnchor)
			cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.MoveAnchor, self.currentPromptLength)
			self.setTextCursor(cursor)
		# if Ctrl E is pressed, go to end of prompt
		elif e.modifiers() & QtCore.Qt.ControlModifier and e.key() == QtCore.Qt.Key_E:
			cursor.movePosition(QtGui.QTextCursor.EndOfBlock, QtGui.QTextCursor.MoveAnchor)
			self.setTextCursor(cursor)
		# if Ctrl L is pressed, clear the prompt
		elif e.modifiers() & QtCore.Qt.ControlModifier and e.key() == QtCore.Qt.Key_L:
			command = self.currentCommand()
			self.stdout.get_and_clean_data()
			self.setText("")
			self.displayPrompt(self.buffer != [])
			self.insertPlainText(command)
		# if Ctrl C is pressed, cancel input on the current line
		elif e.modifiers() & QtCore.Qt.ControlModifier and e.key() == QtCore.Qt.Key_C:
			cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
			self.setTextCursor(cursor)
			self.insertPlainText("\n")
			self.buffer = []
			self.displayPrompt(False)
			
		# if Ctrl D is pressed, close the interpreter
		elif e.modifiers() & QtCore.Qt.ControlModifier and e.key() == QtCore.Qt.Key_D:
			self.parentWidget().close()
			
		# if Return is pressed, then perform the commands
		if e.key() == QtCore.Qt.Key_Return or e.key() == QtCore.Qt.Key_Enter:
			self.entered()
		# if Up or Down is pressed
		elif e.key() == QtCore.Qt.Key_Down:
			self.showPrevious()
		elif e.key() == QtCore.Qt.Key_Up:
			self.showNext()
		# if backspace is pressed, delete until we get to the prompt
		elif e.key() == QtCore.Qt.Key_Backspace:
			if not cursor.hasSelection() and cursor.columnNumber() == self.currentPromptLength:
				return
			QtGui.QTextEdit.keyPressEvent(self, e)
		# if the left key is pressed, move left until we get to the prompt
		elif e.key() == QtCore.Qt.Key_Left and cursor.position() > self.document().lastBlock().position() + self.currentPromptLength:
			anchor = QtGui.QTextCursor.KeepAnchor if e.modifiers() & QtCore.Qt.ShiftModifier else QtGui.QTextCursor.MoveAnchor
			move = QtGui.QTextCursor.WordLeft if e.modifiers() & QtCore.Qt.ControlModifier or e.modifiers() & QtCore.Qt.MetaModifier else QtGui.QTextCursor.Left
			cursor.movePosition(move, anchor)
		# use normal operation for right key
		elif e.key() == QtCore.Qt.Key_Right:
			anchor = QtGui.QTextCursor.KeepAnchor if e.modifiers() & QtCore.Qt.ShiftModifier else QtGui.QTextCursor.MoveAnchor
			move = QtGui.QTextCursor.WordRight if e.modifiers() & QtCore.Qt.ControlModifier or e.modifiers() & QtCore.Qt.MetaModifier else QtGui.QTextCursor.Right
			cursor.movePosition(move, anchor)
		# if home is pressed, move cursor to right of prompt
		elif e.key() == QtCore.Qt.Key_Home:
			anchor = QtGui.QTextCursor.KeepAnchor if e.modifiers() & QtCore.Qt.ShiftModifier else QtGui.QTextCursor.MoveAnchor
			cursor.movePosition(QtGui.QTextCursor.StartOfBlock, anchor, 1)
			cursor.movePosition(QtGui.QTextCursor.Right, anchor, self.currentPromptLength)
		# use normal operation for end key
		elif e.key() == QtCore.Qt.Key_End:
			anchor = QtGui.QTextCursor.KeepAnchor if e.modifiers() & QtCore.Qt.ShiftModifier else QtGui.QTextCursor.MoveAnchor
			cursor.movePosition(QtGui.QTextCursor.EndOfBlock, anchor, 1)
		# use normal operation for all remaining keys
		else:
			if e.text() == "":
				return
			QtGui.QTextEdit.keyPressEvent(self, e)

		self.setTextCursor(cursor)
		self.ensureCursorVisible()



	def insertFromMimeData(self, source):
		"""
		Ensure that on paste events, the data always goes into the edit zone
		"""
		cursor = self.textCursor()
		if source.hasText():
			pasteList = QtCore.QStringList()
			pasteList = source.text().split("\n")
			# move the cursor to the end only if the text is multi-line or is going to be pasted not into the last line
			if (len(pasteList) > 1) or (not self.isCursorInEditZone()):
				cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor, 1)
			self.setTextCursor(cursor)
			# with multi-line text also run the commands
			for line in pasteList[:-1]:
				self.insertPlainText(line)
				self.runCommand(unicode(self.currentCommand()))
			# last line: only paste the text, do not run it
			self.insertPlainText(unicode(pasteList[-1]))

	def entered(self):
		cursor = self.textCursor()
		cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
		self.setTextCursor(cursor)
		self.runCommand( unicode(self.currentCommand()) )


	def insertTaggedText(self, txt, tag):
		if len(txt) > 0 and txt[-1] == '\n': # remove trailing newline to avoid one more empty line
			txt = txt[0:-1]

		c = self.textCursor()
		for line in txt.split('\n'):
			b = c.block()
			b.setUserState(tag)
			c.insertText(line)
			c.insertBlock()

	def insertTaggedLine(self, txt, tag):
		c = self.textCursor()
		b = c.block()
		b.setUserState(tag)
		c.insertText(txt)


	def runCommand(self, cmd):
		oldstdout = sys.stdout
		if oldstdout != self.stdout:
			sys.stdout = self.stdout

		self.updateHistory(cmd)
		self.insertPlainText("\n")

		self.buffer.append(cmd)
		src = "\n".join(self.buffer)
		more = self.runsource(src, "<input>")
		if not more:
			self.buffer = []

		output = self.stdout.get_and_clean_data()
		if output:
			self.insertTaggedText(output, 2)
		self.displayPrompt(more)

		sys.stdout = oldstdout


	def write(self, txt):
		""" reimplementation from code.InteractiveInterpreter """
		self.insertTaggedText(txt, 1)

class Interpreter(QtGui.QDialog):
	def __init__(self, parent=None):
		super(Interpreter, self).__init__(parent)
		self.edit = PythonEdit()
		self.vbox = QtGui.QVBoxLayout()
		self.vbox.addWidget(self.edit)
		self.setLayout(self.vbox)
		self.setMinimumSize(1000, 600)
		self.setWindowTitle("Python Interpreter")
		


class InterpreterMinorMode(rvtypes.MinorMode):
	def __init__(self):
		rvtypes.MinorMode.__init__(self)

		menu = [("Window", [("Python Interpreter", self.createWindow, "F12", None)])]
		self.init("interpreter", None, None, menu)

	def createWindow(self, event):
		dialog = Interpreter(QtGui.QApplication.topLevelWidgets()[0])
		dialog.show()
	

def createMode():
	return InterpreterMinorMode()
