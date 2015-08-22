#!/usr/bin/python3

import os,sys
from gi.repository import Gtk, GdkPixbuf, Gio, Gdk

SIZE = 500

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

    def on_item_activated(self,flowbox,child,window):
        image_file = child.get_child().image_file

        dialog = Gtk.AppChooserDialog.new(window,Gtk.DialogFlags.MODAL,image_file)

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

    def handle_key_release(self, widget, event, data=None):
        if event.keyval == Gdk.KEY_q:
            self.on_rotate_clicked(None, GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE)
        elif event.keyval == Gdk.KEY_w:
            self.on_rotate_clicked(None, GdkPixbuf.PixbufRotation.CLOCKWISE)
        elif event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()

class FlowBoxWindow(Gtk.Window):
    def __init__(self,matches):
        Gtk.Window.__init__(self, title="Fotostudio Schaal")

        self.maximize()

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        mainbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        flowbox = ImageFlowBox()
        actionbar = Gtk.ActionBar.new()

        rotate_left = Gtk.Button.new_from_icon_name('object-rotate-left',Gtk.IconSize.BUTTON)
        rotate_right = Gtk.Button.new_from_icon_name('object-rotate-right',Gtk.IconSize.BUTTON)

        actionbar.pack_start(rotate_left)
        actionbar.pack_start(rotate_right)

        rotate_left.connect('clicked',flowbox.on_rotate_clicked,GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE)
        rotate_right.connect('clicked',flowbox.on_rotate_clicked,GdkPixbuf.PixbufRotation.CLOCKWISE)
        flowbox.connect('child_activated',flowbox.on_item_activated,self)

        self.connect("delete-event", Gtk.main_quit)
        self.connect("key-release-event", flowbox.handle_key_release)

        for image_path in matches:
            imagebox = ImageBox(image_path)
            flowbox.add(imagebox)

        scrolled.add(flowbox)

        mainbox.pack_start(scrolled, True, True, 0)
        mainbox.pack_end(actionbar, False, True, 0)

        self.add(mainbox)
        self.show_all()

if len(sys.argv) == 2:
    matches = []
    for root, dirnames, filenames in os.walk(sys.argv[1]):
        matches.extend([os.path.join(root, filename) for filename in filenames if filename.lower().endswith(".jpg")])

    win = FlowBoxWindow(matches)

    Gtk.main()
