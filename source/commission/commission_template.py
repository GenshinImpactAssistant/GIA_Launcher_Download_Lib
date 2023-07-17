from source.commission.util import *
from source.mission.mission_template import MissionExecutor
from source.map.position.position import *
from source.interaction.interaction_core import itt
from source.manager import asset
from source.common.timer_module import AdvanceTimer
from source.talk.talk import Talk

class LanguageError(Exception):pass

class CommissionTemplate(MissionExecutor, Talk):
    def __init__(self, commission_type, commission_position,is_CFCF=True,is_PUO=True,is_TMCF=True,is_CCT=False):
        MissionExecutor.__init__(self, is_CFCF=is_CFCF,is_PUO=is_PUO,is_TMCF=is_TMCF,is_CCT=is_CCT)
        Talk.__init__(self)

        self.commission_name = commission_type
        self.commission_position = commission_position

        self.is_pickup_spoils = False 
        self.is_commission_succ = False
        self.is_commission_start = False
        self._commission_end_timer = AdvanceTimer(4,2)
        self._commission_end_timer.start()

    def talk_skip(self, stop_func=None):
        if stop_func is None:stop_func=self.checkup_stop_func
        return super().talk_skip(stop_func)
    
    def talk_until_switch(self, stop_func=None):
        if stop_func is None:stop_func=self.checkup_stop_func
        return super().talk_until_switch(stop_func)
    
    def rec_commission_complete(self):
        r = itt.appear(IconCommissionCommissionComplete)
        if r:
            logger.info(t2t('commission complete'))
        return r

    def fight_until_commission_complete(self):
        self.start_combat()
        while 1:
            time.sleep(0.2)
            if self.rec_commission_complete(): break
        self.stop_combat()
    
    def is_commission_complete(self):
        if self.is_commission_start == False:
            if self.is_in_commission():
                self.is_commission_start = True
                return False
            else:
                return False
        else:
            if not self.is_in_commission():
                return self._commission_end_timer.reached_and_reset()
                # for debug
                if self._commission_end_timer.reached_and_reset():
                    print()
                    return True
                else:
                    return False
            else:
                self._commission_end_timer.reset()

    def is_in_commission(self):
        return itt.get_img_existence(asset.IconCommissionCommissionIcon)

    def commission_succ(self):
        self.is_commission_succ=True