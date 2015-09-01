import os

from gi.repository import Gtk

from gi.repository.GdkPixbuf import PixbufRotation
from gi.repository.Gio import app_info_get_default_for_type

from imagebox import ImageBox, ImageFlowBox

class FlowBoxWindow(Gtk.ApplicationWindow):
    def __init__(self, application, image_size, max_image_count):
        Gtk.ApplicationWindow.__init__(self, application=application, title="Fotostudio Schaal", type=Gtk.WindowType.TOPLEVEL)

        self.image_size = image_size
        self.max_image_count = max_image_count

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

        rotate_left.connect('clicked', self.flowbox.on_rotate_clicked, PixbufRotation.COUNTERCLOCKWISE)
        rotate_right.connect('clicked', self.flowbox.on_rotate_clicked, PixbufRotation.CLOCKWISE)
        self.flowbox.connect('child_activated',self.on_item_activated)
        self.choose_folder.connect('file-set', self.on_file_set)

        self.connect("key-release-event", self.flowbox.handle_key_release, self)

        scrolled.add(self.flowbox)

        mainbox.pack_start(scrolled, True, True, 0)
        mainbox.pack_end(actionbar, False, True, 0)

        self.add(mainbox)
        self.flowbox.grab_focus()
        #self.show_all()

    def _load_images(self, path):
        self.flowbox.clear()
        self.choose_folder.set_file(path)
        self._load_images_loop(path)
        self.flowbox.show_all()

    def _load_images_loop(self, path):
        image_count = 0
        for root, dirnames, filenames in os.walk(path.get_path()):
            for image_path in [os.path.join(root,filename) for filename in filenames if filename.lower().endswith(".jpg")]:
                imagebox = ImageBox(image_path, self.image_size)
                self.flowbox.add(imagebox)
                image_count += 1
                if image_count >= self.max_image_count:
                    return

    def on_file_set(self, choose_folder):
        self._load_images(choose_folder.get_file())

    def on_item_activated(self, flowbox, child):
        image_file = child.get_child().image_file

        dialog = Gtk.AppChooserDialog.new(self,Gtk.DialogFlags.MODAL,image_file)

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
