#! /usr/bin/python
# encoding: utf-8

# Copyright 2011 Rory McCann <rory@technomancy.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

import time, datetime, pickle, signal
import pyxhook
import math, os

import pygtk
pygtk.require('2.0')
import pynotify

from threading import Thread, Timer, Event

import gobject, gtk, appindicator

TOO_FAST = [
    {'chars':5, 'sec':1},
    {'chars':50, 'sec':10},
    {'chars':200, 'sec': 60},
]

TOO_FAST.sort(key=lambda x:x['sec'])


class UpdateLabel(Thread):
    def __init__(self, indicator):
        Thread.__init__(self)
        self.indicator = indicator
        self.notifications = {}
        self.num_periods_good = 0
        self.num_periods_bad = 0

    def run(self):
        INTERVAL = 0.2
        while not self.indicator.finished.is_set():
            is_bad = False
            now = time.time()
            new_label_parts = []
            for period in TOO_FAST:
                num_this_period = len([x for x in self.indicator.keypresses if now - x < period['sec']])
                buffer = period['chars'] - num_this_period
                ratio = num_this_period / period['chars']
                new_label_parts.append("{buffer} ({time})".format(time=period['sec'], buffer=buffer))

                warning_string = "{num} keypresses in {time} sec, Max: {max}, ×{ratio:.1f} safe".format(num=num_this_period, time=period['sec'], ratio=ratio, max=period['chars'])
                if ratio > 1:
                    is_bad = True
                    notif = self.notifications.get(period['sec'], pynotify.Notification("Slow Down!", warning_string))
                    notif.update("Slow Down!", warning_string)
                    try:
                        notif.show()
                        self.notifications[period['sec']] = notif
                    except gobject.GError:
                        # Dunno what this is, but it can sometimes happen
                        pass

                else:
                    if period['sec'] in self.notifications:
                        notif = self.notifications[period['sec']]
                        try:
                            notif.close()
                        except gobject.GError:
                            # Dunno what this is, but it can sometimes happen
                            pass
                        del self.notifications[period['sec']]



            if is_bad:
                self.num_periods_bad += 1
            else:
                self.num_periods_good += 1
            ratio_good = self.num_periods_good / (self.num_periods_good + self.num_periods_bad)
            if ratio_good == 1.0:
                nines = u"∞ - "
            else:
                nines = "%.1f / " % ( -1 * math.log10( 1.0 - ratio_good ) )
            #percentage = (self.num_periods_good * 100) / (self.num_periods_good + self.num_periods_bad)
            self.indicator.ind.set_label(nines+ " ".join(new_label_parts))
            time.sleep(INTERVAL)

    def close_all_notifications(self):
        for _, notif in self.notifications.items():
            notif.close()



class TypeSlowerIndicator(object):
    def __init__(self):
        self.keypresses = []

        self.hm = pyxhook.HookManager()
        self.hm.HookKeyboard()
        self.hm.HookMouse()
        self.hm.KeyDown = self.keydown

        self.hm.start()

        ind = appindicator.Indicator ("indicator-sysmonitor",
          "sysmonitor",
            appindicator.CATEGORY_SYSTEM_SERVICES)

        ind.set_status(appindicator.STATUS_ACTIVE)
        ind.set_attention_icon("indicator-messages-new")
        ind.set_label("init")

        menu_item = gtk.MenuItem("Quit")
        menu_item.connect("activate", gtk.main_quit)
        menu = gtk.Menu()
        menu.append(menu_item)
        menu_item.show()
        ind.set_menu(menu)

        self.ind = ind

        self.finished = Event()

        self.updater = UpdateLabel(self)
        self.updater.start()


    def keydown(self, event):
        now = time.time()
        self.keypresses.append(now)

    def set_label(self, text):
        print text
        #self.ind.set_label(text, text)

    def cancel(self):
        self.finished.set()
        self.hm.cancel()
        self.updater.close_all_notifications()
        

def check_for_notify_osd():
    pids= [pid for pid in os.listdir('/proc') if pid.isdigit()]

    for pid in pids:
        cmdline = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read()
        if "notify-osd" in cmdline:
            print "Warning! you are running notify-osd, notifications won't work well. You should switch to notification-daemon with this command:"
            print "kill %s ; /usr/lib/notification-daemon/notification-daemon & " % pid
            break


def main():
    gtk.gdk.threads_init()
    check_for_notify_osd()
    indicator = TypeSlowerIndicator()

    try:
        if not pynotify.init("TypeSlower"):
            sys.exit(1)
        gtk.main()
    finally:
        indicator.cancel()

if __name__ == "__main__":
    main()
