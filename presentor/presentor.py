#!/usr/bin/python3

import os, sys, subprocess, notify2

from gi.repository import Gtk, Gio
from gi.repository.GLib import Error
from gi.repository.GObject import threads_init

from presentor.flowboxwindow import FlowBoxWindow
from presentor.constants import __app_id__, __app_title__, __image_size__, __max_image_count__

class PresentorApplication(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id=__app_id__, flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.connect("startup", self.on_startup)
        self.connect("activate",self.on_activate)
        self.connect("open",self.on_open)
        self.connect("shutdown",self.on_shutdown)

    def on_startup(self, data=None):
        notify2.init(__app_title__)
        try:
            Gtk.Window.set_default_icon_name(__app_id__)
            self.win = FlowBoxWindow(self, __image_size__, __max_image_count__)
            self.add_window(self.win)
        except Error as e:
            print(e)
            self.show_notification("Irgendwas ging schief", e.message, "dialog-error")
            self.quit()

    def on_activate(self, data=None):
        self.win.show_all()

    def on_open(self, app, files, hint, data=None):
        self.win.show_all()
        self.win.load_images(files[0])

    def on_shutdown(self, app, data=None):
        try:
            folder = self.win.choose_folder.get_file()
            if folder is not None:
                mount_point = folder.find_enclosing_mount().get_default_location().get_path()
                subprocess.check_call(["umount",mount_point])
                self.show_notification("Speicherkarte wurde gesichert","Sie können die Speicherkarte nun entfernen","dialog-information")
        except subprocess.CalledProcessError as e:
            self.show_notification("Speicherkarte konnte nicht sicher entfernt werden", "", "dialog-error")
        except Error as e:
            print(e)
        finally:
            os.sync()

    def show_notification(self, summary, body=None, icon=None):
        n = notify2.Notification(summary, body, icon)
        n.show()

def main():
    threads_init()
    app = PresentorApplication()
    app.run(sys.argv)

if __name__ == "__main__":
    main()