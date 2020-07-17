#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import threading

__all__ = ['ValuedThread',]

class ValuedThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.callback = kwargs.pop('thread_callback', None)
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()
        self._error = False
        
    def run(self):
        with self._lock:
            try:
                r = self._target(*self._args, *self._kwargs)
            except Exception as e:
                r = e
                self._error = True
            if self.callback is not None:
                self.callback()
            self._result = r
            
    @property
    def result(self):
        with self._lock:
            return self._result
    
    @property
    def error(self):
        return self._error