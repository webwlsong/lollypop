#!/usr/bin/python
# Copyright (c) 2014-2015 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GLib, Gio, GdkPixbuf

from _thread import start_new_thread
import urllib.request

from lollypop.define import Lp


# Show ArtistInfos in a popover
class PopArtistInfos(Gtk.Popover):
    """
        Init popover
    """
    def __init__(self, artist):
        Gtk.Popover.__init__(self)
        self._infos = ArtistInfos(artist)
        self._infos.show()
        self.add(self._infos)

    """
        Populate view
    """
    def populate(self):
        self._infos.populate()


# Show artist informations from lastfm
class ArtistInfos(Gtk.Bin):
    """
        Init artist infos
        @param artist as str
    """
    def __init__(self, artist):
        Gtk.Bin.__init__(self)
        self._artist = artist
        self._stack = Gtk.Stack()
        self._stack.set_property('expand', True)
        self._stack.show()

        builder = Gtk.Builder()
        builder.add_from_resource('/org/gnome/Lollypop/ArtistInfos.ui')
        builder.connect_signals(self)
        widget = builder.get_object('widget')
        widget.attach(self._stack, 0, 2, 2, 1)

        self._back_btn = builder.get_object('back_btn')
        self._image =  builder.get_object('image')
        self._content =  builder.get_object('content')

        builder.get_object('artist').set_text(artist)

        self._scrolled = builder.get_object('scrolled') 
        self._spinner = builder.get_object('spinner')
        self._not_found = builder.get_object('notfound')
        self._stack.add(self._spinner)
        self._stack.add(self._not_found)
        self._stack.add(self._scrolled)
        self._stack.set_visible_child(self._spinner)
        self.add(widget)

    """
        Populate informations and artist image
    """
    def populate(self):
        start_new_thread(self._populate, ())

    """
        Resize popover and set signals callback
    """
    def do_show(self):
        size_setting = Lp.settings.get_value('window-size')
        if isinstance(size_setting[1], int):
            self.set_size_request(700, size_setting[1]*0.7)
        else:
            self.set_size_request(700, 400)
        Gtk.Popover.do_show(self)

    """
        Preferred width
    """
    def do_get_preferred_width(self):
        return (700, 700)

#######################
# PRIVATE             #
#######################
    """
        Same as _populate()
        @thread safe
    """
    def _populate(self):
        (url, content) = Lp.lastfm.get_artist_infos(self._artist)
        stream = None
        try:
            response = urllib.request.urlopen(url)
            stream = Gio.MemoryInputStream.new_from_data(response.read(), None)
        except Exception as e:
            print("PopArtistInfos::_populate: %s" %e)
            content = None
        GLib.idle_add(self._set_content, content, stream)

    """
        Set content on view
        @param content as str
        @param stream as Gio.MemoryInputStream
    """
    def _set_content(self, content, stream):
        if content is not None:
            self._stack.set_visible_child(self._scrolled)
            self._content.set_markup(content)
        else:
            self._stack.set_visible_child(self._not_found)
        if stream is not None:
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
            self._image.set_from_pixbuf(pixbuf)
            del pixbuf

    """
        Go to previous URL
        @param btn as Gtk.Button
    """
    def _on_back_btn_clicked(self, btn):
        self.destroy()
