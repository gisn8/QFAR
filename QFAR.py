"""
A recent network update left me with hundreds of QGIS project files each with dozens of layer locations needing 
updated to the new layer sources if I ever hoped to use them again. Without this, it would take significant time to even
open a project file with dead ends and then more time rerouting the layers. Testing on dozens of files, this is nearly 
instantaneous.

This program finds qgz and qgs files within a given directory and optionally its subdirectories, copies the files to a 
temp file while finding and replacing the values the user submitted, renames the original to a numbered hidden archive 
file if desired, replaces the original file with the modified version and assigns the "modified file date" to the same 
values as the original file. 

This could be used, for example, to change the IP address of your database source (ex. 192.168.12.34 to 192.168.56.78), 
drive locations (ex. /home/user/GIS_Data to /home/user/Drives/Data/GIS_Data), or even layer specific changes 
(Aerials_2018 to Aerials_2022), though there may be layer specific modifications that would need to be addressed. But as
this is a simple find and replace, any reference to the FIND string will be replaced regardless, so proceed with caution.

Archive copies that are made are prepended with '.' regardless of system. This makes them hidden on Linux systems; on 
Windows, the extra step is taken to also make them hidden; the archive name will still be prepended with '.'. Any files
prepended with '.' will be ignored, however Windows QGS and QGZ files that are not prepended with '.', even if hidden,
will be modified.

Considered seeking out "source=..." and finding and replacing within those strings specifically, but there are going 
be layer names that reference the source of the file that may also need updated to reduce confusion. However this could 
also potentially impact internal file metadata. *Again, this is a simple find and replace method.*


*** WARNING! ***
There are no safeguards against error or malicious injection! It is not outside the possibility to completely corrupt 
your files beyond hope of recovery! Take extreme care! Developer is not responsible for results!

It is recommended that you create a new directory and copy over a few QGIS project files to make sure you're getting the 
results you're expecting before using on your working directories.

WINDOWS: I've tried to accomodate for Windows, but at this time, my Windows machine is down. I could not adequately test. 
LINUX: Performed as expected.
APPLE: I have no access to an Apple machine at this time.
"""

import sys
import os
import platform
import subprocess
import zipfile
import re

from datetime import datetime
from fnmatch import fnmatch
from glob import glob

from PyQt5.QtWidgets import *
from PyQt5 import QtCore

class QFAR_Dlg(QWidget):
	def __init__(self):
		super().__init__()
		self.initUI()
	
	
	def initUI(self):
		self.setWindowTitle('QFAR - A Bulk Find and Replace for QGIS Project Files')  
		
		self.layout = self.set_layout()
		
		self.setLayout(self.layout)
		self.set_connections()
		
		# If repeatedly testing with the same variables, fill appropriate values below, otherwise set to preferred defaults.
		self.set_default_values(find='',replace='', directory='', recursive=True, archive=True)
		
		self.show()

	
	def set_layout(self):
		self.vbox_main = QVBoxLayout()

		# Instructional elements
		self.hbox_instructions = QHBoxLayout()
		self.lbl_instructions = QLabel()
		self.lbl_instructions.setText('This program searches for QGZ format QGIS project files within the given	directory and does a basic find and replace. Useful for bulk redirecting of layer sources.')
		self.lbl_instructions.setWordWrap(True)
		self.hbox_instructions.addWidget(self.lbl_instructions)
		
		self.vbox_main.addLayout(self.hbox_instructions)
		
		# Find and replace elements
		self.hbox_far = QHBoxLayout()

		self.vbox_old = QVBoxLayout()
		self.lbl_find = QLabel()
		self.lbl_find.setText('Find:')
		self.ln_find = QLineEdit()
		
		self.ln_find.setMinimumHeight(29)
		self.vbox_old.addWidget(self.lbl_find)
		self.vbox_old.addWidget(self.ln_find)
		self.hbox_far.addLayout(self.vbox_old)

		self.vbox_new = QVBoxLayout()
		self.lbl_replace = QLabel()
		self.lbl_replace.setText('Replace with:')
		self.ln_replace = QLineEdit()
		
		self.ln_replace.setMinimumHeight(29)
		self.vbox_new.addWidget(self.lbl_replace)
		self.vbox_new.addWidget(self.ln_replace)
		self.hbox_far.addLayout(self.vbox_new)

		self.vbox_main.addLayout(self.hbox_far)
		
		self.vbox_main.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding))

		# Browse directory elements
		self.lbl_directory = QLabel()
		self.lbl_directory.setText('Starting Directory:')
		self.vbox_main.addWidget(self.lbl_directory)

		self.hbox_browse = QHBoxLayout()
		
		self.ln_directory = QLineEdit()
		
		self.ln_directory.setMinimumWidth(320)
		self.hbox_browse.addWidget(self.ln_directory)
		
		self.btn_browse = QPushButton()
		self.btn_browse.setText('Browse')
		self.hbox_browse.addWidget(self.btn_browse)
		self.vbox_main.addLayout(self.hbox_browse)
		
		# Archive originals
		self.hbox_archive = QHBoxLayout()
		self.chk_archive = QCheckBox()
		self.chk_archive.setText('Archive original and mark hidden?')
		self.chk_archive.setChecked(True)
		self.vbox_main.addWidget(self.chk_archive)

		# Recursive checkbox and Start button
		self.hbox_recursive_and_start = QHBoxLayout()
		self.chk_recursive = QCheckBox()
		self.chk_recursive.setText('Search subdirectories?')
		self.chk_recursive.setChecked(True)
		self.hbox_recursive_and_start.addWidget(self.chk_recursive)
		
		self.hbox_recursive_and_start.addSpacerItem(QSpacerItem(150, 10, QSizePolicy.Expanding))

		self.btn_start = QPushButton()
		self.btn_start.setText('Start')
		self.hbox_recursive_and_start.addWidget(self.btn_start)
		self.vbox_main.addLayout(self.hbox_recursive_and_start)

		return self.vbox_main

	
	def set_default_values(self, find='', replace='', directory='', recursive=True, archive=True):
		self.ln_find.setText(find)
		self.ln_replace.setText(replace)
		self.ln_directory.setText(directory)
		self.chk_recursive.setChecked(recursive)
		self.chk_archive.setChecked(archive)

		# If there are default values loaded, setting for <ENTER> to launch as is.
		if find + replace + directory != '':
			self.btn_start.setFocus()
			self.btn_start.setAutoDefault(True)


	def set_connections(self):
		self.btn_browse.clicked.connect(self.get_directory)
		self.btn_start.clicked.connect(self.do_the_thing)
		
	
	def get_directory(self):
		# Gets home directory whatever the OS
		home  = os.path.expanduser('~')
		
		# Opens dialog for user to navigate to desired directory to seek QGZ files (with recursive option?).
		dirpath = QFileDialog.getExistingDirectory(self, 'Select Directory', home)
		
		self.ln_directory.setText(dirpath)


	def do_the_thing(self):
		
		# Validate path
		valid_path = self.validate_dir_path()

		# Validate inputs
		valid_inputs = self.validate_inputs()

		if valid_path and valid_inputs:

			# Gets all QGS/Z files within the appointed directory and its subdirectories if desired.
			files = self.list_files()

			# Filters the files and produces omissions lists
			files, unwritable_files = self.omit_unwritable_files(files)

			# files, archived_files = self.omit_archived_files(files)
			# Efforts to offer lists of what archive files were found ended up in archive files being processed.
			# Not worth the time to write a correction for this. Too little payoff.

			# As comparing before and aftercontent would need to be done to make the list, then again to create new 
			# files, doing within process below instead.
			acceptable_files = []
			updated_files = []

			for file in files:
				
				# See if there are content changes needed in each file
				update_required, content = self.compare_content(file)

				if update_required:
					# Get time metadata from original file
					ctime, mtime, atime = self.get_time_metadata(file)

					# Write new file
					newfile = self.write_new_file(file, content)

					# Checking how metadata has changed (for testing)
					# self.get_time_metadata(newfile)

					# Archive or delete original file
					if self.chk_archive.isChecked():
						self.create_archive(file, ctime, mtime, atime)
					else:
						os.remove(file)
					
					# Rename newfile to original name
					os.rename(newfile, file)

					# Since it has replaced the old file, the newfile path assumes the old file path
					newfile = file

					# assign metadata and seeing if changes reverted as expected;
					self.assign_time_metadata (newfile, ctime, mtime, atime)

					updated_files.append(file)
				
				else:
					acceptable_files.append(file)
						
		# Notify user of process achievements.
		title = ('Process complete!')
		# Options: QMessageBox.Question, Information, Warning, Critical, NoIcon
		icon = QMessageBox.NoIcon
		text = f'\nProcess complete!\n{len(updated_files)} file(s) updated out of {len(files) + len(unwritable_files)} QGIS project file(s) found!\n'
		
		# Using breakline to widen the msgbox as they don't respond to resizing, but will size to content.
		# It's messy, but needed to include the messages (if they will even be needed) in the breakline size consideration.
		breakline = ''
		acceptable_files_found = ''
		unwritable_files_found = ''

		if len(acceptable_files) > 0:
			acceptable_files_found = f'{len(acceptable_files)} file(s) did not require changes:'			
		
		if len(unwritable_files) > 0:
			unwritable_files_found = f'Skipped {len(unwritable_files)} file(s) that did not have adequate write permissions:'

		# Calculating required length of the breakline. Padding by ~15% for non-monospace fonts.
		# len(max(list, key=len) calculates the length of the longest item in a list. Lists can be simply added together to merge.
		bl_len = len(max(files+acceptable_files+unwritable_files+[acceptable_files_found,unwritable_files_found], key=len))*1.15

		for x in range(round(bl_len)):
			breakline = breakline + '_'
		breakline = breakline + '\n'

		if len(acceptable_files) > 0:
			text = text + f'{breakline}\n{acceptable_files_found}\n{self.linebreak_list(acceptable_files)}\n'

		if len(unwritable_files) > 0:
			text = text + f'{breakline}\n{unwritable_files_found}\n{self.linebreak_list(unwritable_files)}\n'
		
		# Closing breakline if multiple sections
		if len(acceptable_files) + len(unwritable_files) > 0:
			text = text + breakline

		self.msgbox(title, icon, text)
		
		print(text)
		print(f'{len(updated_files)} file(s) were modified: \n{self.linebreak_list(updated_files)}\n')
		print('Completed!')
		
		self.close()


	def validate_inputs(self):
		find_string = self.ln_find.text()
		replace_string = self.ln_replace.text()

		# Just in case
		title = ('Input Error!')
		# Options: QMessageBox.Question, Information, Warning, Critical
		icon = QMessageBox.Warning
		text = 'The following are allowed in the "Find" and "Replace with" inputs:\n [A-Z,a-z,0-9,-,_,~,`'

		if find_string == '':
			text = '"Find" input cannot be left blank.'
			self.msgbox(title, icon, text)
			return False

		elif replace_string == '':
			text = '"Replace with" input cannot be left blank.'
			self.msgbox(title, icon, text)
			return False

		# elif not self.is_allowed(find_string):
		# 	self.msgbox(title, icon, text)
		# 	return False

		# elif not self.is_allowed(replace_string):
		# 	self.msgbox(title, icon, text)
		# 	return False

		else:
			return True


	def is_allowed(self, string):
	    characterRegex = re.compile(r'[^a-zA-Z0-9\\/.~:=-\'"]')
	    string = characterRegex.search(string)
	    return not bool(string)
	

	def validate_dir_path(self):
		valid = os.path.exists(self.ln_directory.text())
		
		if valid:
			return valid
		else:
			# Notify user directory not found.
			title = ('Directory Not Found!')
			# Options: QMessageBox.Question, Information, Warning, Critical
			icon = QMessageBox.Warning
			text = 'Directory not found. Please try again.'
			self.msgbox(title, icon, text)


	def list_files(self):
		# creates list of QGZ files within working directory. Setting up Linux and Windows path types.
		path = self.ln_directory.text()
		
		files = []

		if self.chk_recursive.isChecked():
			search_path_wqgz = f'{path}\\**\\*.qgz'
			search_path_wqgs = f'{path}\\**\\*.qgs'
			search_path_lqgz = f'{path}/**/*.qgz'
			search_path_lqgs = f'{path}/**/*.qgs'
		else:
			search_path_wqgz = f'{path}\\*.qgz'
			search_path_wqgs = f'{path}\\*.qgs'
			search_path_lqgz = f'{path}/*.qgz'
			search_path_lqgs = f'{path}/*.qgs'

		if platform.system() == 'Windows':
			for file in glob(search_path_wqgz, recursive=self.chk_recursive.isChecked()):
				files.append(file)
			
			for file in glob(search_path_wgs, recursive=self.chk_recursive.isChecked()):
				files.append(file)
		
		else:
			for file in glob(search_path_lqgz, recursive=self.chk_recursive.isChecked()):
				files.append(file)

			for file in glob(search_path_lqgs, recursive=self.chk_recursive.isChecked()):
				files.append(file)

		print(f'{len(files)} file(s) found:')
		print(self.linebreak_list(files))
		
		return files

	
	def omit_unwritable_files(self, files):
		unwritable_files = []		

		# Bypass file if user does not have write permissions.
		for file in files:
			if not os.access(file, os.W_OK):
				unwritable_files.append(file)
				files.remove(file)

		return files, unwritable_files

	
	def compare_content(self, file):
		find_string = self.ln_find.text()
		replace_string = self.ln_replace.text()

		if fnmatch(file, '*.qgs'):
			with open(file, 'r') as infile:
				content_old = infile.read()
				content_new = content_old.replace(find_string, replace_string)
		
		if fnmatch(file, '*.qgz'):
			inzip = zipfile.ZipFile(file, "r")
		
			# Iterate the input files
			for inzipinfo in inzip.infolist():
				# print(f'inzipinfo: {inzipinfo}')
				
				# Read input file
				with inzip.open(inzipinfo) as infile:
					if fnmatch(inzipinfo.filename, '*.qgs'):
						content_old = infile.read().decode()
						
						# Modify the content of the file by replacing a string
						content_new = content_old.replace(find_string, replace_string)
			
			inzip.close()

		if content_old == content_new:
			update_required = False
			content = None
		else:
			update_required = True
			content = content_new
		
		return update_required, content


	def get_time_metadata(self, file):
		# Creation Time
		ctime = os.path.getctime(file)

		# Modification Time
		mtime = os.path.getmtime(file)

		# Access Time (set for now)
		atime = datetime.now().timestamp()

		# print(f'Creation DT:     {datetime.fromtimestamp(ctime)}')
		# print(f'Modification DT: {datetime.fromtimestamp(mtime)}')
		# print(f'Access DT:       {datetime.now()}')

		# print(f'Creation TS:	   {ctime}')
		# print(f'Modification TS: {mtime}')
		# print(f'Access TS:	   {atime}')

		return ctime, mtime, atime

	
	def write_new_file(self, file, content):
		# https://www.geeksforgeeks.org/how-to-search-and-replace-text-in-a-file-in-python/
		
		srcfile = f'{file}'
		dstfile = f'{os.path.dirname(file)}/tmp_{os.path.basename(file)}'

		if fnmatch(srcfile, '*.qgs'):
			with open(dstfile, 'w') as outfile:
				outfile.write(content)

		if fnmatch(srcfile, '*.qgz'):
			dstfile = self.write_new_zipfile(file, srcfile, dstfile, content)

		return dstfile

	
	def write_new_zipfile(self, file, srcfile, dstfile, content):
		# https://techoverflow.net/2020/11/11/how-to-modify-file-inside-a-zip-file-using-python/
		
		inzip = zipfile.ZipFile(srcfile, "r")
		outzip = zipfile.ZipFile(dstfile, "w", compression=zipfile.ZIP_DEFLATED)

		# print(f'inzip.infolist: {inzip.infolist()}')
		
		# Iterate the input files
		for inzipinfo in inzip.infolist():
			# print(f'inzipinfo: {inzipinfo}')
			# Copy zip file with modified QGS
			with inzip.open(inzipinfo) as infile:
				if fnmatch(inzipinfo.filename, '*.qgs'):
					outzip.writestr(inzipinfo.filename, content.encode())
				
				else: # Other file, dont want to modify, just copy it
					outzip.writestr(inzipinfo.filename, infile.read())
		
		inzip.close()
		outzip.close()

		return dstfile


	def create_archive(self, file, ctime, mtime, atime):
		# See if archive name already exists. If not, create, otherwise create numbered archive file.
		
		# Create iteration counter
		i = 0
		
		# breakdown filename
		
		filepath = os.path.dirname(file)
		
		# Removing filepath and '/'. Will need the stripped filename to rebuild as hidden in Linux.
		filename_no_ext = os.path.splitext(file)[0].replace(filepath,'').replace('/','')
		
		file_ext = os.path.splitext(file)[1]

		arch_file = f'{filepath}/.{filename_no_ext}_{i}{file_ext}'
		
		while True:
			if platform.system() == 'Windows':
				arch_file = arch_file.replace('/','\\')

			if os.path.exists(arch_file):
				i += 1
				arch_file = f'{filepath}/.{filename_no_ext}_{i}{file_ext}'
			
			else:
				os.rename(file, arch_file)
				
				if platform.system() == 'Windows':
					# Setting file to Hidden
					os.system( f"attrib +h {arch_file}" )

				self.assign_time_metadata(arch_file, ctime, mtime, atime)
				
				break


	def assign_time_metadata(self, file, ctime, mtime, atime):
		os.utime(file, (atime, mtime))

		self.get_time_metadata(file)


	def linebreak_list(self, inlist):
		lb_list = "\n".join(map(str, inlist))
		return lb_list


	def msgbox(self, title=None, icon=None, text=None, info=None, details=None):
		msg = QMessageBox()
		if title:
			msg.setWindowTitle(title)
		if icon:
			# Options: QMessageBox.Question, Information, Warning, Critical, NoIcon
			msg.setIcon(icon)
		if text:
			msg.setText(text)
		if info:
			msg.setInformativeText(info)
		if details:
			msg.setDetailedText(details)

		msg.setStandardButtons(QMessageBox.Ok)	# msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		
		msg.exec_()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	frame = QFAR_Dlg()
	sys.exit(app.exec_())
