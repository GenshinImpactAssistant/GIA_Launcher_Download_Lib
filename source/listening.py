

try:
    from source.util import *
except:
    from util import *
import time
import keyboard
import threading
from source.task import task_manager
from source.ingame_ui.ingame_ui import run_ingame_ui, win_ingame_ui
from source.ingame_assist.manager import IngameAssistManager
from source.semiauto_funcs.manager import SemiautoFuncManager
from source.logger import add_logger_to_GUI

TASK_MANAGER = task_manager.TASK_MANAGER
INGAME_ASSIST_MANAGER = IngameAssistManager()
SEMIAUTO_FUNC_MANAGER = SemiautoFuncManager()
threading.excepthook = TASK_MANAGER.task_excepthook
TASK_MANAGER.setDaemon(True)
TASK_MANAGER.start()
keyboard.add_hotkey(GIAconfig.Keymap_StartStop, SEMIAUTO_FUNC_MANAGER.apply_change)

# keyboard.add_hotkey(load_json("keymap.json", f"{CONFIG_PATH_SETTING}")["task"], TASK_MANAGER.start_stop_tasklist)

@logger.catch
def listening():
    if not DEBUG_MODE or True:
        # import giadep
        import giaocr
        import giayolo
        pt = time.time()
        # giadep.install_gia_dependence(source.util.ROOT_PATH)
        giaocr.install_gia_dependence(ROOT_PATH)
        giayolo.install_gia_dependence(ROOT_PATH)
        print(f"sha-1 verify cost: {time.time() - pt}")
    import source.generic_event
    add_logger_to_GUI(win_ingame_ui.log_poster, level= ('INFO' if not DEBUG_MODE else "DEBUG"))
    run_ingame_ui()
    logger.error('pyqt exit')
    # ingame_app.start("python", ["source\\ingame_ui\\ingame_ui.py"])
    # # main_app.waitForFinished()
    # print('start succ\n')
    #
    while 1:
        time.sleep(0.2)


if __name__ == '__main__':
    # 循环监听
    listening()
