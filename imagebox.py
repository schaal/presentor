from gi.repository import Gtk, Gio

from gi.repository.Gdk import KEY_q, KEY_w, KEY_Escape
from gi.repository.GLib import Error
from gi.repository.GdkPixbuf import Pixbuf, PixbufRotation

class ImageBox(Gtk.Box):
    def _set_image_callback(self, source_object, res):
        try:
            pixbuf = Pixbuf.new_from_stream_finish(res).apply_embedded_orientation()
            self.image_widget.set_from_pixbuf(pixbuf)
        except Error as e:
            self.image_widget.set_from_icon_name('dialog-error', Gtk.IconSize.DIALOG)
            self.image_widget.set_size_request(-1,-1)
            self.image_label.set_markup("{0}\n<b>{1}</b>".format(self.image_label.get_label(),e.message))

    def __init__(self, image_path, image_size):
        Gtk.Box.__init__(self)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(5)
        self.set_size_request(image_size, image_size)

        self.image_file = Gio.File.new_for_path(image_path)
        self.image_widget = Gtk.Image.new()

        self.image_label = Gtk.Label.new(self.image_file.get_basename())
        self.image_label.set_justify(Gtk.Justification.CENTER)

        Pixbuf.new_from_stream_at_scale_async(self.image_file.read(), image_size, image_size,True,None,self._set_image_callback)

        self.set_center_widget(self.image_widget)
        self.pack_end(self.image_label, True, True, 0)

class ImageFlowBox(Gtk.FlowBox):
    def __init__(self):
        Gtk.FlowBox.__init__(self)

        self.set_valign(Gtk.Align.START)
        self.set_max_children_per_line(30)
        self.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.set_activate_on_single_click(False)

    def on_rotate_clicked(self, button, direction):
        if self.get_selected_children():
            image = self.get_selected_children()[0].get_child().get_center_widget()
            pixbuf = image.get_pixbuf()
            rotated = pixbuf.rotate_simple(direction)
            image.set_from_pixbuf(rotated)

    def handle_key_release(self, widget, event, window):
        if event.keyval == KEY_q:
            self.on_rotate_clicked(None, PixbufRotation.COUNTERCLOCKWISE)
        elif event.keyval == KEY_w:
            self.on_rotate_clicked(None, PixbufRotation.CLOCKWISE)
        elif event.keyval == KEY_Escape:
            window.get_application().quit()

    def clear(self):
        self.foreach(self.remove)
