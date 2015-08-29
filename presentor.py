#!/usr/bin/python3

import os,sys,subprocess,notify2
from subprocess import CalledProcessError
from gi.repository import Gtk, GdkPixbuf, Gio, Gdk

APP_ID = "de.fotoschaal.presentor"

SIZE = 500
MAX_IMAGE_COUNT = 100
PARTITION = '/dev/sdf1'

class ImageBox(Gtk.Box):
    def _set_image_callback(self, source_object, res):
        pixbuf = GdkPixbuf.Pixbuf.new_from_stream_finish(res).apply_embedded_orientation()
        self.image_widget.set_from_pixbuf(pixbuf)

    def __init__(self, image_path):
        Gtk.Box.__init__(self)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(5)
        self.set_size_request(SIZE,SIZE)

        self.image_file = Gio.File.new_for_path(image_path)
        self.image_widget = Gtk.Image.new()

        image_label = Gtk.Label()
        image_label.set_text(self.image_file.get_basename())

        GdkPixbuf.Pixbuf.new_from_stream_at_scale_async(self.image_file.read(),SIZE,SIZE,True,None,self._set_image_callback)

        self.set_center_widget(self.image_widget)
        self.pack_end(image_label, True, True, 0)

class ImageFlowBox(Gtk.FlowBox):
    def __init__(self):
        Gtk.FlowBox.__init__(self)

        self.set_valign(Gtk.Align.START)
        self.set_max_children_per_line(30)
        self.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.set_activate_on_single_click(False)

    def on_rotate_clicked(self, button, direction):
        image = self.get_selected_children()[0].get_child().get_center_widget()
        pixbuf = image.get_pixbuf()
        rotated = pixbuf.rotate_simple(direction)
        image.set_from_pixbuf(rotated)

    def handle_key_release(self, widget, event, window):
        if event.keyval == Gdk.KEY_q:
            self.on_rotate_clicked(None, GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE)
        elif event.keyval == Gdk.KEY_w:
            self.on_rotate_clicked(None, GdkPixbuf.PixbufRotation.CLOCKWISE)
        elif event.keyval == Gdk.KEY_Escape:
            window.get_application().quit()

    def clear(self):
        self.foreach(self.remove)

class FlowBoxWindow(Gtk.Window):
    def __init__(self, path=None):
        Gtk.Window.__init__(self, title="Fotostudio Schaal", type=Gtk.WindowType.TOPLEVEL)

        self.maximize()

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        mainbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.flowbox = ImageFlowBox()
        actionbar = Gtk.ActionBar.new()

        rotate_left = Gtk.Button.new_from_icon_name('object-rotate-left',Gtk.IconSize.BUTTON)
        rotate_right = Gtk.Button.new_from_icon_name('object-rotate-right',Gtk.IconSize.BUTTON)
        self.choose_folder = Gtk.FileChooserButton.new('Ordner auswählen', Gtk.FileChooserAction.SELECT_FOLDER)

        actionbar.pack_start(rotate_left)
        actionbar.pack_start(rotate_right)
        actionbar.pack_start(self.choose_folder)

        rotate_left.connect('clicked',self.flowbox.on_rotate_clicked,GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE)
        rotate_right.connect('clicked',self.flowbox.on_rotate_clicked,GdkPixbuf.PixbufRotation.CLOCKWISE)
        self.flowbox.connect('child_activated',self.on_item_activated)
        self.choose_folder.connect('file-set', self.on_file_set)

        self.connect("key-release-event", self.flowbox.handle_key_release, self)

        scrolled.add(self.flowbox)

        mainbox.pack_start(scrolled, True, True, 0)
        mainbox.pack_end(actionbar, False, True, 0)

        self.add(mainbox)
        self.show_all()

    def _load_images(self, path):
        self.flowbox.clear()
        self.choose_folder.set_current_folder_file(path)
        self._load_images_loop(path)
        self.flowbox.show_all()

    def _load_images_loop(self, path):
        image_count = 0
        for root, dirnames, filenames in os.walk(path.get_path()):
            for image_path in [os.path.join(root,filename) for filename in filenames if filename.lower().endswith(".jpg")]:
                imagebox = ImageBox(image_path)
                self.flowbox.add(imagebox)
                image_count += 1
                if image_count >= MAX_IMAGE_COUNT:
                    return

    def on_file_set(self, choose_folder):
        self._load_images(choose_folder.get_filename())

    def on_item_activated(self, flowbox, child):
        image_file = child.get_child().image_file

        dialog = Gtk.AppChooserDialog.new(self,Gtk.DialogFlags.MODAL,image_file)

        widget = dialog.get_widget()
        widget.set_show_default(True)

        content_type = widget.get_content_type()

        default_app_info = Gio.app_info_get_default_for_type(content_type, False)

        if default_app_info is not None:
            default_app_info.launch([image_file], None)
        else:
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                appinfo = dialog.get_app_info()
                appinfo.set_as_default_for_type(content_type)
                appinfo.launch([image_file], None)
        dialog.destroy()

class PresentorApplication(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.connect("startup", self.on_startup)
        self.connect("activate",self.on_activate)
        self.connect("open",self.on_open)
        self.connect("shutdown",self.on_shutdown)

    def on_startup(self, data=None):
        notify2.init("Fotostudio Schaal")
        self.win = FlowBoxWindow()
        self.add_window(self.win)

    def on_activate(self, data=None):
        self.win.show_all()

    def on_open(self, app, files, hint, data=None):
        self.win._load_images(files[0])
        self.win.show_all()

    def on_shutdown(self, app, data=None):
        try:
            subprocess.check_call(["udisksctl","unmount","--block-device",PARTITION])
            self.show_notification("Speicherkarte wurde gesichert","Sie können die Speicherkarte nun sicher entfernen","dialog-information")
        except CalledProcessError as e:
            self.show_notification("Speicherkarte konnte nicht sicher entfernt werden", "Bitte entfernen Sie die Speicherkarte, bevor Sie sie entnehmen", "dialog-error")
        finally:
            os.sync()

    def show_notification(self, summary, body=None, icon=None):
        n = notify2.Notification(summary, body, icon)
        n.show()

if __name__ == "__main__":
    app = PresentorApplication()
    app.run(sys.argv)
