#!/usr/bin/python
# -*- coding: utf-8 -*-

from enigma import eConsoleAppContainer
from os import waitpid


class ConsoleItem:
    def __init__(self, containers, cmd, callback, extra_args, binary=False):
        self.filenamesaved = extra_args[0]
        self.containers = containers
        self.callback = callback
        self.extraArgs = extra_args[0]
        self.binary = binary
        self.container = eConsoleAppContainer()
        self.appResults = []
        if isinstance(cmd, list):
            name = " ".join(cmd)
        else:
            name = cmd
        if name in containers:
            name = str(name) + '@' + hex(id(self))
        self.name = name
        self.containers[name] = self

        if callback:
            self.appResults = []
            self.container.dataAvail.append(self.dataAvailCB)

        self.container.appClosed.append(self.finishedCB)

        if len(cmd) > 1:
            print(
                f"[Console] Processing command {str(cmd)} with arguments {str(cmd[1:])}")
        else:
            print(f"[Console] Processing command line  {str(cmd)}")

        retval = self.container.execute(*cmd)
        if retval:
            self.finishedCB(retval)

        if self.callback is None:
            pid = self.container.getPID()
            try:
                waitpid(pid, 0)
            except OSError as err:
                print(
                    f"[Console] Error {
                        str(
                            err.errno)}: Wait for command on PID {
                        str(pid)} to terminate failed! {
                        str(
                            err.strerror)}")

    def dataAvailCB(self, data):
        self.appResults.append(data)

    def finishedCB(self, retval):
        print(f"[Console] finishedCB  {str(retval)}")
        data = self.appResults
        try:
            del self.containers[self.name]
        except Exception as e:
            print(f"[Console] error del self.containers[self.name]  {str(e)}")

        try:
            del self.container.dataAvail[:]
        except Exception as e:
            print(f"[Console] error del dataAvail[:] {str(e)}")

        try:
            del self.container.appClosed[:]
        except Exception as e:
            print(f"[Console] del self.container.appClosed[:] {str(e)}")

        callback = self.callback
        if callback is not None:
            try:
                data = b''.join(self.appResults)
            except Exception as e:
                print(f"[Console][Error] Failed to join appResults: {str(e)}")
            try:
                with open(self.filenamesaved, "wb") as f:
                    f.write(data)
                    print(
                        f"[Console][Debug] Successfully wrote: {str(self.filenamesaved)}")
            except Exception as e:
                print(
                    f"[Console][Error] Failed to write binary data to file: {
                        str(e)}")

            callback(data, retval, self.filenamesaved)


class MyConsole:
    """
        Console by default will work with strings on callback.
        If binary data required class shoud be initialized with Console(binary=True)
    """

    def __init__(self, binary=False):
        self.appContainers = {}
        self.binary = binary
        print(f"[Console]self.binary console: {str(self.binary)}")

    def ePopen(self, cmd, callback=None, extra_args=[]):
        print(f"[Console]command: {str(cmd)}")
        return ConsoleItem(
            self.appContainers,
            cmd,
            callback,
            extra_args,
            self.binary)

    def eBatch(self, cmds, callback, extra_args=[], debug=False):
        self.debug = debug
        cmd = cmds.pop(0)
        self.ePopen(cmd, self.eBatchCB, [cmds, callback, extra_args])

    def eBatchCB(self, data, retval, _extra_args):
        (cmds, callback, extra_args) = _extra_args
        if self.debug:
            print(
                f"[Console][eBatch] retval={
                    str(retval)}, cmds left={
                    str(
                        len(cmds))}, data:\n{
                    str(data)}")
        if len(cmds):
            cmd = cmds.pop(0)
            self.ePopen(cmd, self.eBatchCB, [cmds, callback, extra_args])
        else:
            callback(extra_args)

    def kill(self, name):
        if name in self.appContainers:
            print(f"[Console]kill: {str(name)}")
            self.appContainers[name].container.kill()

    def killAll(self):
        for name, item in self.appContainers.items():
            print(f"[Console]killAll: {str(name)}")
            item.container.kill()
