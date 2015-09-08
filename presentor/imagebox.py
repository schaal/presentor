import sys

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
            print(e, file=sys.stderr)
            self.image_widget.set_from_icon_name('dialog-error', Gtk.IconSize.DIALOG)
            self.set_size_request(-1,-1)
            self.set_markup("{0}\n<b>{1}</b>".format(self.image_label.get_label(),e.message))

    def set_markup(self, markup):
        self.image_label.set_markup(markup)

    def rotate_image(self, direction):
        pixbuf = self.image_widget.get_pixbuf().rotate_simple(direction)
        self.image_widget.set_from_pixbuf(pixbuf)

    def __init__(self, image_path, image_size=None, markup=None):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.image_file = Gio.File.new_for_path(image_path)
        self.image_widget = Gtk.Image()

        self.image_label = Gtk.Label(label=self.image_file.get_basename(), justify=Gtk.Justification.CENTER)

        if markup is not None:
            self.set_markup(markup)

        self.set_center_widget(self.image_widget)
        self.pack_end(self.image_label, True, True, 0)

        if image_size is not None:
            self.set_size_request(image_size, image_size)
            Pixbuf.new_from_stream_at_scale_async(self.image_file.read(), image_size, image_size,True,None,self._set_image_callback)
        else:
            Pixbuf.new_from_stream_async(self.image_file.read(),None,self._set_image_callback)

class ImageFlowBox(Gtk.FlowBox):
    def __init__(self, accel):
        Gtk.FlowBox.__init__(self, valign=Gtk.Align.FILL, halign=Gtk.Align.FILL, max_children_per_line=5, activate_on_single_click=False,selection_mode=Gtk.SelectionMode.SINGLE)
        accel.connect(KEY_q, 0, 0, self._on_accel_activated)
        accel.connect(KEY_w, 0, 0, self._on_accel_activated)

    def _on_accel_activated(self, accel_group, acceleratable, keyval, modifier):
        if keyval == KEY_q:
            self.on_rotate_clicked(None, PixbufRotation.COUNTERCLOCKWISE)
        elif keyval == KEY_w:
            self.on_rotate_clicked(None, PixbufRotation.CLOCKWISE)

    def on_rotate_clicked(self, button, direction):
        if self.get_selected_children():
            self.get_selected_children()[0].get_child().rotate_image(direction)

    def clear(self):
        self.foreach(self.remove)
