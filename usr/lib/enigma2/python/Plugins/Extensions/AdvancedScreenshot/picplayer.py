#!/usr/bin/python
# -*- coding: utf-8 -*-

# AdvancedScreenshot
from __future__ import print_function

# Standard library
from os import listdir, remove
from os.path import exists as file_exists, isdir, isfile, join

# Enigma2 core
from enigma import ePicLoad, eTimer, getDesktop

# Enigma2 Screens/Components
try:
    from Components.AVSwitch import AVSwitch
except ImportError:
    from Components.AVSwitch import eAVControl as AVSwitch
from Components.ActionMap import ActionMap
from Components.Pixmap import MovingPixmap, Pixmap
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen

from . import _


def get_scale():
    """Get framebuffer scale.

    Returns:
        Tuple (scale_x, scale_y) or (1, 1) on error
    """
    return AVSwitch().getFramebufferScale()


# Constants for filelist tuple indices
T_INDEX = 0
T_FRAME_POS = 1
T_PAGE = 2
T_NAME = 3
T_FULL = 4


class Galery_Thumb(Screen):
    """Thumbnail gallery screen for browsing images."""

    def __init__(self, session, piclist, lastindex, path):
        """Initialize thumbnail gallery.

        Args:
            session: Session object
            piclist: List of picture filenames
            lastindex: Last selected index
            path: Path to pictures
        """
        self.textcolor = "#ffffff"
        self.color = "#009eb9ff"
        textsize = 35
        self.space_x = 50
        self.pic_x = 400
        self.space_y = 10
        self.pic_y = 320

        size_w = getDesktop(0).size().width()
        size_h = getDesktop(0).size().height()

        self.thumbs_x = size_w // (self.space_x + self.pic_x)
        self.thumbs_y = size_h // (self.space_y + self.pic_y)
        self.thumbs_count = int(round(self.thumbs_x * self.thumbs_y))
        self.positionlist = []

        skincontent = ""

        # Generate skin for thumbnails
        for x in range(self.thumbs_count):
            pos_x = x % self.thumbs_x
            pos_y = x // self.thumbs_x
            abs_x = self.space_x + pos_x * (self.space_x + self.pic_x)
            abs_y = self.space_y + pos_y * (self.space_y + self.pic_y)

            self.positionlist.append((abs_x, abs_y))

            label_pos = abs_y + self.pic_y - textsize
            thumb_pos_x = abs_x + 5
            thumb_pos_y = abs_y + 5
            thumb_h = self.pic_y - textsize * 2

            # Label skin
            skincontent += ('<widget source="label' + str(x) + '" render="Label" '
                            'position="' + str(abs_x) + ',' + str(label_pos) + '" '
                            'size="' + str(self.pic_x) + ',' + str(textsize) + '" '
                            'halign="center" font="Regular;24" zPosition="2" '
                            'transparent="1" noWrap="1" foregroundColor="' +
                            self.textcolor + '" />\n')

            # Thumbnail skin
            skincontent += (
                '<widget name="thumb' + str(x) + '" '
                'position="' + str(thumb_pos_x) + ',' + str(thumb_pos_y) + '" '
                'size="' + str(self.pic_x - 10) + ',' + str(thumb_h) + '" '
                'zPosition="2" transparent="1" alphatest="on" />\n'
            )

        # Build complete skin
        skinthumb = ('<screen name="Galery_Thumb" position="center,center" size="' +
                     str(size_w) + ',' + str(size_h) + '" flags="wfNoBorder">\n')
        skinthumb += ('<eLabel position="0,0" zPosition="1" size="' +
                      str(size_w) + ',' + str(size_h) + '" backgroundColor="' +
                      self.color + '" halign="center" />\n')
        skinthumb += ('<widget name="frame" position="35,30" size="' +
                      str(self.pic_x + 5) + ',' + str(self.pic_y + 10) +
                      '" scale="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AdvancedScreenshot/images/pic_frame.png" alphatest="on" zPosition="3"/>\n')
        skinthumb += skincontent
        skinthumb += '</screen>\n'

        self.skin = skinthumb

        Screen.__init__(self, session)
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions", "MovieSelectionActions"], {
                "cancel": self.exit,
                "ok": self.key_ok,
                "left": self.key_left,
                "right": self.key_right,
                "up": self.key_up,
                "down": self.key_down
            }, -1
        )

        self['frame'] = MovingPixmap()
        for x in range(self.thumbs_count):
            self['label' + str(x)] = StaticText()
            self['thumb' + str(x)] = Pixmap()

        self.thumbnail_list = []
        self.filelist = []
        self.curr_page = -1
        self.dirlist_count = 0
        self.path = path
        index = 0
        frame_pos = 0
        page = 0

        # Build filelist with metadata
        for filename in piclist:
            if filename:
                self.filelist.append((
                    index,
                    frame_pos,
                    page,
                    filename,
                    path + filename
                ))
                index += 1
                frame_pos += 1
                if frame_pos > self.thumbs_count - 1:
                    frame_pos = 0
                    page += 1
            else:
                self.dirlist_count += 1

        self.max_entry = len(self.filelist) - 1
        self.index = int(lastindex) - self.dirlist_count
        if self.index < 0:
            self.index = 0

        self.picload = ePicLoad()
        if self.picload.PictureData is not None:
            try:
                self.picload.PictureData.get().append(self.show_pic)
            except:
                self.picload.PictureData.connect(self.show_pic)

        self.thumb_timer = eTimer()
        self.thumb_timer.callback.append(self.show_pic)
        self.onLayoutFinish.append(self.set_picload_conf)

    def set_picload_conf(self):
        """Configure picture loader."""
        scale = get_scale()
        scale_x = scale[0] if isinstance(scale[0], (int, float)) else 1
        scale_y = scale[1] if isinstance(scale[1], (int, float)) else 1

        try:
            self.picload.setPara([
                self['thumb0'].instance.size().width(),
                self['thumb0'].instance.size().height(),
                scale_x,
                scale_y,
                False,
                1,
                self.color
            ])
        except Exception as e:
            print("[Galery_Thumb] set_picload_conf Error: " + str(e))
            return

        self.paint_frame()

    def paint_frame(self):
        """Paint selection frame around current thumbnail."""
        if self.max_entry < self.index or self.index < 0:
            return

        pos = self.positionlist[self.filelist[self.index][T_FRAME_POS]]
        self['frame'].moveTo(pos[0], pos[1], 1)
        self['frame'].startMoving()

        if self.curr_page is not self.filelist[self.index][T_PAGE]:
            self.curr_page = self.filelist[self.index][T_PAGE]
            self.new_page()

    def new_page(self):
        """Load new page of thumbnails."""
        self.thumbnail_list = []

        # Clear all thumbnails
        for x in range(self.thumbs_count):
            self['label' + str(x)].setText('')
            self['thumb' + str(x)].hide()

        # Load thumbnails for current page
        for item in self.filelist:
            if item[T_PAGE] is self.curr_page:
                self['label' + str(item[T_FRAME_POS])].setText(
                    '(' + str(item[T_INDEX] + 1) + ') ' + item[T_NAME]
                )
                self.thumbnail_list.append([
                    0,  # Status: 0=not loaded, 1=loading, 2=loaded
                    item[T_FRAME_POS],
                    item[T_FULL]
                ])

        self.show_pic()

    def show_pic(self, pic_info=''):
        """Show thumbnail pictures.

        Args:
            pic_info: Picture information (not used)
        """
        for i in range(len(self.thumbnail_list)):
            img_path = self.thumbnail_list[i][2]

            if not file_exists(img_path):
                print("[Galery_Thumb] Error: File not found: " + str(img_path))
                return

            if self.thumbnail_list[i][0] == 0:  # Not loaded
                result = self.picload.getThumbnail(img_path)
                if result == 1:
                    self.thumb_timer.start(500, True)
                elif result == -1:
                    print("Error loading thumbnail for " + img_path)
                    return
                else:
                    self.thumbnail_list[i][0] = 1  # Loading
                break

            elif self.thumbnail_list[i][0] == 1:  # Loading
                self.thumbnail_list[i][0] = 2  # Loaded
                ptr = self.picload.getData()

                if ptr is None:
                    print("Error: self.PicLoad.getData() returned None")
                    print("[Galery_Thumb] show_pic: returned None: " + str(img_path))
                    return

                try:
                    thumb_widget = 'thumb' + str(self.thumbnail_list[i][1])
                    self[thumb_widget].instance.setPixmap(ptr)
                    self[thumb_widget].show()
                except Exception as e:
                    print("[Galery_Thumb] show_pic Error while setPixmap: " + str(e))

    def key_left(self):
        """Handle left key press."""
        self.index -= 1
        if self.index < 0:
            self.index = self.max_entry
        self.paint_frame()

    def key_right(self):
        """Handle right key press."""
        self.index += 1
        if self.index > self.max_entry:
            self.index = 0
        self.paint_frame()

    def key_up(self):
        """Handle up key press."""
        self.index -= self.thumbs_x
        if self.index < 0:
            self.index = self.max_entry
        self.paint_frame()

    def key_down(self):
        """Handle down key press."""
        self.index += self.thumbs_x
        if self.index > self.max_entry:
            self.index = 0
        self.paint_frame()

    def key_ok(self):
        """Handle OK key press."""
        if self.max_entry < 0:
            return

        self.old_index = self.index
        self.session.openWithCallback(
            self.callback_view,
            Pic_Full_View,
            self.filelist,
            self.index,
            self.path
        )

    def callback_view(self, val=0):
        """Callback from full view screen.

        Args:
            val: New index from full view
        """
        self.index = val
        if self.old_index is not self.index:
            self.paint_frame()

    def exit(self):
        """Exit gallery."""
        del self.picload
        self.remove_thumbnails()
        self.close(self.index + self.dirlist_count)

    def remove_thumbnails(self):
        """Remove thumbnail cache files."""
        import glob
        thumbnail_dir = glob.glob(self.path)
        if thumbnail_dir:
            thumbnail_dir = str(thumbnail_dir[0]) + '.Thumbnails'
            if file_exists(thumbnail_dir) and isdir(thumbnail_dir):
                for filename in listdir(thumbnail_dir):
                    file_path = join(thumbnail_dir, filename)
                    try:
                        if isfile(file_path):
                            remove(file_path)
                    except Exception as e:
                        print("[Galery_Thumb] Error while removing file: " + str(e))
            else:
                print("[Galery_Thumb] Thumbnail folder does not exist")
        else:
            print("[Galery_Thumb] No thumbnail directory found")


class Pic_Full_View(Screen):
    """Full screen picture viewer."""

    def __init__(self, session, filelist, index, path):
        """Initialize full view screen.

        Args:
            session: Session object
            filelist: List of picture files
            index: Current index
            path: Path to pictures
        """
        Screen.__init__(self, session)

        self.textcolor = "#ffffff"
        self.color = "#009eb9ff"
        space = 50
        size_w = getDesktop(0).size().width()
        size_h = getDesktop(0).size().height()

        pic_width = size_w - space * 2
        pic_height = size_h - space * 2

        # Build skin
        skinpaint = ('<screen position="0,0" size="' + str(size_w) +
                     ',' + str(size_h) + '" flags="wfNoBorder">\n')
        skinpaint += ('<eLabel position="0,0" size="' + str(size_w) + ',' +
                      str(size_h) + '" zPosition="0" backgroundColor="' +
                      self.color + '" />\n')
        skinpaint += ('<widget name="pic" position="' + str(space) + ',' +
                      str(space) + '" size="' + str(pic_width) + ',' +
                      str(pic_height) + '" zPosition="1" alphatest="on" />\n')
        skinpaint += ('<widget name="point" position="' + str(space + 20) +
                      ',' + str(space + 2) + '" size="30,30" zPosition="2" ' +
                      'pixmap="skin_default/icons/record.png" alphatest="on" />\n')
        skinpaint += ('<widget name="play_icon" position="' + str(space + 50) +
                      ',' + str(space + 2) + '" size="30,30" zPosition="2" ' +
                      'pixmap="skin_default/icons/ico_mp_play.png" alphatest="on" />\n')
        skinpaint += ('<widget name="play_icon_show" position="' + str(space + 50) +
                      ',' + str(space + 2) + '" size="30,30" zPosition="2" ' +
                      'pixmap="skin_default/icons/ico_mp_play.png" alphatest="on" />\n')
        skinpaint += ('<widget source="file" render="Label" position="' +
                      str(space + 80) + ',' + str(space) + '" size="' +
                      str(size_w - space * 2 - 50) + ',25" font="Regular;28" ' +
                      'halign="left" foregroundColor="' + self.textcolor +
                      '" zPosition="2" noWrap="1" transparent="1" />\n')
        skinpaint += '</screen>\n'

        self.skin = skinpaint

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions", "MovieSelectionActions"], {
                "cancel": self.exit,
                "green": self.play_pause,
                "yellow": self.play_pause,
                "blue": self.next_pic,
                "red": self.prev_pic,
                "left": self.prev_pic,
                "right": self.next_pic
            }, -1
        )

        self['point'] = Pixmap()
        self['pic'] = Pixmap()
        self['play_icon'] = Pixmap()
        self['play_icon_show'] = Pixmap()
        self['file'] = StaticText(_('please wait, loading picture...'))

        self.old_index = 0
        self.filelist = []
        self.lastindex = index
        self.curr_pic = []
        self.show_now = True
        self.dirlist_count = 0

        # Process filelist
        for item in filelist:
            if len(filelist[0]) == 3:
                if item[0][1] is False:
                    self.filelist.append(path + item[0][0])
                else:
                    self.dirlist_count += 1
            elif len(filelist[0]) == 2:
                if item[0][1] is False:
                    self.filelist.append(item[0][0])
                else:
                    self.dirlist_count += 1
            else:
                self.filelist.append(item[T_FULL])

        self.max_entry = len(self.filelist) - 1
        self.index = index - self.dirlist_count
        if self.index < 0:
            self.index = 0

        self.picload = ePicLoad()
        try:
            self.picload.PictureData.get().append(self.finish_decode)
        except:
            self.picload.PictureData.connect(self.finish_decode)

        self.slide_timer = eTimer()
        self.slide_timer.callback.append(self.slide_pic)
        self.slide_timer.start(500, True)

        if self.max_entry >= 0:
            self.onLayoutFinish.append(self.set_picload_conf)

    def set_picload_conf(self):
        """Configure picture loader for full view."""
        scale = get_scale()
        if scale is None or len(scale) < 2:
            print("Error: get_scale() returned invalid value")
            return

        scale_x = scale[0] if isinstance(scale[0], (int, float)) else 1
        scale_y = scale[1] if isinstance(scale[1], (int, float)) else 1

        if self['pic'].instance is None:
            return

        self.picload.setPara([
            self['pic'].instance.size().width(),
            self['pic'].instance.size().height(),
            scale_x,
            scale_y,
            False,
            1,
            self.color
        ])

        self['play_icon'].hide()
        self['play_icon_show'].hide()
        self.start_decode()

    def show_picture(self):
        """Display current picture."""
        if self.show_now and len(self.curr_pic):
            self.show_now = False
            self['file'].setText(self.curr_pic[0])
            self.lastindex = self.curr_pic[1]

            if self.curr_pic[2] is not None:
                self['pic'].instance.setPixmap(self.curr_pic[2])
            else:
                print("Error: Image not found.")

            self.curr_pic = []
            self.next_image()
            self.start_decode()

    def finish_decode(self, pic_info=''):
        """Callback when picture decoding finishes.

        Args:
            pic_info: Picture information string
        """
        self['point'].hide()
        ptr = self.picload.getData()
        if ptr is None:
            return

        text = ''
        try:
            text = pic_info.split('\n', 1)
            text = '(' + str(self.index + 1) + '/' + str(self.max_entry + 1) + ') ' + text[0].split('/')[-1]
        except:
            pass

        self.curr_pic = []
        self.curr_pic.append(text)
        self.curr_pic.append(self.index)
        self.curr_pic.append(ptr)
        self.show_picture()

    def start_decode(self):
        """Start decoding current picture."""
        if 0 <= self.index < len(self.filelist) and self.filelist[self.index]:
            self.picload.startDecode(self.filelist[self.index])
            self['point'].show()
            self['play_icon_show'].show()
        else:
            print("Error: Invalid index or file not found.")

    def next_image(self):
        """Move to next image."""
        self.index += 1
        if self.index > self.max_entry:
            self.index = 0

    def prev_image(self):
        """Move to previous image."""
        self.index -= 1
        if self.index < 0:
            self.index = self.max_entry

    def slide_pic(self):
        """Slide to next picture automatically."""
        print("[Galery_Thumb] slide_pic slide to next Picture index: " + str(self.lastindex))
        self.play_pause()
        self.show_now = True
        self.show_picture()

    def play_pause(self):
        """Toggle slideshow play/pause."""
        if self.slide_timer.isActive():
            self.slide_timer.stop()
            self['play_icon'].hide()
            self['play_icon_show'].hide()
        else:
            self.slide_timer.start(10 * 1000)  # 10 seconds
            self['play_icon'].show()
            self['play_icon_show'].hide()
            self.next_pic()

    def prev_pic(self):
        """Show previous picture."""
        self.curr_pic = []
        self.index = self.lastindex
        self.prev_image()
        self.start_decode()
        self.show_now = True

    def next_pic(self):
        """Show next picture."""
        self.show_now = True
        self.show_picture()

    def exit(self):
        """Exit full view."""
        del self.picload
        self.close(self.lastindex + self.dirlist_count)
