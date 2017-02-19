#!/usr/bin/python3

import os
import sys
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk, Gio, Notify
from gi.repository.GLib import Error
from gi.repository.GObject import threads_init

from presentor.flowboxwindow import FlowBoxWindow
from presentor.constants import __app_id__, __image_size__, __max_image_count__

class PresentorApplication(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id=__app_id__,
                                 flags=Gio.ApplicationFlags.HANDLES_OPEN)

        self.win = None

        self.connect("startup", self.on_startup)
        self.connect("activate", self.on_activate)
        self.connect("open", self.on_open)
        self.connect("shutdown", self.on_shutdown)

    def on_startup(self, data=None):
        Notify.init(__app_id__)
        try:
            Gtk.Window.set_default_icon_name(__app_id__)
            self.win = FlowBoxWindow(self, __image_size__, __max_image_count__)
            self.add_window(self.win)
        except:
            e = sys.exc_info()[1]
            print(e, file=sys.stderr)
            self.show_notification("Irgendwas ging schief", str(e), "dialog-error")
            self.quit()

    def on_activate(self, data=None):
        self.win.show_all()

    def on_open(self, app, files, hint, data=None):
        self.win.show_all()
        self.win.load_images(files[0])

    def on_shutdown(self, app, data=None):
        self.unmount()

    def unmount(self, button=None):
        folder = self.win.choose_folder.get_file()
        try:
            if folder is not None and folder.has_prefix(Gio.File.new_for_path("/media")):
                mount_point = folder.find_enclosing_mount().get_default_location().get_path()
                subprocess.check_call(["umount", mount_point])
        except (subprocess.CalledProcessError, Error) as ex: # pylint: disable=E0712
            self.show_notification(
                "Speicherkarte konnte nicht sicher entfernt werden", "", "dialog-error")
            print(ex, file=sys.stderr)
        finally:
            os.sync()

    def show_notification(self, summary, body=None, icon=None):
        notification = Notify.Notification(summary=summary, body=body)
        notification.set_property("icon-name", icon)
        notification.set_app_name(__app_id__)
        notification.show()

def main():
    threads_init()
    app = PresentorApplication()
    app.run(sys.argv)

if __name__ == "__main__":
    main()
