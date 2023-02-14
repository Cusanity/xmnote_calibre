#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai


__license__ = 'GPL v3'
__copyright__ = '2023, Cusanity <wyc935398521@gmail.com>'
__docformat__ = 'restructuredtext en'

import re

if False:
    # This is here to keep my python error checker from complaining about
    # the builtin functions that will be defined by the plugin loading system
    # You do not need this code in your plugins
    get_icons = get_resources = None

from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel

from calibre_plugins.interface_demo.config import prefs


def is_valid_ipv4(ip_address):
    compile_ip = re.compile(
        '^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$')
    if compile_ip.match(ip_address):
        return True
    else:
        return False


def is_valid_port(port_str):
    return 65535 > int(port_str) > 1023


class DemoDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.do_user_config = do_user_config

        # The current database shown in the GUI
        # db is an instance of the class LibraryDatabase from db/legacy.py
        # This class has many, many methods that allow you to do a lot of
        # things. For most purposes you should use db.new_api, which has
        # a much nicer interface from db/cache.py
        self.db = gui.current_db

        self.l = QVBoxLayout()
        self.setLayout(self.l)

        self.label = QLabel(self.get_formatted_label())
        self.l.addWidget(self.label)

        self.setWindowTitle('纸间书摘')
        self.setWindowIcon(icon)

        self.about_button = QPushButton('About', self)
        self.about_button.clicked.connect(self.about)
        self.l.addWidget(self.about_button)

        self.marked_button = QPushButton(
            'Show books with only one format in the calibre GUI', self)
        self.marked_button.clicked.connect(self.marked)
        self.l.addWidget(self.marked_button)

        self.view_button = QPushButton(
            'View the most recently added book', self)
        self.view_button.clicked.connect(self.view)
        self.l.addWidget(self.view_button)

        self.update_metadata_button = QPushButton(
            'Update metadata in a book\'s files', self)
        self.update_metadata_button.clicked.connect(self.update_metadata)
        self.l.addWidget(self.update_metadata_button)

        self.conf_button = QPushButton(
            'Configure this plugin', self)
        self.conf_button.clicked.connect(self.config)
        self.l.addWidget(self.conf_button)

        self.resize(self.sizeHint())

    def about(self):
        # Get the about text from a file inside the plugin zip file
        # The get_resources function is a builtin function defined for all your
        # plugin code. It loads files from the plugin zip file. It returns
        # the bytes from the specified file.
        #
        # Note that if you are loading more than one file, for performance, you
        # should pass a list of names to get_resources. In this case,
        # get_resources will return a dictionary mapping names to bytes. Names that
        # are not found in the zip file will not be in the returned dictionary.
        from calibre.gui2 import error_dialog, info_dialog
        text = get_resources('about.txt')
        QMessageBox.about(self, 'About the Interface Plugin Demo',
                          text.decode('utf-8'))
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, 'Cannot update metadata',
                                'No books selected', show=True)
        # Map the rows to book ids
        selected_book_ids = list(map(self.gui.library_view.model().id, rows))
        # print(ids)
        info_dialog(self, 'Selected count', str(len(selected_book_ids)), show=True)
        filtered_list = filter(lambda a: a.get('book_id', {}) in selected_book_ids,
                               self.gui.current_db.new_api.all_annotations())
        for i in filtered_list:
            print(i)
        print(114515)

    def marked(self):
        ''' Show books with only one format '''
        db = self.db.new_api
        matched_ids = {book_id for book_id in db.all_book_ids() if len(db.formats(book_id)) == 1}
        # Mark the records with the matching ids
        # new_api does not know anything about marked books, so we use the full
        # db object
        self.db.set_marked_ids(matched_ids)

        # Tell the GUI to search for all marked records
        self.gui.search.setEditText('marked:true')
        self.gui.search.do_search()

    def view(self):
        ''' View the most recently added book '''
        most_recent = most_recent_id = None
        db = self.db.new_api
        for book_id, timestamp in db.all_field_for('timestamp', db.all_book_ids()).items():
            if most_recent is None or timestamp > most_recent:
                most_recent = timestamp
                most_recent_id = book_id

        if most_recent_id is not None:
            # Get a reference to the View plugin
            view_plugin = self.gui.iactions['View']
            # Ask the view plugin to launch the viewer for row_number
            view_plugin._view_calibre_books([most_recent_id])

    def update_metadata(self):
        '''
        Set the metadata in the files in the selected book's record to
        match the current metadata in the database.
        '''
        from calibre.gui2 import error_dialog, info_dialog
        def export_highlight(self):
            confirm = QMessageBox()
            confirm.setText(
                "Are you sure you want to send ALL highlights of the selected books to XMNOTE? This cannot be undone.")
            confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            confirm.setIcon(QMessageBox.Question)
            confirmed = confirm.exec()
            print(filter(lambda a: a.get("annotation", {}).get("type") == "highlight",
                         self.gui.current_db.new_api.all_annotations()))
            if confirmed != QMessageBox.Yes:
                return

        # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, 'Cannot update metadata',
                                'No books selected', show=True)
        # Map the rows to book ids
        ids = list(map(self.gui.library_view.model().id, rows))
        info_dialog(self, 'Selected count', str(len(ids)), show=True)
        db = self.db.new_api
        for book_id in ids:
            # Get the current metadata for this book from the db
            mi = db.get_metadata(book_id, get_cover=True, cover_as_data=True)
            fmts = db.formats(book_id)
            print('book_id: ', book_id)
            print('mi: ', mi)
            print('fmts: ', fmts)

        info_dialog(self, 'Updated files',
                    'Updated the metadata in the files of %d book(s)' % len(ids),
                    show=True)

    def get_formatted_label(self):
        res = '目标设备:\n' + prefs['server_ip_addr'] + ':' + prefs['server_port'] + '\n\n'
        res += '已选书籍:\n'
        # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        ids = list(map(self.gui.library_view.model().id, rows))
        db = self.db.new_api
        for book_id in ids:
            # Get the current metadata for this book from the db
            mi = db.get_metadata(book_id, get_cover=True, cover_as_data=True)
            fmts = db.formats(book_id)
            print('book_id: ', book_id)
            print('mi: ', mi)
            print('fmts: ', fmts)
            res += mi.title + '\n'
        return res + '\n'

    def config(self):
        from calibre.gui2 import error_dialog
        self.do_user_config(parent=self)
        self.label.setText(self.get_formatted_label())
        # Apply the changes
        if not is_valid_ipv4(prefs['server_ip_addr']):
            return error_dialog(self.gui, 'IP地址无效',
                                'IP地址无效', show=True)
        try:
            if not is_valid_port(prefs['server_port']):
                return error_dialog(self.gui, '端口无效',
                                    '端口为一个1024 ~ 65535的整数', show=True)
        except ValueError:
            return error_dialog(self.gui, '端口格式错误',
                                '端口为一个1024 ~ 65535的整数', show=True)
