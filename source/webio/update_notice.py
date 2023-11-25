from source.util import *


def upd_message():
    ret_message = ""
    version_num = int(GIAconfig.General_Version.split('.')[-1])
    if version_num != int(GIA_VERSION.split(".")[-1]):
        ret_message += t2t("GIA 已升级到") + f"{GIA_VERSION}. \n"

    if version_num == 0:
        ret_message = t2t("Welcome to GIA!") + '\n\n'
        ret_message += t2t(
            'This software is open source, free of charge and for learning and exchange purposes only. The developer team has the final right to interpret this project. All problems arising from the use of this software are not related to this project and the developer team. If you encounter a merchant using this software to practice on your behalf and charging for it, it may be the cost of equipment and time, etc. The problems and consequences arising from this software have nothing to do with it.') + '\n\n'
        ret_message += t2t(
            'By using this software, you acknowledge that you have fully read and agree to the GIA License, User Agreement and the above statements.') + '\n\n'
        ret_message += t2t(
            'GIA is free and open source software on Github and Gitee. If you have purchased GIA from any source, you have been scammed.') + '\n\n'
    else:
        if version_num <= 500:
            ret_message += f"推荐删除tactic中的team.json和team_example_3.json，然后重启GIA。\n"
        if version_num < 753:
            ret_message += f"战斗策略自动填充已经可用。\n可以删除tactic中的team.json和team_example_3.json，然后重启GIA。\n"
        if version_num < 779:
            ret_message += f"现已支持多显示器多缩放设置。可能存在问题，欢迎反馈。\n"
        if version_num < 874:
            ret_message += f"config设置已重置，请重新设置config。\n"
            "tactic, collector等设置可以继续使用。\n"
            "注意：队伍设置现在默认为自适应，如果需要使用你自己的设置，请将AdaptiveTeamSetup(自适应队伍设置)设置为false。"
        if version_num < 933:
            ret_message += f"升级自定义任务的UI界面\n\
                        提升自定义任务采集成功率"
        if version_num < 1100:
            ret_message += "有新的启动器可用：python-git-program-launcher\n"
            "更多信息，请查看Release 0.9.0的更新通知。\n"
        if version_num < 1130:
            ret_message += "添加了游戏内辅助功能\n"
        if version_num < 1158:
            ret_message += "角色支持增加到4.2\n"\
                           "增加对那维莱特转圈圈的适配"

    x = load_json()
    x["Version"] = GIA_VERSION
    save_json(x)
    GIAconfig.update()
    return ret_message
