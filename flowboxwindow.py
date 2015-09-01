import os

from threading import Thread

from gi.repository import Gtk, GLib

from gi.repository.GdkPixbuf import PixbufRotation
from gi.repository.Gio import app_info_get_default_for_type
from gi.repository.Gdk import KEY_Escape, ModifierType
from imagebox import ImageBox, ImageFlowBox

class FlowBoxWindow(Gtk.ApplicationWindow):
    def __init__(self, application, image_size, max_image_count):
        Gtk.ApplicationWindow.__init__(self, application=application, title="Fotostudio Schaal", type=Gtk.WindowType.TOPLEVEL)

        self.image_size = image_size
        self.max_image_count = max_image_count

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

        self.loading_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)

        loading_image = Gtk.Image.new_from_file("logo.svg")

        self.loading_stack.add_named(loading_image, "loading")
        self.loading_stack.add_named(scrolled, "imagebox")

        mainbox.pack_start(self.loading_stack, True, True, 0)
        mainbox.pack_end(actionbar, False, True, 0)

        self.add(mainbox)
        self.flowbox.grab_focus()

    def on_quit_requested(self, *args):
        self.get_application().quit()

    def set_loading(self,loading):
        if loading:
            self.loading_stack.set_visible_child_name("loading")
        else:
            self.loading_stack.set_visible_child_name("imagebox")

    def _load_images(self, path):
        self.set_loading(True)
        self.flowbox.clear()
        self.choose_folder.set_file(path)
        Thread(target=self._load_images_thread, args=(path,)).start()

    def _load_images_finished(self):
        self.flowbox.show_all()

        self.set_loading(False)

    def _insert_imagebox(self, image_path):
        imagebox = ImageBox(image_path, self.image_size)
        self.flowbox.add(imagebox)
        imagebox.show_all()

    def _load_images_thread(self, path):
        image_count = 0
        for root, dirnames, filenames in os.walk(path.get_path()):
            for image_path in [os.path.join(root,filename) for filename in filenames if filename.lower().endswith(".jpg")]:
                GLib.idle_add(self._insert_imagebox,image_path)
                image_count += 1
                if image_count >= self.max_image_count:
                    GLib.idle_add(self.set_loading, False)
                    return

    def on_file_set(self, choose_folder):
        self._load_images(choose_folder.get_file())

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
