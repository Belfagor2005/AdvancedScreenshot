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


def getScale():
    return AVSwitch().getFramebufferScale()


T_INDEX = 0
T_FRAME_POS = 1
T_PAGE = 2
T_NAME = 3
T_FULL = 4

"""
self.color =    (('#ff000000', _('trasparent')),
                ('#00000000', _('black')),
                ('#009eb9ff', _('blue')),
                ('#00ff5a51', _('red')),
                ('#00ffe875', _('yellow')),
                ('#0038FF48', _('green')))
self.textcolor = (('#ff000000', _('trasparent')),('#00000000', _('black')))
"""


class Galery_Thumb(Screen):

    def __init__(self, session, piclist, lastindex, path):
        """ make skin """
        self.textcolor = "#ffffff"
        self.color = "#009eb9ff"
        textsize = 35
        self.spaceX = 50
        self.picX = 400
        self.spaceY = 10
        self.picY = 320

        size_w = getDesktop(0).size().width()
        size_h = getDesktop(0).size().height()

        self.thumbsX = size_w // (self.spaceX + self.picX)
        self.thumbsY = size_h // (self.spaceY + self.picY)
        self.thumbsC = int(round(self.thumbsX * self.thumbsY))
        self.positionlist = []

        skincontent = ""

        for x in range(self.thumbsC):
            posX = x % self.thumbsX
            posY = x // self.thumbsX
            absX = self.spaceX + posX * (self.spaceX + self.picX)
            absY = self.spaceY + posY * (self.spaceY + self.picY)

            self.positionlist.append((absX, absY))

            label_pos = absY + self.picY - textsize
            thumb_pos_x = absX + 5
            thumb_pos_y = absY + 5
            thumb_h = self.picY - textsize * 2

            skincontent += ('<widget source="label' +
                            str(x) +
                            '" render="Label" '
                            'position="' +
                            str(absX) +
                            ',' +
                            str(label_pos) +
                            '" '
                            'size="' +
                            str(self.picX) +
                            ',' +
                            str(textsize) +
                            '" '
                            'halign="center" font="Regular;24" zPosition="2" '
                            'transparent="1" noWrap="1" foregroundColor="' +
                            self.textcolor +
                            '" />\n')

            skincontent += (
                '<widget name="thumb' + str(x) + '" '
                'position="' + str(thumb_pos_x) + ',' + str(thumb_pos_y) + '" '
                'size="' + str(self.picX - 10) + ',' + str(thumb_h) + '" '
                'zPosition="2" transparent="1" alphatest="on" />\n'
            )

        skinthumb = '<screen name="Galery_Thumb" position="center,center" size="' + \
            str(size_w) + ',' + str(size_h) + '" flags="wfNoBorder">\n'
        skinthumb += '<eLabel position="0,0" zPosition="1" size="' + \
            str(size_w) + ',' + str(size_h) + '" backgroundColor="' + self.color + '" halign="center" />\n'
        skinthumb += '<widget name="frame" position="35,30" size="' + str(self.picX + 5) + ',' + str(
            self.picY + 10) + '" scale="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AdvancedScreenshot/images/pic_frame.png" alphatest="on" zPosition="3"/>\n'
        skinthumb += skincontent
        skinthumb += '</screen>\n'

        self.skin = skinthumb

        Screen.__init__(self, session)
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions", "MovieSelectionActions"], {
                "cancel": self.Exit,
                "ok": self.KeyOk,
                "left": self.key_left,
                "right": self.key_right,
                "up": self.key_up,
                "down": self.key_down
            }, -1
        )
        self['frame'] = MovingPixmap()
        for x in range(self.thumbsC):
            self['label' + str(x)] = StaticText()
            self['thumb' + str(x)] = Pixmap()

        self.Thumbnaillist = []
        self.filelist = []
        self.currPage = -1
        self.dirlistcount = 0
        self.path = path
        index = 0
        framePos = 0
        Page = 0
        for x in piclist:
            if x:
                self.filelist.append((index,
                                      framePos,
                                      Page,
                                      x,
                                      path + x))
                index += 1
                framePos += 1
                if framePos > self.thumbsC - 1:
                    framePos = 0
                    Page += 1
            else:
                self.dirlistcount += 1

        self.maxentry = len(self.filelist) - 1
        self.index = int(lastindex) - self.dirlistcount
        if self.index < 0:
            self.index = 0

        self.picload = ePicLoad()
        if self.picload.PictureData is not None:
            self.picload.PictureData.get().append(self.showPic)
        self.ThumbTimer = eTimer()
        self.ThumbTimer.callback.append(self.showPic)
        self.onLayoutFinish.append(self.setPicloadConf)

    def setPicloadConf(self):
        sc = getScale()
        scale_x = sc[0] if isinstance(sc[0], (int, float)) else 1
        scale_y = sc[1] if isinstance(sc[1], (int, float)) else 1
        try:
            self.picload.setPara([self['thumb0'].instance.size().width(),
                                  self['thumb0'].instance.size().height(),
                                  scale_x,
                                  scale_y,
                                  False,
                                  1,
                                  self.color])
        except Exception as e:
            print(f"[Galery_Thumb] setPicloadConf Error: {str(e)}")
            return
        self.paintFrame()

    def paintFrame(self):
        if self.maxentry < self.index or self.index < 0:
            return
        pos = self.positionlist[self.filelist[self.index][T_FRAME_POS]]
        self['frame'].moveTo(pos[0], pos[1], 1)
        self['frame'].startMoving()
        if self.currPage is not self.filelist[self.index][T_PAGE]:
            self.currPage = self.filelist[self.index][T_PAGE]
            self.newPage()

    def newPage(self):
        self.Thumbnaillist = []
        for x in range(self.thumbsC):
            self['label' + str(x)].setText('')
            self['thumb' + str(x)].hide()

        for x in self.filelist:
            if x[T_PAGE] is self.currPage:
                self['label' + str(x[T_FRAME_POS])].setText('(' + \
                                   str(x[T_INDEX] + 1) + ') ' + x[T_NAME])
                self.Thumbnaillist.append([0, x[T_FRAME_POS], x[T_FULL]])
        self.showPic()

    def showPic(self, picInfo=''):
        for x in range(len(self.Thumbnaillist)):
            img_path = self.Thumbnaillist[x][2]
            if not file_exists(img_path):
                print(f"[Galery_Thumb] Error: File not found: {str(img_path)}")
                return
            if self.Thumbnaillist[x][0] == 0:
                result = self.picload.getThumbnail(img_path)
                if result == 1:
                    self.ThumbTimer.start(500, True)
                elif result == -1:
                    print(f"Error loading thumbnail for {img_path}")
                    return
                else:
                    self.Thumbnaillist[x][0] = 1
                break
            elif self.Thumbnaillist[x][0] == 1:
                self.Thumbnaillist[x][0] = 2
                ptr = self.picload.getData()
                if ptr is None:
                    print("Error: self.PicLoad.getData() returned None")
                    print(
                        f"[Galery_Thumb] showPic: returned None: {
                            str(img_path)}")
                    return
                try:
                    self['thumb' + str(self.Thumbnaillist[x][1])
                         ].instance.setPixmap(ptr)
                    self['thumb' + str(self.Thumbnaillist[x][1])].show()
                except Exception as e:
                    print(
                        f"[Galery_Thumb] showPic Error while setPixmap: {
                            str(e)}")
        return

    def key_left(self):
        self.index -= 1
        if self.index < 0:
            self.index = self.maxentry
        self.paintFrame()

    def key_right(self):
        self.index += 1
        if self.index > self.maxentry:
            self.index = 0
        self.paintFrame()

    def key_up(self):
        self.index -= self.thumbsX
        if self.index < 0:
            self.index = self.maxentry
        self.paintFrame()

    def key_down(self):
        self.index += self.thumbsX
        if self.index > self.maxentry:
            self.index = 0
        self.paintFrame()

    def KeyOk(self):
        if self.maxentry < 0:
            return
        self.old_index = self.index
        self.session.openWithCallback(
            self.callbackView,
            Pic_Full_View,
            self.filelist,
            self.index,
            self.path)

    def callbackView(self, val=0):
        self.index = val
        if self.old_index is not self.index:
            self.paintFrame()

    def Exit(self):
        del self.picload
        self.remove_thumbails()
        self.close(self.index + self.dirlistcount)

    def remove_thumbails(self):
        import glob
        thumbnail_dir = glob.glob(self.path)
        thumbnail_dir = str(thumbnail_dir[0]) + '.Thumbnails'
        if file_exists(thumbnail_dir) and isdir(thumbnail_dir):
            for filename in listdir(thumbnail_dir):
                file_path = join(thumbnail_dir, filename)
                try:
                    if isfile(file_path):
                        remove(file_path)
                except Exception as e:
                    print(
                        f"[Galery_Thumb] Error while removing file: {
                            str(e)}")
        else:
            print('The folder does not exist')


class Pic_Full_View(Screen):

    def __init__(self, session, filelist, index, path):
        Screen.__init__(self, session)

        """ make skin """
        self.textcolor = "#ffffff"
        self.color = "#009eb9ff"
        space = 50
        size_w = getDesktop(0).size().width()
        size_h = getDesktop(0).size().height()

        pic_width = size_w - space * 2
        pic_height = size_h - space * 2

        skinpaint = '<screen position="0,0" size="' + \
            str(size_w) + ',' + str(size_h) + '" flags="wfNoBorder">\n'
        skinpaint += '<eLabel position="0,0" size="' + str(size_w) + ',' + str(
            size_h) + '" zPosition="0" backgroundColor="' + self.color + '" />\n'
        skinpaint += '<widget name="pic" position="' + str(space) + ',' + str(space) + '" size="' + str(
            pic_width) + ',' + str(pic_height) + '" zPosition="1" alphatest="on" />\n'
        skinpaint += '<widget name="point" position="' + str(space + 20) + ',' + str(
            space + 2) + '" size="30,30" zPosition="2" pixmap="skin_default/icons/record.png" alphatest="on" />\n'
        skinpaint += '<widget name="play_icon" position="' + str(space + 50) + ',' + str(
            space + 2) + '" size="30,30" zPosition="2" pixmap="skin_default/icons/ico_mp_play.png" alphatest="on" />\n'
        skinpaint += '<widget name="play_icon_show" position="' + str(space + 50) + ',' + str(
            space + 2) + '" size="30,30" zPosition="2" pixmap="skin_default/icons/ico_mp_play.png" alphatest="on" />\n'
        skinpaint += '<widget source="file" render="Label" position="' + str(space + 80) + ',' + str(space) + '" size="' + str(
            size_w - space * 2 - 50) + ',25" font="Regular;28" halign="left" foregroundColor="' + self.textcolor + '" zPosition="2" noWrap="1" transparent="1" />\n'
        skinpaint += '</screen>\n'
        self.skin = skinpaint

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions", "MovieSelectionActions"], {
                "cancel": self.Exit,
                "green": self.PlayPause,
                "yellow": self.PlayPause,
                "blue": self.nextPic,
                "red": self.prevPic,
                "left": self.prevPic,
                "right": self.nextPic
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
        self.currPic = []
        self.shownow = True
        self.dirlistcount = 0
        for x in filelist:
            if len(filelist[0]) == 3:
                if x[0][1] is False:
                    self.filelist.append(path + x[0][0])
                else:
                    self.dirlistcount += 1
            elif len(filelist[0]) == 2:
                if x[0][1] is False:
                    self.filelist.append(x[0][0])
                else:
                    self.dirlistcount += 1
            else:
                self.filelist.append(x[T_FULL])

        self.maxentry = len(self.filelist) - 1
        self.index = index - self.dirlistcount
        if self.index < 0:
            self.index = 0
        self.picload = ePicLoad()
        self.picload.PictureData.get().append(self.finish_decode)
        self.slideTimer = eTimer()
        self.slideTimer.callback.append(self.slidePic)
        self.slideTimer.start(500, True)

        if self.maxentry >= 0:
            self.onLayoutFinish.append(self.setPicloadConf)

    def setPicloadConf(self):
        sc = getScale()
        if sc is None or len(sc) < 2:
            print("Error: getScale() no valid value")
            return
        scale_x = sc[0] if isinstance(sc[0], (int, float)) else 1
        scale_y = sc[1] if isinstance(sc[1], (int, float)) else 1
        if self['pic'].instance is None:
            return
        self.picload.setPara([self['pic'].instance.size().width(),
                              self['pic'].instance.size().height(),
                              scale_x,
                              scale_y,
                              False,
                              1,
                              self.color])
        self['play_icon'].hide()
        self['play_icon_show'].hide()
        self.start_decode()

    def ShowPicture(self):
        if self.shownow and len(self.currPic):
            self.shownow = False
            self['file'].setText(self.currPic[0])
            self.lastindex = self.currPic[1]
            if self.currPic[2] is not None:
                self['pic'].instance.setPixmap(self.currPic[2])
            else:
                print("Error: Immage not found.")
            self.currPic = []
            self.next()
            self.start_decode()

    def finish_decode(self, picInfo=''):
        self['point'].hide()
        ptr = self.picload.getData()
        if ptr is None:
            return
        text = ''
        try:
            text = picInfo.split('\n', 1)
            text = '(' + str(self.index + 1) + '/' + \
                str(self.maxentry + 1) + ') ' + text[0].split('/')[-1]
        except BaseException:
            pass

        self.currPic = []
        self.currPic.append(text)
        self.currPic.append(self.index)
        self.currPic.append(ptr)
        self.ShowPicture()
        return

    def start_decode(self):
        if 0 <= self.index < len(self.filelist) and self.filelist[self.index]:
            self.picload.startDecode(self.filelist[self.index])
            self['point'].show()
            self['play_icon_show'].show()
        else:
            print("Error: Invalid index or file not found.")

    def next(self):
        self.index += 1
        if self.index > self.maxentry:
            self.index = 0

    def prev(self):
        self.index -= 1
        if self.index < 0:
            self.index = self.maxentry

    def slidePic(self):
        print(
            f"[Galery_Thumb]slidePic slide to next Picture index: {str(self.lastindex)}")
        self.PlayPause()
        self.shownow = True
        self.ShowPicture()

    def PlayPause(self):
        if self.slideTimer.isActive():
            self.slideTimer.stop()
            self['play_icon'].hide()
            self['play_icon_show'].hide()
        else:
            self.slideTimer.start(10 * 1000)
            self['play_icon'].show()
            self['play_icon_show'].hide()
            self.nextPic()

    def prevPic(self):
        self.currPic = []
        self.index = self.lastindex
        self.prev()
        self.start_decode()
        self.shownow = True

    def nextPic(self):
        self.shownow = True
        self.ShowPicture()

    def Exit(self):
        del self.picload
        self.close(self.lastindex + self.dirlistcount)
