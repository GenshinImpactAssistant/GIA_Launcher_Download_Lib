from source.util import *
from source.interaction.interaction_core import itt
from source.task.task_template import TaskTemplate
from source.common.base_threading import BaseThreading
from source.exceptions.util import *
from source.ui.ui import ui_control
from source.ui import page as UIPage

COLLECTION_PATH_TASK = "CollectionPathTask"
DOMAIN_TASK = "DomainTask"
MISSION_TASK = "MissionTask"
COMMISSION_TASK = "CommissionTask"
CLAIM_REWARD_TASK = "ClaimRewardTask"
LEY_LINE_OUTCROP_TASK = "LeyLineOutcropTask"
LAUNCH_GENSHIN_TASK = "LaunchGenshinTask"
COLLECT_IMAGE = "CollectImage"

class TaskManager(BaseThreading):
    def __init__(self) -> None:
        super().__init__(thread_name="TaskManager")
        self.reg_task_flag = False
        self.curr_task = TaskTemplate()
        self.task_list = []
        self.get_task_list = lambda:[]
        self.start_tasklist_flag = False
    
    def task_excepthook(self, args):
        # if 'stop_task_flag' in args.exc_value.__dict__:
        exception_instance = args.exc_value
        logger.exception(exception_instance)
        if isinstance(exception_instance, GIABaseException):
            if args.exc_value.stop_task_flag:
                self.stop_tasklist()
            if len(exception_instance.POSSIBLE_REASONS) > 0:
                i = 0
                for pr in exception_instance.POSSIBLE_REASONS:
                    i+=1
                    logger.error(f'{t2t("Possible Reason")} {i}: {pr}')
        if isinstance(exception_instance, SnapshotException):
            exception_instance.save_snapshot(itt.capture(jpgmode=FOUR_CHANNELS))
    
    def append_task(self, task_name):
        self.task_list.append(task_name)

    def set_tasklist(self, tasks):
        self.task_list = tasks

    def clear_task_list(self):
        self.task_list = []

    # def stop_tasklist(self):
    #     self.start_tasklist_flag = False
    
    def get_task_statement(self):
        if not self.start_tasklist_flag:
            return t2t("No Task Running")
        elif self.start_tasklist_flag and not self.reg_task_flag:
            return t2t("Loading")
        else:
            return self.curr_task.get_statement()
    
    def remove_task(self, task_name) -> bool:
        for i in range(len(self.task_list)):
            if self.task_list[i] == task_name:
                del(self.task_list[i])
                return True
        return False
        
    def start_stop_tasklist(self):
        self.start_tasklist_flag = not self.start_tasklist_flag
        self.curr_task.stop_threading()

    def stop_tasklist(self):
        if self.start_tasklist_flag:
            logger.info(t2t('stopping tasks'))
            logger.info(t2t('switch ui to bigmap'))
            ui_control.ui_goto(UIPage.page_bigmap)
            self.start_tasklist_flag = False
            self.curr_task.stop_threading()
    
    def start_stop_task(self, task_name):
        if not self.reg_task_flag:
            
            # if self.curr_task.stop_threading_flag:
            #     logger.info(t2t("End Task"))
            #     self.curr_task.end_task()
            #     self.reg_task_flag = not self.reg_task_flag
            if task_name == DOMAIN_TASK:
                from source.task.domain.domain_task import DomainTask
                self.curr_task = DomainTask()
                
            elif task_name == MISSION_TASK:
                from source.task.mission.mission_task import MissionTask
                self.curr_task = MissionTask()
            elif task_name == COMMISSION_TASK:
                from source.commission.commission_executor import CommissionExecutor
                self.curr_task = CommissionExecutor()
            elif task_name == CLAIM_REWARD_TASK:
                from source.task.claim_reward.claim_reward import ClaimRewardTask
                self.curr_task = ClaimRewardTask()
            elif task_name == LEY_LINE_OUTCROP_TASK:
                from source.task.ley_line_outcrop.ley_line_outcrop import LeyLineOutcropTask
                self.curr_task = LeyLineOutcropTask()
            elif task_name == LAUNCH_GENSHIN_TASK:
                from source.task.launch_genshin.launch_genshin import LaunchGenshin
                self.curr_task = LaunchGenshin()
            elif task_name == COLLECT_IMAGE:
                from source.task.collect_image.collect_image import CollectImage
                self.curr_task = CollectImage()
            elif task_name == 'CollectorTask':
                pass
            logger.info(t2t("Task") + task_name + t2t(" Start."))
            self.reg_task_flag = True
            self._add_sub_threading(self.curr_task)
            self.curr_task.continue_threading()
            
            # register sub-threading
            # for i in self.curr_task.thread_list:
            #     self._add_sub_threading(i) # start thread
        else:
            logger.info(t2t("End Task"))
            # if self.curr_task.is_task_running:
            #     self.curr_task.terminate_task()
            self.curr_task.stop_threading()
            self.sub_threading_list = []
            self.reg_task_flag = not self.reg_task_flag


    def loop(self):
        # TODO: 持续检测len(self.task_list), 任务队列中第一个任务完成后删除.
        if self.start_tasklist_flag:
            # self.task_list = self.get_task_list()
            if len(self.task_list) > 0:
                for i in self.task_list:
                    if self.checkup_stop_func():
                        break
                    if self.start_tasklist_flag == False:
                        break
                    self.start_stop_task(i)
                    while 1:
                        if not self.reg_task_flag:
                            break
                        if self.checkup_stop_func():
                            break
                        if self.start_tasklist_flag == False:
                            break
                        if self.curr_task.pause_threading_flag:
                            break
                        # try:
                        #     self.curr_task.exec_task()
                        # except TaskEndException as e:
                        #     logger.info(f"Task end manually")
                        time.sleep(0.2)
                    logger.info(f"task {i} end.")
                    self.start_stop_task(i)
                logger.info(f"all task end.")
                self.stop_tasklist()
                # self.pause_threading()
            else:
                logger.info(f"all task end.")
                self.stop_tasklist()

TASK_MANAGER = TaskManager()

if __name__ == '__main__':
    tm = TASK_MANAGER
    # keyboard.add_hotkey(load_json("keymap.json", f"{CONFIG_PATH_SETTING}")["task"], tm.start_stop_task, args=("CollectionPathTask",))
    while 1:
        time.sleep(1)
    
