import time
from ctypes import *
from util import *
import timer_module
from base_threading import BaseThreading
from assets.AutoTrackDLLAPI.AutoTrackAPI import AutoTracker

def del_log():
    logger.debug(_("cleaning cvautotrack files"))
    for root, dirs, files in os.walk(os.path.join(root_path)):
        for f in files:
            if f == "autoTrack.log":
                os.remove(os.path.join(root_path, "autoTrack.log"))
                logger.debug(_("autoTrack.log 1 cleaned"))
    for root, dirs, files in os.walk(os.path.join(root_path, "source")):
        for f in files:
            if f == "autoTrack.log":
                os.remove(os.path.join(root_path, "source", "autoTrack.log"))
                logger.debug(_("autoTrack.log 2 cleaned"))
    for root, dirs, files in os.walk(os.path.join(root_path, "source", "webio")):
        for f in files:
            if f == "autoTrack.log":
                os.remove(os.path.join(root_path, "source", "webio", "autoTrack.log"))
                logger.debug(_("autoTrack.log 3 cleaned"))
del_log()



class AutoTrackerLoop(BaseThreading):
    def __init__(self):
        super().__init__()
        self.setName("AutoTrackerLoop")
        self.loaded_flag = False
        self.position = [0,0]
        self.last_position = self.position
        self.in_excessive_error = False
        self.start_sleep_timer = timer_module.Timer(diff_start_time=61)
        self.history_posi = []
        self.history_timer = timer_module.Timer()
        # logger.debug(f"cvautotrack log: {cvAutoTracker.disable_log()}")
        # scene_manager.switchto_mainwin(max_time=5)
    
    def load_dll(self):
        self.cvAutoTracker = AutoTracker() # os.path.join(root_path, 'source\\cvAutoTrack_7.2.3\\CVAUTOTRACK.dll')
        self.cvAutoTracker.init()
        logger.info(_("cvAutoTrack DLL has been loaded."))
        logger.debug('1) err' + str(self.cvAutoTracker.get_last_error()))
        r = self.cvAutoTracker.disable_log()
        logger.debug(f"disable log {r}")
        time.sleep(2)
        self.position = self.cvAutoTracker.get_position()
        self.last_position = self.position
        self.rotation = self.cvAutoTracker.get_rotation()
        self.in_excessive_error = False
        self.start_sleep_timer = timer_module.Timer(diff_start_time=61)
        self.loaded_flag = True

    def run(self):
        ct = 0
        time.sleep(0.1)
        while 1:
            if not self.loaded_flag:
                time.sleep(2)
                continue
            
            time.sleep(self.while_sleep)
            if self.stop_threading_flag:
                return 0

            if self.pause_threading_flag:
                if self.working_flag:
                    self.working_flag = False
                time.sleep(1)
                continue

            if not self.working_flag:
                self.working_flag = True

            if self.checkup_stop_func():
                self.pause_threading_flag = True
                continue
            
            if self.start_sleep_timer.get_diff_time() >= 60:
                if self.start_sleep_timer.get_diff_time() <= 62:
                    logger.debug("cvAutoTrackerLoop switch to sleep mode.")
                time.sleep(0.8)
                continue
            
            
            
            self.rotation = self.cvAutoTracker.get_rotation()
            self.position = self.cvAutoTracker.get_position()
            
            
            if not self.position[0]:
                import scene_manager
                if scene_manager.get_current_pagename() == 'main':
                    logger.warning("??????????????????")
                else:
                    time.sleep(0.5)
                self.position = (False, 0, 0)
                self.in_excessive_error = True
                time.sleep(0.5)
                continue
            if ct >= 20:
                self.last_position = self.position
                self.in_excessive_error = False
                logger.debug("???????????????")
                ct = 0
            if euclidean_distance(self.position[1:], self.last_position[1:]) >= 50:
                # print("????????????")
                self.in_excessive_error = True
                ct += 1
            else:
                self.last_position = self.position
                self.in_excessive_error = False
                ct = 0
            if self.history_timer.get_diff_time()>=1:
                self.history_timer.reset()
                if len(self.history_posi)<30:
                    self.history_posi.append(self.position)
                else:
                    del(self.history_posi[0])
                    self.history_posi.append(self.position)
            # print(self.last_position)

    def get_position(self):
        if not self.loaded_flag:
            self.load_dll()
            time.sleep(3)
        self.start_sleep_timer.reset()
        return self.position

    def get_rotation(self):
        if not self.loaded_flag:
            self.load_dll()
            time.sleep(3)
        self.start_sleep_timer.reset()
        return self.rotation

    def is_in_excessive_error(self):
        if not self.loaded_flag:
            self.load_dll()
            time.sleep(3)
        self.start_sleep_timer.reset()
        return self.in_excessive_error
    
# logger.info(cvAutoTracker.verison())

# ?????????????????????????????????????????????
# ??????????????? `python ./main.py` ??????????????????????????????
if __name__ == '__main__':
    cal=AutoTrackerLoop()
    a = cal.get_position()
    print()
    # # ?????????????????????????????????????????????
    # # sleep(5)
    #
    # # print(cvAutoTracker.SetWorldCenter(793.9, -1237.8))
    #
    # # ????????????????????????DLL???
    # # tracker = AutoTracker('source\\CVAUTOTRACK.dll')
    #
    # # ???????????????????????????
    # # tracker.init()
    # # print('1) err', tracker.get_last_error(), '\n')
    #
    # # ??????????????????????????????????????????????????????????????????????????????
    # print(cvAutoTrackerLoop.get_position())
    # print('2) err', cvAutoTrackerLoop.get_position(), '\n')
    #
    # # ??????UID??????????????????
    # # print(cvAutoTrackerLoop.get_uid())
    # # print('3) err', cvAutoTrackerLoop.get_last_error(), '\n')
    #
    # # print(cvAutoTrackerLoop.get_direction())
    # # print('4) err', cvAutoTrackerLoop.get_last_error(), '\n')
    #
    # print(cvAutoTrackerLoop.get_rotation())
    # # print('5) err', cvAutoTrackerLoop.get_last_error(), '\n')
    #
    # while 1:
    #     # print(cvAutoTracker.get_rotation())
    #
    #     # ret = cvAutoTracker.get_position()
    #     # posi = cvAutoTracker.translate_posi(ret[1],ret[2])
    #     print(cvAutoTrackerLoop.get_position())
    #     time.sleep(0.2)
    #
    # # ?????????????????????????????????????????????????????????????????????????????????
    # cvAutoTracker.uninit()
    pass

# 0 263.25 0 -> 793.9 -1237.8

# 10 263.8 10 -> 773 -1258

# -10 -10 -> 811 -1217

# 740 -1012
# 684 -1518
# 3.3 3.4
