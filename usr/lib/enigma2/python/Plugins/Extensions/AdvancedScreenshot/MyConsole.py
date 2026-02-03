#!/usr/bin/python
# -*- coding: utf-8 -*-
# RAED & mfaraj57 &  (c) 2018
# mod Lululla 20251113

from enigma import eConsoleAppContainer
from os import waitpid


class ConsoleItem:
    """Class representing a console command item."""
    
    def __init__(self, containers, cmd, callback, extra_args, binary=False):
        """Initialize console item.
        
        Args:
            containers: Dictionary of active containers
            cmd: Command to execute (string or list)
            callback: Callback function for command completion
            extra_args: Extra arguments for callback
            binary: Whether to handle binary data
        """
        self.filenamesaved = extra_args[0]
        self.containers = containers
        self.callback = callback
        self.extraArgs = extra_args[0]
        self.binary = binary
        self.container = eConsoleAppContainer()
        self.appResults = []
        
        # Generate unique name for this command
        if isinstance(cmd, list):
            name = " ".join(cmd)
        else:
            name = cmd
            
        if name in containers:
            name = str(name) + '@' + hex(id(self))
        self.name = name
        self.containers[name] = self

        # Set up callbacks
        if callback:
            self.appResults = []
            self.container.dataAvail.append(self.dataAvailCB)

        self.container.appClosed.append(self.finishedCB)

        # Log command execution
        if len(cmd) > 1:
            print("[Console] Processing command " + str(cmd) + " with arguments " + str(cmd[1:]))
        else:
            print("[Console] Processing command line " + str(cmd))

        # Execute command
        retval = self.container.execute(*cmd)
        if retval:
            self.finishedCB(retval)

        # Wait for command if no callback provided
        if self.callback is None:
            pid = self.container.getPID()
            try:
                waitpid(pid, 0)
            except OSError as err:
                print("[Console] Error " + str(err.errno) + ": Wait for command on PID " + str(pid) + " to terminate failed! " + str(err.strerror))

    def dataAvailCB(self, data):
        """Callback for data availability from command output.
        
        Args:
            data: Data received from command
        """
        self.appResults.append(data)

    def finishedCB(self, retval):
        """Callback for command completion.
        
        Args:
            retval: Return value from command execution
        """
        print("[Console] finishedCB " + str(retval))
        
        # Clean up container
        try:
            del self.containers[self.name]
        except Exception as e:
            print("[Console] error del self.containers[self.name] " + str(e))

        # Clean up callbacks
        try:
            del self.container.dataAvail[:]
        except Exception as e:
            print("[Console] error del dataAvail[:] " + str(e))

        try:
            del self.container.appClosed[:]
        except Exception as e:
            print("[Console] del self.container.appClosed[:] " + str(e))

        # Execute callback if provided
        callback = self.callback
        if callback is not None:
            # Join all collected data
            try:
                data = b''.join(self.appResults)
            except Exception as e:
                print("[Console][Error] Failed to join appResults: " + str(e))
                return
                
            # Write data to file
            try:
                with open(self.filenamesaved, "wb") as f:
                    f.write(data)
                    print("[Console][Debug] Successfully wrote: " + str(self.filenamesaved))
            except Exception as e:
                print("[Console][Error] Failed to write binary data to file: " + str(e))
                return

            # Call user callback with results
            callback(data, retval, self.filenamesaved)


class MyConsole:
    """Console class for executing commands with callbacks.
    
    Console by default will work with strings on callback.
    If binary data required class should be initialized with Console(binary=True)
    """
    
    def __init__(self, binary=False):
        """Initialize console.
        
        Args:
            binary: Whether to handle binary data (default: False)
        """
        self.appContainers = {}
        self.binary = binary
        print("[Console]self.binary console: " + str(self.binary))

    def ePopen(self, cmd, callback=None, extra_args=None):
        """Execute a single command.
        
        Args:
            cmd: Command to execute
            callback: Callback function for completion
            extra_args: Extra arguments for callback
            
        Returns:
            ConsoleItem object
        """
        if extra_args is None:
            extra_args = []
            
        print("[Console]command: " + str(cmd))
        return ConsoleItem(self.appContainers, cmd, callback, extra_args, self.binary)

    def eBatch(self, cmds, callback, extra_args=None, debug=False):
        """Execute multiple commands in batch.
        
        Args:
            cmds: List of commands to execute
            callback: Callback function for completion of all commands
            extra_args: Extra arguments for callback
            debug: Enable debug output (default: False)
        """
        if extra_args is None:
            extra_args = []
            
        self.debug = debug
        cmd = cmds.pop(0)
        self.ePopen(cmd, self.eBatchCB, [cmds, callback, extra_args])

    def eBatchCB(self, data, retval, _extra_args):
        """Callback for batch command execution.
        
        Args:
            data: Data from command output
            retval: Return value from command
            _extra_args: Extra arguments containing remaining commands
        """
        (cmds, callback, extra_args) = _extra_args
        
        if self.debug:
            print("[Console][eBatch] retval=" + str(retval) + ", cmds left=" + str(len(cmds)) + ", data:\n" + str(data))
            
        if len(cmds):
            # Execute next command in batch
            cmd = cmds.pop(0)
            self.ePopen(cmd, self.eBatchCB, [cmds, callback, extra_args])
        else:
            # All commands completed, call user callback
            callback(extra_args)

    def kill(self, name):
        """Kill a specific command by name.
        
        Args:
            name: Name of command to kill
        """
        if name in self.appContainers:
            print("[Console]kill: " + str(name))
            self.appContainers[name].container.kill()

    def killAll(self):
        """Kill all running commands."""
        for name, item in self.appContainers.items():
            print("[Console]killAll: " + str(name))
            item.container.kill()
