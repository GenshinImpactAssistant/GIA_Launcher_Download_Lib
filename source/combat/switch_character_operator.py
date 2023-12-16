from source.common import character
from source.funclib import combat_lib
from source.combat import tactic_operator
from source.common.base_threading import BaseThreading
from source.interaction.interaction_core import itt
from source.common.timer_module import Timer, AdvanceTimer
from source.util import *
from source.manager import asset
from source.combat.aim_operator import AimOperator
from source.api.pdocr_complete import ocr
from source.funclib import movement
from source.ui.ui import ui_control
from source.ui import page as UIPage

SHIELD = 'Shield'
CORE = 'Core'
SUB_CORE = 'SubCore'
ASSIST = "Assist"


def sort_flag_1(x: character.Character):
    return x.priority


class SwitchCharacterOperator(BaseThreading):
    """负责换人,同时控制策略执行和自动瞄准.

    Args:
        BaseThreading (_type_): _description_
    """

    def __init__(self):
        super().__init__()
        self.setName('SwitchCharacterOperator')
        self.chara_list = None

        self.tactic_operator = tactic_operator.TacticOperator()
        self.aim_operator = AimOperator()
        self._add_sub_threading(self.tactic_operator)
        self._add_sub_threading(self.aim_operator)

        self.current_character_num = 1
        self.switch_timer = Timer(diff_start_time=2)  # 换人冷却计时器
        self.tactic_operator.set_enter_timer(self.switch_timer)

        self.died_character = []  # 存储的是角色序号而非角色名称
        self.reborn_timer = Timer(diff_start_time=150)  # 鸡蛋复活计时器
        self.position_check_timer = AdvanceTimer(0.3).start()  # position级别角色检查计时器
        self.mode = "Normal"

    def run(self):
        while 1:
            time.sleep(0.1)
            if self.stop_threading_flag:
                self.tactic_operator.stop_threading()
                return

            if self.pause_threading_flag:
                if self.working_flag:
                    self.working_flag = False
                time.sleep(1)
                continue

            if not self.working_flag:  # tactic operator no working
                self.working_flag = True
            if self.checkup_stop_func():
                self.pause_threading_flag = True
                continue
            if self.mode == 'Shield':
                self.aim_operator.pause_threading()
                self.switch_character(switch_type="SHIELD")
                time.sleep(0.4)
            else:
                if self.aim_operator.sco_blocking_request.is_blocking():
                    self.aim_operator.sco_blocking_request.reply_request()
                    logger.debug("sco_blocking_request")
                    self.switch_character(switch_type="SHIELD")
                    time.sleep(0.2)
                    continue
                if self.tactic_operator.get_working_statement():  # tactic operator working
                    # time.sleep(0.1)
                    if self.position_check_timer.reached_and_reset():
                        logger.debug("tactic operator working")
                        self.switch_character(switch_type="SHIELD")
                else:
                    logger.debug("switch_character TRIGGER")
                    self.switch_character(switch_type="TRIGGER")
                    time.sleep(0.4)

    def _check_and_reborn(self, x) -> bool:
        """重生角色

        Returns:
            bool: Returns True if resurrection is successful or not required, otherwise returns False.
            
        """
        if itt.get_img_existence(asset.IconCombatCharacterDied, is_log=True):
            aopf = self.aim_operator.pause_threading_flag
            if not aopf:
                self.aim_operator.pause_threading()
            succ_flag_1 = False
            print(self.died_character)
            for i in range(10):
                if \
                        ocr.is_img_num_plus(
                            itt.capture(posi=asset.AreaCombatRevivalFoods.position, jpgmode=NORMAL_CHANNELS))[
                            0]:
                    break
                time.sleep(0.15)
                if self.checkup_stop_func():  # break
                    if not aopf: self.aim_operator.continue_threading()
                    return True
                r = itt.appear_then_click(asset.ButtonFoodEgg, is_log=True)
                if r:
                    succ_flag_1 = True
                    break
            if not succ_flag_1:
                logger.info("reborn failed")
                self.reborn_timer.reset()
                self.died_character.append(x)
                if not (ui_control.verify_page(UIPage.page_main) or ui_control.verify_page(UIPage.page_domain)):
                    itt.key_press('esc')
                if not aopf: self.aim_operator.continue_threading()
                return False  # failed

            for i in range(10):
                time.sleep(0.15)
                ret_check_and_reborn_2 = itt.appear_then_click(asset.ButtonGeneralConfirm, is_log=True)
                print(f"ret_check_and_reborn_2 {ret_check_and_reborn_2}")
                if ret_check_and_reborn_2: itt.delay('animation')
                if ui_control.verify_page(UIPage.page_main) or ui_control.verify_page(UIPage.page_domain):
                    self.reborn_timer.reset()
                    self.died_character = []  # clean list
                    time.sleep(0.3)  # 防止重复检测
                    if not aopf: self.aim_operator.continue_threading()
                    return True  # reborn succ

            self.reborn_timer.reset()
            if not (ui_control.verify_page(UIPage.page_main) or ui_control.verify_page(UIPage.page_domain)):
                itt.key_press('esc')
            time.sleep(0.3)  # 防止重复检测
            self.died_character.append(x)
            if not (ui_control.verify_page(UIPage.page_main) or ui_control.verify_page(UIPage.page_domain)):
                itt.key_press('esc')
            if not aopf: self.aim_operator.continue_threading()
            return False  # failed
        else:
            return True

    def switch_character(self, switch_type="TRIGGER"):
        """_summary_

        Args:
            switch_type (str, optional): 角色切换模式. Defaults to "TRIGGER". 
                "TRIGGER":使用trigger作为切换标准\n
                "SHIELD":仅切换并执行护盾类角色的策略组
            

        Returns:
            _type_: _description_
        """
        for chara in self.chara_list:
            logger.debug('check up in: ' + chara.name)
            if self.checkup_stop_func():
                return 0
            if chara.n in self.died_character:  # died
                if self.reborn_timer.get_diff_time() <= 125:  # reborn cd
                    continue
            tg = None
            if switch_type == "TRIGGER" and chara.trigger():
                tg = chara.tactic_group
            elif switch_type in ["CORE", "SHIELD"] and chara.is_position_ready(switch_type):
                tg = chara.tactic_group
            if tg != None:
                self.current_character_num = combat_lib.get_current_chara_num(self.checkup_stop_func)
                logger.debug(
                    f"switch_character: {switch_type}: targetnum: {chara.n} current num: {self.current_character_num} tactic group: {tg}")
                self.tactic_operator.pause_threading()
                if chara.n != self.current_character_num:
                    r = self._switch_character(chara.n)
                    if not r:  # Failed
                        continue
                self.tactic_operator.set_parameter(tg, chara)
                self.tactic_operator.restart_executor()
                self.tactic_operator.continue_threading()
                return True

    def _switch_character(self, x: int) -> bool:
        """_summary_

        Args:
            x (int): chara id(1~4)

        Returns:
            bool: True: 切换成功; False: 切换失败
        """
        # itt.middle_click()
        t = self.switch_timer.get_diff_time()
        combat_lib.chara_waiting(self.checkup_stop_func)  # 检测异常情况并处理
        logger.debug('try switching to ' + str(x))
        switch_succ_num = 0  # 切换成功计数
        switch_target_num = 2  # 目标次数
        for i in range(60):
            pt = time.time()
            if self.checkup_stop_func(): return False
            combat_lib.unconventionality_situation_detection()  # 处理USD
            itt.key_press(str(x))

            # 如果切换成功, 快速+2
            if combat_lib.get_current_chara_num(self.checkup_stop_func, max_times=5) == x:
                itt.delay(0.1, comment='quick switch delay')
                if combat_lib.get_current_chara_num(self.checkup_stop_func, max_times=5) == x:
                    switch_succ_num += 2

            # 检查并复活角色

            r = self._check_and_reborn(x)

            if not r:  # if r == False
                return False

            # 可能卡住,跳一跳
            if i > 10:
                if i == 11:
                    movement.jump_timer_reset()
                movement.jump_in_loop(jump_dt=3)
                if i > 45:
                    movement.move(
                        [movement.MOVE_AHEAD, movement.MOVE_LEFT, movement.MOVE_RIGHT, movement.MOVE_BACK][i % 4],
                        distance=3)
            if i > 55:
                logger.warning('角色切换失败')
            logger.trace(f"sco loop cost: {time.time() - pt}")
            if switch_succ_num >= switch_target_num:
                logger.debug(f"switch chara to {x} succ")
                self.current_character_num = x
                self.switch_timer.reset()
                # itt.delay(0.05)
                return True
        # self.current_num = x
        self.switch_timer.reset()
        # itt.delay(0.05)
        return False

    def pause_threading(self):
        if self.pause_threading_flag != True:
            self.pause_threading_flag = True
            self.tactic_operator.pause_threading()
            self.aim_operator.pause_threading()

    def continue_threading(self):
        if self.pause_threading_flag != False:
            logger.info(f"SCO is getting the character list")
            self.chara_list = combat_lib.get_chara_list()
            self.chara_list.sort(key=sort_flag_1, reverse=False)
            self.pause_threading_flag = False
            self.tactic_operator.set_parameter(None, None)
            self.tactic_operator.continue_threading()
            self.aim_operator.continue_threading()
            self.current_character_num = combat_lib.get_current_chara_num(self.checkup_stop_func)


if __name__ == '__main__':
    pass
    # import combat_loop
    # chara=combat_loop.get_chara_list()
    # sco=Switch_Character_Operator(chara)

    # to.set_parameter(chara.tactic_group,chara)
    # sco.start()
