#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
"""
#########################################################
#                                                       #
#  Advanced Screenshot                                  #
#  Version: 1.0                                         #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#                                                       #
#  Last Modified: "11:37 - 20250515"                    #
#                                                       #
#  Credits:                                             #
#  - Original concept by Lululla                        #
#                                                       #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################
"""
__author__ = "Lululla"

# Standard Library Imports
import subprocess
import time
from datetime import datetime
from os import (
    access, chmod, listdir, makedirs, remove, stat, W_OK, X_OK
)
from os.path import exists, getctime, isdir, isfile, join  # , getsize
from re import match

# Third-party Imports
try:
    from Components.AVSwitch import AVSwitch
except ImportError:
    from Components.AVSwitch import eAVControl as AVSwitch
from enigma import eActionMap, ePicLoad, getDesktop
from twisted.web import resource, server

# Application-specific Imports
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import (
    ConfigEnableDisable, ConfigInteger, ConfigSelection, ConfigSubsection,
    ConfigYesNo, config, getConfigListEntry
)
from Components.Label import Label
from Components.Harddisk import harddiskmanager
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import resolveFilename, SCOPE_MEDIA

# Local specific Imports
from . import _
from .MyConsole import MyConsole

# Constants
SIZE_W = getDesktop(0).size().width()
SIZE_H = getDesktop(0).size().height()


def getScale():
    return AVSwitch().getFramebufferScale()


BUTTON_MAP = {
    "059": "KEY_F1",
    "060": "KEY_F2",
    "061": "KEY_F3",
    "062": "KEY_F4",
    "063": "KEY_F5",
    "064": "KEY_F6",
    "065": "KEY_F7",
    "066": "KEY_F8",
    "067": "KEY_F9",
    "068": "KEY_F10",
    "102": "KEY_HOME",
    "113": "Mute",
    "167": "KEY_RECORD",
    # "352": "Help",
    "138": "Help",
    "358": "Info",
    "362": "Timer",
    "365": "EPG",
    "370": "Subtitle",
    "377": "TV",
    "385": "Radio",
    "388": "Text",
    "392": "Audio",
    "398": "Red",
    "399": "Green",
    "400": "Yellow",
    "401": "Blue"
}


MODE_MAP = {
    "osd": "-o",
    "video": "-v",
    "All": ""
}


# auto mount device
def getMountedDevs():

    def handleMountpoint(loc):
        original_mp, original_desc = loc
        normalized_mp = original_mp.rstrip('/') + '/'
        if original_desc:
            new_desc = f"{original_desc} ({normalized_mp})"
        else:
            new_desc = f"({normalized_mp})"
        return (normalized_mp, new_desc)

    mountedDevs = [
        (resolveFilename(SCOPE_MEDIA, 'hdd'), _('Hard Disk')),
        (resolveFilename(SCOPE_MEDIA, 'usb'), _('USB Drive'))
    ]
    mountedDevs += [
        (p.mountpoint, _(p.description) if p.description else '')
        for p in harddiskmanager.getMountedPartitions(True)
    ]
    mountedDevs = [path for path in mountedDevs if isdir(path[0]) and access(path[0], W_OK | X_OK)]

    netDir = resolveFilename(SCOPE_MEDIA, 'net')
    if isdir(netDir):
        mountedDevs += [(join(netDir, p), _('Network mount')) for p in listdir(netDir)]

    mountedDevs += [(join('/', 'tmp'), _('Temporary'))]

    mountedDevs = list(map(handleMountpoint, mountedDevs))

    return mountedDevs


# Configuration
config.plugins.AdvancedScreenshot = ConfigSubsection()
config.plugins.AdvancedScreenshot.enabled = ConfigEnableDisable(default=True)
config.plugins.AdvancedScreenshot.freezeframe = ConfigEnableDisable(default=False)
config.plugins.AdvancedScreenshot.allways_save = ConfigEnableDisable(default=False)
config.plugins.AdvancedScreenshot.fixed_aspect_ratio = ConfigEnableDisable(default=False)
config.plugins.AdvancedScreenshot.always_43 = ConfigEnableDisable(default=False)
config.plugins.AdvancedScreenshot.bi_cubic = ConfigEnableDisable(default=False)
config.plugins.AdvancedScreenshot.picturesize = ConfigSelection(
    default="1920x1080",
    choices=[
        ("1920x1080", "1080p (Full HD)"),
        ("1280x720", "720p (HD)"),
        ("720x576", "576p (SD)"),
        ("default", _("Default Resolution"))
    ]
)


config.plugins.AdvancedScreenshot.pictureformat = ConfigSelection(
    default="-j 90",
    choices=[
        ('-j 100', _('JPEG 100%')),
        ('-j 90', _('JPEG 90%')),
        ('-j 80', _('JPEG 80%')),
        ('-j 60', _('JPEG 60%')),
        ('-p', _('PNG')),
        ('bmp', _('BMP'))
    ]
)

config.plugins.AdvancedScreenshot.path = ConfigSelection(
    default="/tmp/", choices=getMountedDevs())
"""
    # choices=[
        # ("/media/hdd/", _("Hard Disk")),
        # ("/media/usb/", _("USB Drive")),
        # ("/tmp/", _("Temporary"))
    # ]
# )
"""
config.plugins.AdvancedScreenshot.picturetype = ConfigSelection(
    default="video",
    choices=[
        ("osd", _("OSD Only")),
        ("video", _("Video Only")),
        ("All", _("OSD + Video"))
    ]
)


config.plugins.AdvancedScreenshot.timeout = ConfigSelection(
    default="3",
    choices=[
        ("1", "1 sec"),
        ("3", "3 sec"),
        ("5", "5 sec"),
        ("10", "10 sec"),
        ("off", _("no message")),
        ("0", _("no timeout"))
    ]
)
config.plugins.AdvancedScreenshot.buttonchoice = ConfigSelection(
    default="138",
    choices=BUTTON_MAP
)
config.plugins.AdvancedScreenshot.switchhelp = ConfigYesNo(default=False)
"""
config.plugins.AdvancedScreenshot.quality = ConfigSelection(
    default="90",
    choices=[str(x) for x in range(50, 101, 10)]
)
"""
config.plugins.AdvancedScreenshot.capture_delay = ConfigInteger(default=0, limits=(0, 10))
# Dummy per padding/compatibility
config.plugins.AdvancedScreenshot.dummy = ConfigSelection(
    default="1",
    choices=[("1", " ")]
)


def cleanup_tmp_files(tmp_folder="/tmp", max_age_seconds=3600):
    """Cleanup Utility"""
    now = time.time()
    for filename in listdir(tmp_folder):
        if filename.startswith("web_grab_") and (filename.endswith(".png") or filename.endswith(".jpg")):
            filepath = tmp_folder + "/" + filename
            try:
                statc = stat(filepath)
                if now - statc.st_mtime > max_age_seconds:
                    remove(filepath)
            except Exception:
                pass


def checkfolder(folder):
    if exists(folder):
        return True
    return False


def _get_extension(fmt):
    """Mappa formato -> estensione"""
    if fmt.startswith('-j'):
        return '.jpg'
    elif fmt == '-p':
        return '.png'
    elif fmt == 'bmp':
        return '.bmp'
    return '.jpg'  # fallback


def _generate_filename():
    base_path = config.plugins.AdvancedScreenshot.path.value.rstrip('/')
    full_path = f"{base_path}/screenshots"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pic_format = config.plugins.AdvancedScreenshot.pictureformat.value
    if pic_format.startswith("-j"):
        ext = ".jpg"
    elif pic_format == "-p":
        ext = ".png"
    else:
        ext = ".bmp"
    try:
        makedirs(full_path, exist_ok=True)
        for path in [base_path, full_path]:
            if not exists(path):
                raise Exception(f"Folder {path} does not exist")
            if not access(path, W_OK):
                raise Exception(f"Write permission denied for {path}")
        chmod(full_path, 0o777)
    except Exception as e:
        print(f"[ERROR] Creating directory: {e}")
        return None

    return f"{full_path}/screenshot_{timestamp}{ext}"


def _build_grab_command(filename):
    cmd = ["/usr/bin/grab"]
    if not exists('/var/lib/dpkg/status'):
        cmd += ["-d"]  # Critical parameters missing

    picturetype_map = {
        "osd": "-o",
        "video": "-v",
        "All": ""
    }
    pic_type = config.plugins.AdvancedScreenshot.picturetype.value
    if pic_type in picturetype_map and picturetype_map[pic_type]:
        cmd.append(picturetype_map[pic_type])

    fixed_aspect_ratio = config.plugins.AdvancedScreenshot.fixed_aspect_ratio.value
    if fixed_aspect_ratio:
        cmd.append("-n")

    always_43 = config.plugins.AdvancedScreenshot.always_43.value
    if always_43:
        cmd.append("-l")

    bi_cubic = config.plugins.AdvancedScreenshot.bi_cubic.value
    if bi_cubic:
        cmd.append("-b")

    pic_format = config.plugins.AdvancedScreenshot.pictureformat.value
    if pic_format.startswith('-j'):
        cmd += pic_format.split()  # Example: "-j 90" → ["-j", "90"]
    elif pic_format == '-p':
        cmd.append("-p")

    cmd.append(filename)

    return cmd


class WebGrabResource(resource.Resource):
    """Web interface handler for remote screenshot capture"""

    def __init__(self, session):
        resource.Resource.__init__(self)
        self.session = session

    def render_GET(self, request):
        """Handle GET requests for screenshot capture"""
        try:
            cleanup_tmp_files()

            # 1: Parameter update and validation
            params = {
                'format': request.args.get(b'format', [b'-j 90'])[0].decode(),
                'r': request.args.get(b'r', [b'720'])[0].decode(),
                'v': request.args.get(b'v', [b'0'])[0].decode(),
                's': request.args.get(b's', [b'1'])[0].decode()
            }

            # 2: New format validation
            valid_formats = ('-j 100', '-j 90', '-j 80', '-j 60', 'bmp', '-p')
            if params['format'] not in valid_formats:
                raise ValueError("[AdvancedScreenshotConfig]Format not supported")

            if params['r'] != 'default' and not match(r"^\d+(x\d+)?$", params['r']):
                raise ValueError("[AdvancedScreenshotConfig]Invalid resolution")

            # 3: Filename generation updated
            filename = _generate_filename(params['format'])

            cmd = _build_grab_command(params, filename)

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            if not exists(filename):
                if result.returncode == 0:
                    # 4: Content-Type dinamico
                    ext = _get_extension(params['format'])
                    with open(filename, 'rb') as f:
                        request.setHeader(b'Content-Type', f'image/{ext}'.encode())
                        request.write(f.read())
                    if int(params['s']) == 1 and exists(filename):
                        remove(filename)
                else:
                    request.setResponseCode(500)
                    request.write(f"Error: {result.stderr.decode()}".encode())

        except Exception as e:
            request.setResponseCode(500)
            request.write(f"[AdvancedScreenshotConfig]Error: {str(e)}".encode())

        return server.NOT_DONE_YET


class ScreenshotCore:
    def __init__(self, session):
        self.session = session
        self.previous_flag = 0
        self.myConsole = MyConsole()
        self._bind_hotkey()

    def _bind_hotkey(self):
        eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self._key_handler)

    def _key_handler(self, key, flag):
        try:
            current_value = str(key)
            target_value = config.plugins.AdvancedScreenshot.buttonchoice.value

            # If the button is NOT the one configured for screenshot, let it pass!
            if current_value != target_value:
                return 0

            # If it is the screenshot button and it is enabled:
            if config.plugins.AdvancedScreenshot.enabled.value:
                if config.plugins.AdvancedScreenshot.switchhelp.value:
                    if flag == 1:
                        self.capture()
                        return 1
                else:
                    if flag == 3:
                        self.capture()
                        return 1

            return 0
        except Exception as e:
            print("[AdvancedScreenshotConfig]Key handler error: " + str(e))
            return 0

    """
    # def _key_handler(self, key, flag):
        # try:
            # current_value = str(key)
            # target_value = config.plugins.AdvancedScreenshot.buttonchoice.value

            # print("[AdvancedScreenshotConfig]Key event: " + str(current_value) + " vs " + str(target_value) + ", Flag: " + str(flag))

            # if (current_value == target_value and
                    # config.plugins.AdvancedScreenshot.enabled.value):

                # if config.plugins.AdvancedScreenshot.switchhelp.value:
                    # # Short press mode
                    # if flag == 1:
                        # print("[AdvancedScreenshotConfig]Short press detected")
                        # self.capture()
                        # return 1
                # else:
                    # # Long press mode
                    # if flag == 3:
                        # print("[AdvancedScreenshotConfig]Long press detected")
                        # self.capture()
                        # return 1

                # if flag == 0:  # KEY_UP
                    # print("[AdvancedScreenshotConfig]Key released")

            # return 0
        # except Exception as e:
            # print(f"[AdvancedScreenshotConfig][AdvancedScreenshotConfig]Key handler error: {str(e)}")
            # return 0
    """

    def capture(self):
        if not self._is_grab_available():
            raise Exception("Web capture failed Grab not available")
        try:
            filename = _generate_filename()
            if not filename:
                return
            cmd = _build_grab_command(filename)
            self.last_capture_filename = filename
            print("[Capture] Running command:", " ".join(cmd))
            self.myConsole.ePopen(cmd, self._capture_callback, [filename])
        except Exception as e:
            print(f"[AdvancedScreenshotConfig][ERROR] Capture error: {str(e)}")
            self._show_error(_("Error during capture:\n") + str(e))

    def _capture_callback(self, data, retval, extra_args):
        print(f"[AdvancedScreenshotConfig][_capture_callback]extra_args: {str(extra_args)}")
        filename = extra_args  # [0]
        error_msg = ""

        if retval != 0:
            error_msg = "Grab command failed with code: " + str(retval)

        if not error_msg and filename:
            for x in range(5):  # Retry per attesa file
                if exists(filename):
                    break
                time.sleep(0.5)
            else:
                error_msg = "File not created\nCheck disk space"

        if error_msg:
            print(f"[AdvancedScreenshotConfig][ERROR]: {str(error_msg)}")
            self._show_error(_(error_msg))
            return

        print(f"[AdvancedScreenshotConfig][INFO] Screenshot saved: {str(filename)}")
        if config.plugins.AdvancedScreenshot.freezeframe.value:
            self.session.openWithCallback(self._freeze_callback, FreezeFrame, filename)
        else:
            self._show_message(_("Screenshot saved successfully!"))

    def _freeze_callback(self, retval):
        if retval:
            self._show_message(_("Screenshot saved successfully!"))

    def _is_grab_available(self):
        return exists("/usr/bin/grab")

    def _show_message(self, message):
        """Show success notification"""
        self.session.open(
            MessageBox,
            message,
            MessageBox.TYPE_INFO,
            timeout=int(config.plugins.AdvancedScreenshot.timeout.value)
        )

    def _show_error(self, message):
        """Show error notification"""
        self.session.open(
            MessageBox,
            message,
            MessageBox.TYPE_ERROR,
            timeout=5
        )


class FreezeFrame(Screen):
    skin = f"""
    <screen name="FreezeFrame" position="0,0" size="{SIZE_W},{SIZE_H}" flags="wfNoBorder">
        <widget name="preview" position="0,0" size="{SIZE_W},{SIZE_H}" zPosition="4" />
        <widget name="info" position="center,50" size="600,40" font="Regular;28" zPosition="5" halign="center"/>
    </screen>"""

    def __init__(self, session, filename):
        Screen.__init__(self, session)
        self.filename = filename
        self.picload = ePicLoad()
        # print(f"[FreezeFrame] ePicLoad.__dict__: {str(ePicLoad.__dict__)}")
        self.Scale = getScale()
        self["preview"] = Pixmap()
        self["info"] = Label(_("Press OK to save - EXIT to cancel"))
        self["actions"] = ActionMap(["OkCancelActions"], {
            "ok": self.save,
            "cancel": self.discard
        })
        self.picload.PictureData.get().append(self.DecodePicture)
        print(f"[FreezeFrame] File {self.filename}")
        self.onLayoutFinish.append(self.ShowPicture)

    def ShowPicture(self):
        if exists(self.filename):
            print(f"[FreezeFrame] ShowPicture: {str(self.filename)}")
        scalex = self.Scale[0] if isinstance(self.Scale[0], (int, float)) else 1
        scaley = self.Scale[1] if isinstance(self.Scale[1], (int, float)) else 1
        self.picload.setPara([
            self["preview"].instance.size().width(),
            self["preview"].instance.size().height(),
            scalex,
            scaley,
            0,
            1,
            "#ff000000"
        ])
        if self.picload.startDecode(self.filename):
            self.picload = ePicLoad()
            try:
                self.picload.PictureData.get().append(self.DecodePicture)
            except:
                self.picload_conn = self.picload.PictureData.connect(self.DecodePicture)
        return

    def DecodePicture(self, PicInfo=None):
        print(f"[FreezeFrame] DecodePicture: {str(PicInfo)}")
        ptr = self.picload.getData()
        if ptr is not None:
            self["preview"].instance.setPixmap(ptr)
            self["preview"].instance.show()

    def save(self):
        self.close(True)

    def discard(self):
        """
        # try:
            # if not config.plugins.AdvancedScreenshot.allways_save.value:
                # remove(self.filename)
        # except Exception as e:
            # print(f"[AdvancedScreenshotConfig] Error deleting file: {str(e)}")
        """
        self.close(False)


class ScreenshotGallery(Screen):
    skin = """
        <screen position="center,center" size="1280,720" title="Screenshot Gallery" flags="wfNoBorder">
            <!-- <widget name="list" position="40,40" scrollbarMode="showNever" size="620,560" itemHeight="35" font="Regular;32" /> -->
            <widget name="list" position="40,40" size="620,560" itemHeight="35" font="Regular;32" />
            <eLabel position="345,670" size="300,40" font="Regular;36" backgroundColor="#b3ffd9" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#0000ff00" text="OK" halign="center" />
            <eLabel position="643,670" size="300,40" font="Regular;36" backgroundColor="#00ffa000" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#00ffa000" text="Delete" halign="center" />
            <widget name="preview" position="682,126" size="550,350" zPosition="9" alphatest="blend" scale="1" />
            <widget name="info" position="44,606" zPosition="4" size="1189,55" font="Regular;28" foregroundColor="yellow" transparent="1" halign="center" valign="center" />
            <eLabel backgroundColor="#00ff0000" position="45,710" size="300,6" zPosition="12" />
            <eLabel backgroundColor="#0000ff00" position="345,710" size="300,6" zPosition="12" />
            <eLabel backgroundColor="#00ffff00" position="643,710" size="300,6" zPosition="12" />
            <eLabel backgroundColor="#000000ff" position="944,710" size="300,6" zPosition="12" />
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)

        self.screenshots = []
        self['list'] = MenuList(self.screenshots)
        self['preview'] = Pixmap()

        base_path = config.plugins.AdvancedScreenshot.path.value.rstrip('/')
        self.full_path = f"{base_path}/screenshots"
        path = self.full_path
        if not path.endswith("/"):
            self.full_path += "/"

        self.Scale = getScale()
        self.picload = ePicLoad()
        try:
            self.picload.PictureData.get().append(self.DecodePicture)
        except:
            self.picload_conn = self.picload.PictureData.connect(self.DecodePicture)
        self['info'] = Label()
        self["list"].onSelectionChanged.append(self.ShowPicture)
        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"], {
            "red": self.close,
            "green": self.preview,
            "yellow": self.delete,
            "up": self.keyUp,
            "down": self.keyDown,
            "left": self.keyLeft,
            "right": self.keyRight,
            "ok": self.preview,
            "cancel": self.close,
        })
        self._load_screenshots()
        self.onLayoutFinish.append(self.ShowPicture)

    def _load_screenshots(self):
        print(f"[AdvancedScreenshotConfig] ScreenshotGallery path: {str(self.full_path)}")
        try:
            self.screenshots = sorted([
                f for f in listdir(self.full_path)
                if f.lower().endswith(tuple(["jpg", "png", "bmp"]))
            ], key=lambda x: getctime(join(self.full_path, x)), reverse=True)
            print(f"[AdvancedScreenshotConfig] ScreenshotGallery screenshots: {str(self.screenshots)}")
            self["list"].setList(self.screenshots)
        except Exception as e:
            self.session.open(MessageBox, _("Error loading gallery: ") + str(e), MessageBox.TYPE_ERROR)

    def ShowPicture(self):
        fname = self['list'].getCurrent()
        self.filename = self.full_path + str(fname)
        print('filename ok=', self.filename)
        if self.filename is not None:
            print(f"[ScreenshotGallery] ShowPicture: {str(self.filename)}")
            scalex = self.Scale[0] if isinstance(self.Scale[0], (int, float)) else 1
            scaley = self.Scale[1] if isinstance(self.Scale[1], (int, float)) else 1
            self.picload.setPara([
                self["preview"].instance.size().width(),
                self["preview"].instance.size().height(),
                scalex,
                scaley,
                0,
                1,
                "#ff000000"
            ])

            if self.picload.startDecode(self.filename):
                self.picload = ePicLoad()
                self.picload.PictureData.get().append(self.DecodePicture)
            return

    def DecodePicture(self, PicInfo=""):
        if len(self.screenshots) > 0:
            print(f"[ScreenshotGallery] DecodePicture: {str(PicInfo)}")
            if self.filename is not None:
                ptr = self.picload.getData()
            else:
                fname = self['list'].getCurrent()
                self.filename = self.full_path + str(fname)
                ptr = self.picload.getData()
            print(f"[ScreenshotGallery] DecodePicture self.filename: {str(self.filename)}")
            self["info"].setText(_(self.filename))
            self["preview"].instance.setPixmap(ptr)
            self["preview"].instance.show()

    def keyUp(self):
        print("[DEBUG] up pressed")
        try:
            self['list'].up()
            self.ShowPicture()
        except Exception as e:
            print(e)

    def keyDown(self):
        print("[DEBUG] down pressed")
        try:
            self['list'].down()
            self.ShowPicture()
        except Exception as e:
            print(e)

    def keyLeft(self):
        try:
            self['list'].pageUp()
            self.ShowPicture()
        except Exception as e:
            print(e)

    def keyRight(self):
        try:
            self['list'].pageDown()
            self.ShowPicture()
        except Exception as e:
            print(e)

    def preview(self):
        if selection := self["list"].getCurrent():
            path = join(self.full_path, selection)
            self.session.open(ScreenshotPreview, path)

    def delete(self, confirm=False):
        if not confirm:
            self.session.openWithCallback(
                self.delete, MessageBox,
                _("Are you sure you want to delete this screenshot?"),
                MessageBox.TYPE_YESNO
            )
        else:
            if selection := self["list"].getCurrent():
                try:
                    remove(join(self.full_path, selection))
                    self._load_screenshots()
                except Exception as e:
                    self.session.open(MessageBox, _("Delete failed: ") + str(e), MessageBox.TYPE_ERROR)


class ScreenshotPreview(Screen):
    skin = f"""
    <screen position="0,0" size="{SIZE_W},{SIZE_H}" title="Screenshot Preview" flags="wfNoBorder">
        <widget name="image" position="0,0" size="{SIZE_W},{SIZE_H}" />
    </screen>"""

    def __init__(self, session, filepath):
        Screen.__init__(self, session)
        self.filepath = filepath
        self["image"] = Pixmap()
        self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.close})
        self._show_image()

    def _show_image(self):
        self.picload = ePicLoad()
        self.picload.PictureData.get().append(self._update_image)
        self.picload.setPara((
            SIZE_W, SIZE_H,
            SIZE_W, SIZE_H,
            False, 1, "#00000000"
        ))
        self.picload.startDecode(self.filepath)

    def _update_image(self, picInfo=None):
        if ptr := self.picload.getData():
            self["image"].instance.setPixmap(ptr)


class AdvancedScreenshotConfig(ConfigListScreen, Screen):
    skin = """
    <screen name="AdvancedScreenshotConfig" position="center,center" size="1280,720" title="Screenshot Settings" flags="wfNoBorder">
        <widget name="config" position="50,50" size="1180,600" scrollbarMode="showNever" itemHeight="35" font="Regular;32" />
        <eLabel position="45,670" size="300,40" font="Regular;36" backgroundColor="#b3ffd9" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#0000ff00" text="OK" halign="center" />
        <eLabel position="345,670" size="300,40" font="Regular;36" backgroundColor="#b3ffd9" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#00ffa000" text="Cancel" halign="center" />
        <eLabel position="643,670" size="300,40" font="Regular;36" backgroundColor="#00ffa000" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#00ffa000" text="Galery" halign="center" />
        <eLabel position="944,670" size="300,40" font="Regular;36" backgroundColor="#3e91f6" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#00ffa000" text="List" halign="center" />
        <eLabel backgroundColor="#00ff0000" position="45,710" size="300,6" zPosition="12" />
        <eLabel backgroundColor="#0000ff00" position="345,710" size="300,6" zPosition="12" />
        <eLabel backgroundColor="#00ffff00" position="643,710" size="300,6" zPosition="12" />
        <eLabel backgroundColor="#000000ff" position="944,710" size="300,6" zPosition="12" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.setup_title = _("Settings")
        self.list = []
        self.onChangedEntry = []
        self["config"] = ConfigList(self.list)
        self._create_config()
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.onChangedEntry)
        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions", "VirtualKeyboardActions"],
            {
                "ok": self.save,
                "cancel": self.cancel,
                "blue": self.onGallery,
                "yellow": self.onPicView,
                "green": self.save,
                "red": self.cancel,
                "showVirtualKeyboard": self.KeyText,
            }
        )
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        self.setTitle(self.setup_title)

    def _create_config(self):
        self.list = []

        # Basic configuration
        section = '--------------------------------------( Advanced Screenshot Setup )--------------------------------------'
        self.list.append(getConfigListEntry(_(section)))
        self.list.append(getConfigListEntry(_("Enable plugin"), config.plugins.AdvancedScreenshot.enabled))

        if config.plugins.AdvancedScreenshot.enabled.value:

            # 1: Update image format options
            self.list.append(getConfigListEntry(
                _("Image format"),
                config.plugins.AdvancedScreenshot.pictureformat
            ))

            # 2: New logic for resolution
            self.list.append(getConfigListEntry(
                _("Resolution"),
                config.plugins.AdvancedScreenshot.picturesize
            ))

            # 3: Aspect ratio fix
            self.list.append(getConfigListEntry(
                _("Fix aspect ratio (adds -n to force no stretching)"),
                config.plugins.AdvancedScreenshot.fixed_aspect_ratio
            ))

            # 4: Force 4:3 output
            self.list.append(getConfigListEntry(
                _("Always output 4:3 image (adds letterbox if source is 16:9)"),
                config.plugins.AdvancedScreenshot.always_43
            ))

            # 5: Bicubic resize
            self.list.append(getConfigListEntry(
                _("Use bicubic resize (slower, but smoother image)"),
                config.plugins.AdvancedScreenshot.bi_cubic
            ))

            # 6: Freeze frame preview
            self.list.append(getConfigListEntry(
                _("Freeze frame preview"),
                config.plugins.AdvancedScreenshot.freezeframe
            ))

            if config.plugins.AdvancedScreenshot.freezeframe.value:
                self.list.append(getConfigListEntry(
                    _("Always save screenshots"),
                    config.plugins.AdvancedScreenshot.allways_save
                ))

            # 7: Save path
            self.list.append(getConfigListEntry(
                _("Save path (requires restart)"),
                config.plugins.AdvancedScreenshot.path
            ))

            # 8: Keymapping
            current_value = config.plugins.AdvancedScreenshot.buttonchoice.value
            button_name = BUTTON_MAP.get(current_value, _("Unknown"))

            if current_value in ("398", "399", "400"):
                self.list.append(getConfigListEntry(
                    _("Button behavior warning"),
                    config.plugins.AdvancedScreenshot.dummy,
                    _("Long press required for {}").format(button_name)
                ))
            else:
                self.list.append(getConfigListEntry(
                    _("Press type for {}").format(button_name),
                    config.plugins.AdvancedScreenshot.switchhelp
                ))

            # 9: Timeout
            self.list.append(getConfigListEntry(
                _("Message timeout (seconds)"),
                config.plugins.AdvancedScreenshot.timeout
            ))

        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def onChangedEntry(self, configElement=None):
        for x in self.onChangedEntry:
            x()
        self._create_config()

    def save(self):
        for x in self["config"].list:
            x[1].save()
        self.close(True)

    def cancel(self):
        self.close(False)

    def KeyText(self):
        sel = self["config"].getCurrent()
        if sel:
            text_value = str(sel[1].value)
            self.session.openWithCallback(
                self.VirtualKeyBoardCallback,
                VirtualKeyBoard,
                title=sel[0],
                text=text_value
            )

    def VirtualKeyBoardCallback(self, callback=None):
        if callback is not None:
            current = self["config"].getCurrent()
            cfg = current[1]
            try:
                if hasattr(cfg, "base"):
                    cfg.value = int(callback)
                else:
                    cfg.value = callback
            except Exception:
                pass
            self["config"].invalidate(current)

    def getCurrentEntry(self):
        return self["config"].getCurrent()[0]

    def showhide(self):
        pass

    def getCurrentValue(self):
        return str(self["config"].getCurrent()[1].getText())

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self._create_config()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self._create_config()

    def keyDown(self):
        self['config'].instance.moveSelection(self['config'].instance.moveDown)
        self._create_config()

    def keyUp(self):
        self['config'].instance.moveSelection(self['config'].instance.moveUp)
        self._create_config()

    def onPicView(self):
        fullpath = []
        base_path = config.plugins.AdvancedScreenshot.path.value.rstrip('/')
        full_path = f"{base_path}/screenshots/"
        print(f"[AdvancedScreenshotConfig]onPicView full_path: {str(full_path)}")
        if checkfolder(full_path):
            for x in listdir(full_path):
                if isfile(full_path + x):
                    print(f"[AdvancedScreenshotConfig]onPicView file x: {str(x)}")
                    if x.endswith('.jpg') or x.endswith('.png') or x.endswith('.bmp') or x.endswith('.gif'):
                        fullpath.append(x)
            self.fullpath = fullpath
            try:
                from .picplayer import Galery_Thumb
                self.session.open(Galery_Thumb, self.fullpath, 0, full_path)
            except TypeError as e:
                print(f"[AdvancedScreenshotConfig]onPicView error: {str(e)}")

    def onGallery(self):
        try:
            self.session.open(ScreenshotGallery)
        except TypeError as e:
            print(f"[AdvancedScreenshotConfig]onGallery error: {str(e)}")


def get_button_name(value):
    return dict(BUTTON_MAP).get(value, _("Unknown"))


def get_available_buttons():
    return [code for code, name in BUTTON_MAP]


def sessionstart(reason, session=None, **kwargs):
    """Initialize plugin components"""
    print(f"[AdvancedScreenshotConfig]sessionstart Initialize plugin components: {str(reason)} session {str(session)} ")
    if reason == 0 and session:
        # Register web interface
        root = kwargs.get('root', None)
        if root:
            root.putChild(b'grab', WebGrabResource(session))
        print(f"[AdvancedScreenshotConfig]sessionstart Initialize root: {str(root)} ")
        return ScreenshotCore(session)


def setup(session, **kwargs):
    session.open(AdvancedScreenshotConfig)


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            where=PluginDescriptor.WHERE_SESSIONSTART,
            fnc=sessionstart
        ),
        PluginDescriptor(
            name=_("Advanced Screenshot"),
            description=_("Professional screenshot tool"),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=setup
        ),
        PluginDescriptor(
            name=_("Advanced Screenshot Gallery"),
            description=_("View captured screenshots"),
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=lambda session: session.open(ScreenshotGallery)
        )
    ]


"""
"Usage: grab [commands] [filename]\n\n"
"command:\n"
"-o only grab osd (framebuffer) when using this with png or bmp\n"
"   fileformat you will get a 32bit pic with alphachannel\n"
"-v only grab video OSD (on-screen display)\n"
"-i (video device) to grab video (default 0)\n"
"-d always use osd resolution (good for skinshots)\n"
"-n dont correct 16:9 aspect ratio\n"
"-r (size) resize to a fixed width, maximum: 1920\n"
"-l always 4:3, create letterbox if 16:9\n"
"-b use bicubic picture resize (slow but smooth)\n"
"-j (quality) produce jpg files instead of bmp (quality 0-100)\n"
"-p produce png files instead of bmp\n"
"-q Quiet mode, don't output debug messages\n"
"-s write to stdout instead of a file (silent)\n"
"-h this help screen\n\n"
# -t=NUMBER — timeout in seconds for grab
# -a=1 — capture with audio enabled (video stream only)
"If no command is given the complete picture will be grabbed.\n"
"If no filename is given /tmp/screenshot.[bmp/jpg/png] will be used.\n");
"""
