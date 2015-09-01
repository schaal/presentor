#!/usr/bin/python3

import os,sys,subprocess,notify2
from subprocess import CalledProcessError
from gi.repository import Gtk, Gio

from flowboxwindow import FlowBoxWindow

APP_ID = "de.fotoschaal.presentor"

SIZE = 500
MAX_IMAGE_COUNT = 100

class PresentorApplication(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.connect("startup", self.on_startup)
        self.connect("activate",self.on_activate)
        self.connect("open",self.on_open)
        self.connect("shutdown",self.on_shutdown)

    def on_startup(self, data=None):
        notify2.init("Fotostudio Schaal")
        self.win = FlowBoxWindow(self)
        self.add_window(self.win)

    def on_activate(self, data=None):
        self.win.show_all()

    def on_open(self, app, files, hint, data=None):
        self.win._load_images(files[0])
        self.win.show_all()

    def on_shutdown(self, app, data=None):
        try:
            mount_point = self.win.choose_folder.get_file().find_enclosing_mount().get_default_location().get_path()
            subprocess.check_call(["umount",mount_point])
            self.show_notification("Speicherkarte wurde gesichert","Sie können die Speicherkarte nun entfernen","dialog-information")
        except CalledProcessError as e:
            self.show_notification("Speicherkarte konnte nicht sicher entfernt werden", "", "dialog-error")
        finally:
            os.sync()

    def show_notification(self, summary, body=None, icon=None):
        n = notify2.Notification(summary, body, icon)
        n.show()

if __name__ == "__main__":
    app = PresentorApplication()
    app.run(sys.argv)
