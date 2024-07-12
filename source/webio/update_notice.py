from source.util import *


def upd_message():
    ret_message = ""
    version_num = int(GIAconfig.General_Version.split('.')[-1])
    if version_num != int(GIA_VERSION.split(".")[-1]):
        ret_message += "# " + t2t("GIA 已升级到") + f"{GIA_VERSION} \n"

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
                           "增加对那维莱特转圈圈的适配\n"
        if version_num < 1176:
            ret_message += t2t('''
## v1.0.0.1176 新内容：
- 添加新自定义任务创建方式          
''')
        if version_num < 1190:
            ret_message += t2t('''
## v1.0.0.1190 新内容：
- 自动启动原神  
- 修复OCR坐标展开错误
- 适配夏洛蒂  
- 修复芙宁娜的战斗策略  
- 暂时禁用通用采集  
- 自动忽略无效任务名    
- 识别加载页面  
- 自动修复无效config参数  
- 已知bug修复  
''')
        if version_num < 1204:
            ret_message += t2t('''
        ## v1.0.0.1204 新内容：
        - 适配4.3探索派遣  
        - 自动领取每日纪行任务奖励  
        - 适配娜维娅  
        - 新增`禁用`型触发器，自动战斗时，使用该触发器的角色将不会被切换上场。  
        
        ## 修复：  
        - 识别未知UI页面
        ''')
        if version_num < 1206:
            ret_message += t2t('''
        ## v1.0.0.1206 新内容：
        - 自动战斗优化：所有角色空闲时使用position为Main的角色进行普通攻击

        ## 修复：  
        - 地脉衍出无法领取奖励的问题
        - 有时下载自定义任务失败的问题
        ''')
        if version_num < 1236:
            ret_message += t2t('''
        ## v1.0.0.1236 
        
        ## 新内容：
        - 添加每日委托“无人注意的盖伊” @DarkFlameMaster

        ## 修复：  
        - 适配4.6大地图UI更新
        - 加载UI界面识别错误
        - 自动战斗中的不必要警告
        ''')
        if version_num < 1279:
            ret_message += t2t('''
        ## v1.1.0.1279 

        ## 新内容：
        - 更新地图到4.6
        - 支持枫丹秘境，可以在设置界面选择
        - 添加半自动功能启动音效
        - 自动瞄准现在能够发现障碍物后的敌人
        - 自动瞄准在瞄准时会进行少量平A
        - 秘境失败后自动重试（测试中）
        - 自动大地图移动时，若队伍中有护盾角色将自动开盾
        - 图片采集功能（测试中）
    
        ## 修复：  
        - 修复半自动功能快捷键不起效问题
        - 修复在离岛的地图识别失败
        - 修复在进璃月港路上地图识别失败
        - 原神打开行为不正确
        - 重装原神后无法检测路径
        - 已知问题
        
        ## 优化：
        - ui识别失败多次后尝试按esc退出
        
        ''')


    x = load_json()
    x["Version"] = GIA_VERSION
    save_json(x)
    GIAconfig.update()
    return ret_message
