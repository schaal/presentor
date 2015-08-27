#!/usr/bin/python3

import os,sys,subprocess,notify2
from subprocess import CalledProcessError
from gi.repository import Gtk, GdkPixbuf, Gio, Gdk

SIZE = 500
MAX_IMAGE_COUNT = 100

class ImageBox(Gtk.Box):
    def _set_image_callback(self, source_object, res):
        pixbuf = GdkPixbuf.Pixbuf.new_from_stream_finish(res)
        pixbuf.apply_embedded_orientation()
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
            window._cleanup()

    def clear(self):
        self.foreach(self.remove)

class FlowBoxWindow(Gtk.Window):
    def __init__(self, path=None):
        Gtk.Window.__init__(self, title="Fotostudio Schaal")

        self.maximize()

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        mainbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        self.flowbox = ImageFlowBox()
        actionbar = Gtk.ActionBar.new()

        rotate_left = Gtk.Button.new_from_icon_name('object-rotate-left',Gtk.IconSize.BUTTON)
        rotate_right = Gtk.Button.new_from_icon_name('object-rotate-right',Gtk.IconSize.BUTTON)
        choose_folder = Gtk.FileChooserButton.new('Ordner auswählen', Gtk.FileChooserAction.SELECT_FOLDER)

        actionbar.pack_start(rotate_left)
        actionbar.pack_start(rotate_right)
        actionbar.pack_start(choose_folder)

        rotate_left.connect('clicked',self.flowbox.on_rotate_clicked,GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE)
        rotate_right.connect('clicked',self.flowbox.on_rotate_clicked,GdkPixbuf.PixbufRotation.CLOCKWISE)
        self.flowbox.connect('child_activated',self.on_item_activated)
        choose_folder.connect('file-set', self.on_file_set)

        self.connect("destroy-event", self._cleanup)
        self.connect("delete-event", self._cleanup)
        self.connect("key-release-event", self.flowbox.handle_key_release, self)

        if path is not None:
            choose_folder.set_current_folder(path)
            self._load_images(path)

        scrolled.add(self.flowbox)

        mainbox.pack_start(scrolled, True, True, 0)
        mainbox.pack_end(actionbar, False, True, 0)

        self.add(mainbox)
        self.show_all()

    def _load_images(self, path):
        self.flowbox.clear()
        self._load_images_loop(path)
        self.flowbox.show_all()

    def _load_images_loop(self, path):
        image_count = 0
        for root, dirnames, filenames in os.walk(path):
            for image_path in [os.path.join(root,filename) for filename in filenames if filename.lower().endswith(".jpg")]:
                imagebox = ImageBox(image_path)
                self.flowbox.add(imagebox)
                image_count += 1
                if image_count >= MAX_IMAGE_COUNT:
                    return

    def _cleanup(self, widget=None, event=None):
        try:
            subprocess.check_call(["udisksctl","unmount","--block-device","/dev/sdb1"])
            subprocess.check_call(["udisksctl","power-off","--block-device","/dev/sdb"])
            show_notification("Speicherkarte wurde gesichert","Sie können die Speicherkarte nun sicher entfernen","dialog-information")
        except CalledProcessError as e:
            show_notification("Speicherkarte konnte nicht sicher entfernt werden", "Bitte entfernen Sie die Speicherkarte, bevor Sie sie entnehmen", "dialog-error")
        finally:
            os.sync()
            Gtk.main_quit()

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

def show_notification(summary, body=None, icon=None):
    n = notify2.Notification(summary, body, icon)
    n.show()

notify2.init("Fotostudio Schaal")

if len(sys.argv) == 2:
    win = FlowBoxWindow(sys.argv[1])
else:
    win = FlowBoxWindow()

Gtk.main()
