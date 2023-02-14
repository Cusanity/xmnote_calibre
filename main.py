#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai


__license__ = 'GPL v3'
__copyright__ = '2023, Cusanity <wyc935398521@gmail.com>'
__docformat__ = 'restructuredtext en'

import json
import re
import mechanize

from calibre.gui2 import error_dialog, info_dialog

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

        self.conf_button = QPushButton(
            '设置目标设备的IP', self)
        self.conf_button.clicked.connect(self.config)
        self.l.addWidget(self.conf_button)

        self.about_button = QPushButton('导出到纸间书摘', self)
        self.about_button.clicked.connect(self.export)
        self.l.addWidget(self.about_button)

        self.view_button = QPushButton(
            '帮助', self)
        self.view_button.clicked.connect(self.xmnote_help)
        self.l.addWidget(self.view_button)

        self.resize(self.sizeHint())

    def export(self):
        # Get the about text from a file inside the plugin zip file
        # The get_resources function is a builtin function defined for all your
        # plugin code. It loads files from the plugin zip file. It returns
        # the bytes from the specified file.
        #
        # Note that if you are loading more than one file, for performance, you
        # should pass a list of names to get_resources. In this case,
        # get_resources will return a dictionary mapping names to bytes. Names that
        # are not found in the zip file will not be in the returned dictionary.
        import dateutil.parser as dp
        from calibre.ebooks.metadata import authors_to_string
        rows = self.gui.library_view.selectionModel().selectedRows()
        # Map the rows to book ids
        selected_book_ids = list(map(self.gui.library_view.model().id, rows))
        db = self.db.new_api
        for book_id in selected_book_ids:
            # Get the current metadata for this book from the db
            mi = db.get_metadata(book_id, get_cover=True, cover_as_data=True)
            fmts = db.formats(book_id)
            filtered_list = self.gui.current_db.new_api.all_annotations_for_book(book_id)
            body = {'title': mi.title,
                    'author': authors_to_string(mi.authors),
                    'publisher': mi.publisher,
                    'publishDate': int(dp.parse(str(mi.pubdate)).timestamp()),
                    'type': 1,
                    'locationUnit': 1,
                    'entries': []
                    }
            if mi.isbn:
                body['isbn'] = mi.isbn

            print('book_id: ', book_id)
            print('mi: ', mi)
            print('fmts: ', fmts)
            for i in filtered_list:
                anno = i['annotation']
                if 'removed' in anno and anno['removed'] is True:
                    continue
                timestamp_str = str(anno['timestamp'])
                timestamp = int(dp.parse(timestamp_str).timestamp())

                entry = {'text': anno['highlighted_text']}
                if 'notes' in anno:
                    entry['note'] = anno['notes']
                if 'toc_family_titles' in anno and len(anno['toc_family_titles']) > 0:
                    entry['chapter'] = ' > '.join(anno['toc_family_titles'])
                entry['time'] = timestamp
                print(str(i))
                body['entries'].append(entry)

            url = 'http://%s:8080/send' % prefs['server_ip_addr']
            print(json.dumps(body))
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json;charset=UTF-8',
            }
            br = mechanize.Browser()
            br.set_handle_robots(False)
            req = mechanize.Request(url=url,
                                    data=json.dumps(body),
                                    headers=headers,
                                    method='POST')
            from urllib.error import URLError
            try:
                resp = br.open(req)
                print(json.loads(resp.read()))
            except URLError:
                return error_dialog(self.gui, '请求发送失败',
                                    '可能原因:\n• 目标设备IP地址错误\n• 目标设备未进入API导入界面', show=True,
                                    show_copy_button=False)

    def xmnote_help(self):
        return info_dialog(self, '帮助',
                           '若要将Calibre的笔记发送至纸间书摘，请确保纸间书摘的版本在v3.5.6及以上。'
                           '在开始导出前您需要让运行Calibre的设备与运行纸间书摘的设备处在同一局域网中，'
                           '然后在纸间书摘中打开「我的」-「书摘导入」-「通过API导入」，您可以在打开的页面底部看到设备的IP。'
                           '将IP输入至「设置目标设备的IP」一栏中，即可开始执行笔记的导出。',
                           show=True,
                           show_copy_button=False
                           )

    def get_formatted_label(self):
        res = '目标设备IP:\n' + prefs['server_ip_addr'] + '\n\n'
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
            res += '• ' + mi.title + '\n'
        return res + '\n'

    def config(self):
        self.do_user_config(parent=self)
        self.label.setText(self.get_formatted_label())
        # Apply the changes
        if not is_valid_ipv4(prefs['server_ip_addr']):
            return error_dialog(self.gui, 'IP地址无效',
                                'IP地址无效', show=True)
        # try:
        #     if not is_valid_port(prefs['server_port']):
        #         return error_dialog(self.gui, '端口无效',
        #                             '端口为一个1024 ~ 65535的整数', show=True)
        # except ValueError:
        #     return error_dialog(self.gui, '端口格式错误',
        #                         '端口为一个1024 ~ 65535的整数', show=True)
