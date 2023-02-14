#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai


__license__   = 'GPL v3'
__copyright__ = '2023, Cusanity <wyc935398521@gmail.com>'
__docformat__ = 'restructuredtext en'

from qt.core import QWidget, QHBoxLayout, QLabel, QLineEdit

from calibre.utils.config import JSONConfig

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/interface_demo) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/interface_demo')

# Set defaults
prefs.defaults['server_ip_addr'] = '192.168.0.1'
# prefs.defaults['server_port'] = '8080'


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.popup = QHBoxLayout()
        self.setLayout(self.popup)

        self.ip_label = QLabel('设备IP地址: ')
        self.popup.addWidget(self.ip_label)

        self.ip_edit = QLineEdit(self)
        self.ip_edit.setText(prefs['server_ip_addr'])
        self.popup.addWidget(self.ip_edit)
        self.ip_label.setBuddy(self.ip_edit)

        # self.port_label = QLabel('设备端口号: ')
        # self.popup.addWidget(self.port_label)
        #
        # self.port_edit = QLineEdit(self)
        # self.port_edit.setText(prefs['server_port'])
        # self.popup.addWidget(self.port_edit)
        # self.port_label.setBuddy(self.port_edit)

    def save_settings(self):
        prefs['server_ip_addr'] = self.ip_edit.text()
        # prefs['server_port'] = self.port_edit.text()
