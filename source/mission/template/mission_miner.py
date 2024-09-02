import threading

from source.mission.mission_template import MissionExecutor, genshin_map
from source.cvars import STOP_RULE_COMBAT
from source.funclib import movement, combat_lib
from source.manager import img_manager
from source.common.base_threading import BaseThreading, ThreadBlockingRequest
from source.interaction.interaction_core import itt
from source.common.timer_module import Timer,AdvanceTimer
from source.util import *


def left_clicker_finding(alive_timer:AdvanceTimer):
    while 1:
        itt.left_click()
        time.sleep(5)
        if alive_timer.reached():
            break

class MissionMiner(MissionExecutor):



    def __init__(self, dictname, name: str, **kwargs):
        """

        Args:
            dictname: dict(support) or str(not recommend)
            name:
        """
        self.is_circle_search_enemy = False
        self.enemy_flag = True
        self.corr_rate = 0.8
        self.sub_threading_alive_timer = AdvanceTimer(10)

        super().__init__(is_CFCF=True, is_PUO=True, is_TMCF=True, is_CCT=True)
        self.__dict__.update(kwargs)
        self.dictname = dictname
        self.setName(name)

    def get_enemy_feature(self, ret_mode=1):
        """获得敌人位置

        Args:
            ret_mode (int, optional): _description_. Defaults to 1.

        Returns:
            _type_: _description_
        """
        cap = self.itt.capture(jpgmode=FOUR_CHANNELS)
        orsrc = cap.copy()
        imsrc = combat_lib.get_mineral_blood_bar_img(cap)
        _, imsrc2 = cv2.threshold(imsrc, 1, 255, cv2.THRESH_BINARY)
        # cv2.imshow('123',retimg)
        # cv2.waitKey(100)
        if ret_mode == 1: # 返回点坐标
            ret_point = img_manager.get_rect(imsrc2, orsrc, ret_mode=2)
            return ret_point
        elif ret_mode == 2: # 返回高度差
            ret_rect = img_manager.get_rect(imsrc2, orsrc, ret_mode=0)
            if ret_rect is None:
                return None
            return ret_rect[2] - ret_rect[0]

    def _lock_on_enemy(self):
        ret_points = self.get_enemy_feature() # 获得敌方血条坐标
        if ret_points is None:
            return 0
        points_length = []
        if len(ret_points) == 0:
            return 0
        else:
            for point in ret_points:
                mx, my = SCREEN_CENTER_X,SCREEN_CENTER_Y
                points_length.append((point[0] - mx) ** 2 + (point[1] - my) ** 2)
            closest_point = ret_points[points_length.index(min(points_length))] # 获得距离鼠标坐标最近的一个坐标
            px, py = closest_point
            mx, my = SCREEN_CENTER_X,SCREEN_CENTER_Y
            px = (px - mx) / (2.4*self.corr_rate)
            py = (py - my) / (2*self.corr_rate) + 50 # 获得鼠标坐标偏移量
            # print(px,py)
            px=maxmin(px,200,-200)
            py=maxmin(py,200,-200)
            self.itt.move_to(px, py, relative=True)
            py-=50
            return px+py

    def is_mineral_exist(self):
        self.sub_threading_alive_timer.reset()
        if self.checkup_stop_func(): return True
        return self.get_enemy_feature() != []

    def _keep_distance_with_enemy(self):  # 期望敌方血条像素高度为7px # TODO:与敌人保持距离
        target_px = 7
        if self.enemy_flag:
            px = self.get_enemy_feature(ret_mode=2)
            if px is None:
                return False
            if px < target_px:
                itt.key_down('w')
                while 1:
                    time.sleep(0.05)
                    if self.checkup_stop_func():
                        itt.key_up('w')
                        return False
                    px = self.get_enemy_feature(ret_mode=2)
                    if px is None:
                        itt.key_up('w')
                        return False
                    if px >= target_px:
                        itt.key_up('w')
                        return True
            else:
                return True



    def _exec_absorption(self):
        movement.land()
        pos = genshin_map.get_position()
        abs_pos = self.PUO.get_absorb_pos(pos)
        movement.move_to_position(abs_pos, stop_func=self.checkup_stop_func)
        self.start_combat(mode="Shield")

        # mineeeeeeee
        while 1:
            siw()
            if self.checkup_stop_func(): break

            # find mineral
            self.sub_threading_alive_timer.reset()
            t_ = threading.Thread(target=left_clicker_finding, args=(self.sub_threading_alive_timer,))
            t_.start()
            self.circle_search(center_posi=abs_pos,radius=3,stop_func=self.is_mineral_exist)
            t_.join()
            if self.is_mineral_exist():
                # mine
                while 1:
                    itt.left_click()
                    if self.checkup_stop_func(): break
                    self._lock_on_enemy()
                    if not self.is_mineral_exist(): break

                continue
            else:
                break

        self.stop_combat()

        # replace absorption position

        self.PUO.absorptive_positions.pop(self.PUO.absorptive_positions.index(abs_pos))
        self.PUO.absorptive_positions.append(list(genshin_map.get_position()))
        super()._exec_absorption(mode='PLANT')


    def exec_mission(self):
        self.start_pickup()  # SweatFlower167910289922 SweatFlowerV2P120230507180640i0
        self.move_along(self.dictname, is_tp=True, is_precise_arrival=False, adsorb=True)
        time.sleep(2)  # 如果路径结束时可能仍有剩余采集物，等待。
        self.stop_pickup()
        # self.collect(MODE="AUTO",pickup_points=[[71, -2205],[65,-2230]])

if __name__ == '__main__':
    mm=MissionMiner('1','1')
    while 1:
        time.sleep(1)
        print(mm.is_mineral_exist())