from gi.repository import Gtk, GdkPixbuf, GLib

from gi.repository.Gdk import KEY_q, KEY_w, KEY_Escape

class ImageBox(Gtk.Box):
    def _set_image_callback(self, source_object, res):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream_finish(res).apply_embedded_orientation()
            self.image_widget.set_from_pixbuf(pixbuf)
        except GLib.Error as e:
            #TODO: show error
            pass

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
        if self.get_selected_children():
            image = self.get_selected_children()[0].get_child().get_center_widget()
            pixbuf = image.get_pixbuf()
            rotated = pixbuf.rotate_simple(direction)
            image.set_from_pixbuf(rotated)

    def handle_key_release(self, widget, event, window):
        if event.keyval == KEY_q:
            self.on_rotate_clicked(None, GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE)
        elif event.keyval == KEY_w:
            self.on_rotate_clicked(None, GdkPixbuf.PixbufRotation.CLOCKWISE)
        elif event.keyval == KEY_Escape:
            window.get_application().quit()

    def clear(self):
        self.foreach(self.remove)
