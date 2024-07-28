from source.util import *
import keyboard
from source.flow.utils.flow_template import FlowController, FlowTemplate, FlowConnector, EndFlowTemplate
import source.flow.utils.flow_code as FC, source.flow.utils.flow_state as ST
from source.interaction.minimap_tracker import tracker
from source.funclib import movement, generic_lib, collector_lib
from source.funclib.err_code_lib import *
import pytz, datetime
from source.ui.ui import ui_control
from source.ui import page as UIPage
from source.common.timer_module import AdvanceTimer, Timer
from source.ingame_ui.ingame_ui import set_notice
from source.integration_json.funclib import correction_collection_position


class PathRecorderConnector(FlowConnector):
    def __init__(self):
        super().__init__()


        # self.total_collection_list = []
        self.checkup_stop_func = None
        self.collection_path_dict = {}

        self.min_distance = 1
        self.path_name = ""
        self.last_direction = 999
        self.is_pickup_mode = False
        self.coll_name = ""
        self.start_as_ingame_func = False
        self.generator = ''

    def reset(self):
        self.path_name = ""
        self.last_direction = 999
        self.coll_name = ""

class PathRecorderCore(FlowTemplate):
    def __init__(self, upper: PathRecorderConnector):
        super().__init__(upper,flow_id=ST.PATH_RECORDER ,next_flow_id=ST.PATH_RECORDER_END)

        self.force_add_flag = None
        keyboard.add_hotkey('\\', self._start_stop_recording)
        self.COLLECTION_POSITION = []
        # for i in load_json("all_position.json", fr"{ROOT_PATH}/assets/POI_JSON_API"):
        from source.integration_json.reader import JIApi
        for i in JIApi.data.values():
            for j in i:
                self.COLLECTION_POSITION.append(tracker.convert_GenshinMap_to_cvAutoTrack(j.position))
        self.KONGYING_TAVERN_COLLECTION_POSITION = collector_lib.get_item_position_new("圣遗物调查点")

        self.upper = upper
        self.enter_flag = False
        self.upper.while_sleep = 0.05
        self.record_index=0
        self.pickup_icon_timer = AdvanceTimer(1).reset().start()
        self.position_migration_times = 0
        self.position_migration_timer = Timer()
        self.used_collection_position = []
        self.ENFORCE_FIX_LIMIT = 6

        # self.all_position = []

    def _add_posi_to_dict(self, posi:list):
        posi[0] = round(posi[0],3)
        posi[1] = round(posi[1],3)
        curr_motion = movement.get_current_motion_state()
        self.upper.collection_path_dict["position_list"].append(
            {
                "position":posi,
                "motion":curr_motion,
                "id":len(self.upper.collection_path_dict["position_list"])+1,
            }
        )
        # self.upper.collection_path_dict["all_position"].append(posi)
        logger.info(t2t("position added:")+
                    f"{posi} {curr_motion}"
                    )

    def get_all_position(self, posi_dict):
        all_posi = []
        for i in posi_dict["position_list"]:
            all_posi.append(i["position"])
        return all_posi

    def state_init(self):
        pass
        # self._next_rfc()

    def state_before(self):

        self.upper.collection_path_dict = {
            "name":"",
            "time":"",
            "start_position":[],
            "break_position":[],
            "end_position":[],
            "position_list":[],
            "additional_info":{
                "pickup_points":[]
            },
            "adsorptive_position":[],
            "generate_from":self.upper.generator
        }
        self.force_add_flag = False
        if self.upper.coll_name != "":
            # self.COLLECTION_POSITION = collector_lib.load_items_position(self.upper.coll_name)
            #TODO: get_item_position_new need upd?
            #  self.COLLECTION_POSITION = collector_lib.get_item_position_new(self.upper.coll_name)# [i['position'] for i in self.COLLECTION_POSITION]
            self.force_add_flag = True

        self.enter_flag = False
        self.used_collection_position = []
        self.record_index=0
        self.pickup_icon_timer = AdvanceTimer(1).reset().start()
        self.position_migration_times = 0
        # if not
        if self.upper.start_as_ingame_func:
            self._reinit_smallmap()
        curr_posi = tracker.get_position()
        self._add_break_position(curr_posi)
        self._next_rfc()

    def _reinit_smallmap(self):
        set_notice(t2t("Please take your hands off the keyboard and mouse while the position are being calibrated"))
        time.sleep(1)
        tracker.reinit_smallmap()
        set_notice(t2t("Position calibration complete. Happy recording"), timeout=4)

    def _start_stop_recording(self):
        if self.rfc == FC.INIT:
            self.rfc = FC.BEFORE
            logger.info(t2t("ready to start recording"))
        if self.rfc == FC.IN:
            self.rfc = FC.AFTER
            logger.info(t2t("ready to stop recording"))

    def _fix_position(self, p, offset=9.3):
        ed_list = quick_euclidean_distance_plist(p, self.COLLECTION_POSITION)
        if min(ed_list)<offset:
            rp = quick_sort_euclidean_distance_plist(p, self.COLLECTION_POSITION)[0]
            # rp = self.COLLECTION_POSITION[np.argmin(ed_list)]
            if list(rp) in self.used_collection_position:
                logger.info(f"position refix fail: {rp} used.")
                return p,False
            else:
                logger.info(f"position refix succ: {p} -> {rp}")
                self.used_collection_position.append(list(rp))
                return rp,True
        else:
            if min(ed_list)<15:
                logger.info(f"position refix fail: {p} {self.COLLECTION_POSITION[np.argmin(ed_list)]} 9<{min(ed_list)}<15")
            return p,False

    def _add_break_position(self, posi, f_exist=False, is_end = False):
        # 添加BP
        posi[0] = round(posi[0],3)
        posi[1] = round(posi[1],3)
        bpindex = len(self.upper.collection_path_dict["break_position"])
        if len(self.upper.collection_path_dict["break_position"])==0:
            self.upper.collection_path_dict["break_position"].append(list(posi))
            logger.info(f"break position added {posi}")
        elif (abs(euclidean_distance(posi,self.upper.collection_path_dict["break_position"][-1])) >= 5.2):
            if self.upper.is_pickup_mode:
                posi,succ = self._fix_position(posi)
                if self.force_add_flag:
                    if succ:
                        f_exist = True # add  a variable
            self.upper.collection_path_dict["break_position"].append(list(posi))
            logger.info(f"break position added {posi}")

            if self.upper.is_pickup_mode and f_exist:
                self.upper.collection_path_dict["additional_info"]["pickup_points"].append(bpindex)
                logger.info(f"pickup bp added: {bpindex}")
        else:
            logger.warning(f"break position too close")
            if is_end and self.upper.is_pickup_mode and self.force_add_flag:
                posi,succ = self._fix_position(posi, offset=20)
                if succ:
                    self.upper.collection_path_dict["break_position"].append(list(posi))
                    self.upper.collection_path_dict["additional_info"]["pickup_points"].append(bpindex)
                    logger.info(f"break position added {posi}")
                    logger.info(f"last pickup bp added: {bpindex}")
            if self.upper.is_pickup_mode:
                if f_exist:
                    if bpindex-1 not in self.upper.collection_path_dict["additional_info"]["pickup_points"]:
                        self.upper.collection_path_dict["additional_info"]["pickup_points"].append(bpindex-1)
                        logger.info(f"pickup bp added to bp-1: {bpindex-1}")

    def state_in(self):
        # 验证UI界面
        # if self.upper.start_as_ingame_func:
        #     set_notice(t2t("Recording..."), timeout=3)
        if not ui_control.verify_page(UIPage.page_main):
            return super().state_in()
        # 获得所有position
        all_posi = self.get_all_position(self.upper.collection_path_dict)
        curr_posi = tracker.get_position()
        # 识别当前角色方向
        curr_direction = tracker.get_direction()
        # 修正坐标偏移过大问题

        if not self.upper.start_as_ingame_func:  # 游戏内运行不需要验证坐标识别错误，这是为Video2Path服务的。
            migration_flag = False

            if len(self.upper.collection_path_dict["position_list"])>0:
                last_position = self.upper.collection_path_dict["position_list"][-1]["position"]
                if self.position_migration_times == 0:
                    migration_offset = 10
                else:
                    migration_offset = 10+min(self.ENFORCE_FIX_LIMIT,self.position_migration_timer.get_diff_time())*10 # 考虑时间与距离关系，*6不一定准确，Max=10+10*ENFORCE_FIX_LIMIT


                if euclidean_distance(curr_posi, last_position)>=migration_offset:
                    migration_flag = True # 偏移过大
                    logger.warning(f"坐标偏移过大: offset: {round(migration_offset,2)} current: {round(euclidean_distance(curr_posi, last_position),2)} time: {round(self.position_migration_timer.get_diff_time(),2)}")
                    if self.position_migration_times >= 2:
                        if self.position_migration_timer.get_diff_time()>=self.ENFORCE_FIX_LIMIT: # 偏移超过ENFORCE_FIX_LIMIT，强制修正
                            logger.warning(f"Position migration>28 within {self.ENFORCE_FIX_LIMIT}, reset position {last_position} -> {curr_posi}")
                            self.position_migration_times = 0
                            migration_flag = False # 强制修正坐标
                    if self.position_migration_times == 0:
                        self.position_migration_timer.reset() # 重置计时器
                    self.position_migration_times += 1

            if migration_flag:return super().state_in()
            self.position_migration_timer.reset()
        # migration verify end.

        # 添加position用于记录motion
        if len(all_posi)>10:
            min_dist = quick_euclidean_distance_plist(curr_posi, all_posi[-10:-1]).min()
        elif len(all_posi)>0:
            min_dist = quick_euclidean_distance_plist(curr_posi, all_posi).min()
        else:
            min_dist = 99999

        if min_dist >= self.upper.min_distance:
            self._add_posi_to_dict(list(curr_posi))
        # 识别F
        if self.upper.is_pickup_mode and not self.force_add_flag:
            if generic_lib.f_recognition():
                logger.info(f"found f")
                self._add_break_position(curr_posi, f_exist=True)
        # 吸附采集点
        if self.upper.is_pickup_mode:
            if generic_lib.f_recognition():
                ed_min = min(quick_euclidean_distance_plist(curr_posi, self.COLLECTION_POSITION))
                ed_min2 = min(quick_euclidean_distance_plist(curr_posi, self.KONGYING_TAVERN_COLLECTION_POSITION))
                if min(ed_min, ed_min2)<8:
                    # rp = list(self.COLLECTION_POSITION[np.argmin(ed_list)])
                    rp = list(curr_posi)
                    rp2 = list(correction_collection_position(rp))
                    if rp != rp2:
                        logger.info(f'correction position: genshin coordinate: {rp} -> {rp2}')
                    else:
                        logger.info(f'correction position: genshin coordinate {rp2} fail.')
                    if len(self.upper.collection_path_dict["adsorptive_position"]) != 0:
                        dist = min(quick_euclidean_distance_plist(rp2, self.upper.collection_path_dict["adsorptive_position"]))
                    else:
                        dist = 999
                    if dist > 5:
                    # if list(rp2) not in self.upper.collection_path_dict["adsorptive_position"]:
                        logger.info(f"add adsorptive position succ: {rp2}")
                        self.upper.collection_path_dict["adsorptive_position"].append(rp2)
                    else:
                        logger.info(f'add ads fail: too close: {dist}')

        # 计算视角朝向并添加BP
        if abs(movement.calculate_delta_angle(curr_direction, self.upper.last_direction)) >= 3.5:
            self._add_break_position(curr_posi)
            self.upper.last_direction = curr_direction

        # 第一次运行时初始化
        if not self.enter_flag:
            self.logger_or_notice(t2t("start recording"))
            self.enter_flag = True
            self.upper.collection_path_dict["start_position"]=list(tracker.get_position())
        return super().state_in()

    def _fix_bps(self):
        logger.info(f'bps fix {len(self.upper.collection_path_dict["break_position"])} -> {self.upper.collection_path_dict["additional_info"]["pickup_points"][-1]+1}')
        self.upper.collection_path_dict["break_position"] = \
        self.upper.collection_path_dict["break_position"]   \
        [:self.upper.collection_path_dict["additional_info"]["pickup_points"][-1]+1]
        return True

    def logger_or_notice(self, x:str):
        if self.upper.start_as_ingame_func:
            set_notice(x, timeout=3)
        else:
            logger.info(x)

    def state_after(self):
        # self.upper.total_collection_list.append(self.upper.collection_path_dict)
        curr_posi = tracker.get_position()
        self.upper.collection_path_dict["end_position"]=list(curr_posi)
        self._add_break_position(curr_posi, is_end=True)
        tz = pytz.timezone('Etc/GMT-8')
        t = datetime.datetime.now(tz)
        date = t.strftime("%Y%m%d%H%M%S")
        jsonname = f"{self.upper.path_name}{date}i{self.record_index}"
        self.record_index+=1
        # if self.upper.is_pickup_mode:
        #     self._fix_bps() # 这个功能好像与is_end=True功能冲突...
        save_path = fr"{ROOT_PATH}/dev_assets/tlpp/{jsonname}.py"
        save_path2 = fr"{ROOT_PATH}/dev_assets/tlpp"
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"{jsonname} = "+str(self.upper.collection_path_dict) + f"""
\n
import time\n
from source.mission.template.mission_just_collect import MissionJustCollect\n
if __name__ == '__main__':\n
    MissionJustCollect({jsonname}, 'tlpp_test').start_threading()\n
    while 1:\n
        time.sleep(0.2)\n
""")
        save_json(self.upper.collection_path_dict, f"{jsonname}.json", save_path2)
        # save_json(self.upper.collection_path_dict,json_name=jsonname,default_path=f"assets\\TeyvatMovePath")
        self.logger_or_notice(f"recording save in {save_path}, " + t2t("Record end."))
        self.rfc = FC.INIT


class PathRecorderEnd(EndFlowTemplate):
    def __init__(self, upper: FlowConnector):
        super().__init__(upper, flow_id=ST.PATH_RECORDER_END, err_code_id=ERR_PASS)

class PathRecorderController(FlowController):
    def __init__(self):
        super().__init__(PathRecorderConnector(), current_flow_id =  ST.PATH_RECORDER)
        self.flow_connector = self.flow_connector # type: PathRecorderConnector
        self.flow_connector.checkup_stop_func = self.checkup_stop_func

        self.pc = PathRecorderCore(self.flow_connector)

        self.append_flow(self.pc)
        self.append_flow(PathRecorderEnd(self.flow_connector))

    def reset(self):
        super().reset()

if __name__ == '__main__':
    pn = input("input your path name")
    prc = PathRecorderController()
    prc.flow_connector.path_name = pn
    prc.start()
    logger.info(f"Load over.")
    logger.info(f"ready to start.")
    while 1:
        time.sleep(1)