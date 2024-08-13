from source.mission.mission_template import MissionExecutor, time, ENEMY_REACTION_FIGHT, combat_lib, logger, genshin_map, movement
from source.cvars import STOP_RULE_COMBAT


class MissionCombat(MissionExecutor):



    def __init__(self, dictname, name: str, **kwargs):
        """

        Args:
            dictname: dict(support) or str(not recommend)
            name:
        """
        self.is_circle_search_enemy = False


        super().__init__(is_CFCF=True, is_PUO=True, is_TMCF=True, is_CCT=True)
        self.__dict__.update(kwargs)
        self.dictname = dictname
        self.setName(name)

    def _exec_absorption(self):
        movement.land()
        pos = genshin_map.get_position()
        abs_pos = self.PUO.get_absorb_pos(pos)
        if self.is_circle_search_enemy:

            self.circle_search(pos, stop_rule=STOP_RULE_COMBAT,radius=3)
        combat_lib.CSDL.active_find_enemy()
        if combat_lib.CSDL.get_combat_state():
            logger.info('enter combat')
            self.start_combat()
            while combat_lib.CSDL.get_combat_state():
                time.sleep(0.5)
            self.stop_combat()

        # replace absorption position

        self.PUO.absorptive_positions.pop(self.PUO.absorptive_positions.index(abs_pos))
        self.PUO.absorptive_positions.append(list(genshin_map.get_position()))
        return super()._exec_absorption()

    def exec_mission(self):
        self.start_pickup()  # SweatFlower167910289922 SweatFlowerV2P120230507180640i0
        self.move_along(self.dictname, is_tp=True, is_precise_arrival=False, adsorb=True)
        time.sleep(2)  # 如果路径结束时可能仍有剩余采集物，等待。
        self.stop_pickup()
        # self.collect(MODE="AUTO",pickup_points=[[71, -2205],[65,-2230]])
