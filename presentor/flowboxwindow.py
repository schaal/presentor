import os
import xdg.BaseDirectory

from threading import Thread, Lock

from gi.repository import Gtk, GLib

from gi.repository.GdkPixbuf import PixbufRotation
from gi.repository.Gio import app_info_get_default_for_type, content_type_guess
from gi.repository.Gdk import KEY_Escape, ModifierType

from presentor.imagebox import ImageBox, ImageFlowBox
from presentor.constants import __app_id__, __app_title__

class FlowBoxWindow(Gtk.ApplicationWindow):
    def __init__(self, application, image_size, max_image_count):
        Gtk.ApplicationWindow.__init__(self, application=application, title=__app_title__, type=Gtk.WindowType.TOPLEVEL)

        self.image_size = image_size
        self.max_image_count = max_image_count

        self.quit_requested = False
        self.lock = Lock()
        self.maximize()

        accel = Gtk.AccelGroup()
        accel.connect(KEY_Escape, 0, 0, self.on_quit_requested)
        self.add_accel_group(accel)

        scrolled = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)

        mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.flowbox = ImageFlowBox(accel)
        actionbar = Gtk.ActionBar()

        rotate_left = Gtk.Button.new_from_icon_name('object-rotate-left',Gtk.IconSize.BUTTON)
        rotate_right = Gtk.Button.new_from_icon_name('object-rotate-right',Gtk.IconSize.BUTTON)
        self.choose_folder = Gtk.FileChooserButton(title='Ordner auswählen', action=Gtk.FileChooserAction.SELECT_FOLDER)

        actionbar.pack_start(rotate_left)
        actionbar.pack_start(rotate_right)
        actionbar.pack_start(self.choose_folder)

        rotate_left.connect('clicked', self.flowbox.on_rotate_clicked, PixbufRotation.COUNTERCLOCKWISE)
        rotate_right.connect('clicked', self.flowbox.on_rotate_clicked, PixbufRotation.CLOCKWISE)
        self.flowbox.connect('child_activated',self.on_item_activated)
        self.choose_folder.connect('file-set', self.on_file_set)

        scrolled.add(self.flowbox)

        self.loading_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.NONE)

        try:
            logo = self._get_resource_path("logo.svg")
            if logo is not None:
                loading_image = Gtk.Image.new_from_file(logo)
                self.loading_stack.add_named(loading_image, "loading")
        except GLib.Error as e:
            print(e)

        self.loading_stack.add_named(scrolled, "imagebox")

        mainbox.pack_start(self.loading_stack, True, True, 0)
        mainbox.pack_end(actionbar, False, True, 0)

        self.add(mainbox)
        self.flowbox.grab_focus()

    def _get_resource_path(self, resource_name):
        data_paths = xdg.BaseDirectory.load_data_paths(os.path.join(__app_id__,resource_name))
        data_path = None
        for x in data_paths:
            data_path = x
            break
        return data_path

    def on_quit_requested(self, *args):
        self.quit_requested = True
        self.get_application().quit()

    def set_loading(self,loading):
        self.choose_folder.set_sensitive(not loading)
        self.loading_stack.set_visible_child_name("imagebox")

    def load_images(self, path):
        self.set_loading(True)
        self.flowbox.clear()
        self.choose_folder.set_file(path)
        Thread(target=self._load_images_thread, args=(path,self.lock)).start()

    def _insert_imagebox(self, image_path):
        imagebox = ImageBox(image_path, self.image_size)
        self.flowbox.add(imagebox)
        imagebox.show_all()

    def _load_images_thread(self, path, lock):
        with lock:
            try:
                image_count = 0
                for root, dirnames, filenames in os.walk(path.get_path()):
                    for image_path in [os.path.join(root,filename) for filename in filenames if content_type_guess(filename)[0].startswith("image/")]:
                        GLib.idle_add(self._insert_imagebox,image_path)
                        image_count += 1
                        if image_count >= self.max_image_count or self.quit_requested:
                            return
            finally:
                GLib.idle_add(self.set_loading, False)


    def on_file_set(self, choose_folder):
        self.load_images(choose_folder.get_file())

    def on_item_activated(self, flowbox, child):
        image_file = child.get_child().image_file

        dialog = Gtk.AppChooserDialog(parent=self, flags=Gtk.DialogFlags.MODAL, gfile=image_file)

        widget = dialog.get_widget()
        widget.set_show_default(True)

        content_type = widget.get_content_type()

        default_app_info = app_info_get_default_for_type(content_type, False)

        if default_app_info is not None:
            default_app_info.launch([image_file], None)
        else:
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                appinfo = dialog.get_app_info()
                appinfo.set_as_default_for_type(content_type)
                appinfo.launch([image_file], None)
        dialog.destroy()
