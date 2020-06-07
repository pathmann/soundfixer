#!/usr/bin/env python3

import sys

from threading import Thread
from queue import Queue

import pulsectl


SINK = "alsa_output.pci-0000_25_00.0.analog-stereo"


class SinkSetter(Thread):
    def __init__(self, sinkid, q):
        Thread.__init__(self)
        self.sinkid = sinkid
        self.queue = q
        self.pulse = pulsectl.Pulse('soundfixer-sinksetter')

    def run(self):
        while True:
            sourceid = self.queue.get()
            try:
                self.pulse.sink_input_move(sourceid, self.sinkid)
            except Exception as e:
                print("exception: %s" % e)

            self.queue.task_done()


def get_sink(pulse):
    for sink in pulse.sink_list():
        if sink.name == SINK:
            return sink.index

    return None


def source_watcher(queue, ev):
    if ev.t == pulsectl.PulseEventTypeEnum.new and ev.facility == pulsectl.PulseEventFacilityEnum.sink_input:
        queue.put(ev.index)


def main(argv):
    pulse = pulsectl.Pulse('soundfixer-sourcewatcher')
    sinkid = get_sink(pulse)
    
    if sinkid is None:
        print("no sink found")
        return
    else:
        print("sink found: %s" % sinkid)
    
    queue = Queue()

    setter = SinkSetter(sinkid, queue)
    setter.daemon = True
    setter.start()

    pulse.event_mask_set('sink_input')
    pulse.event_callback_set(lambda ev: source_watcher(queue, ev))
    pulse.event_listen()


if __name__ == "__main__":
    main(sys.argv)