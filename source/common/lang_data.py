from source.util import *

# with open(f"{ROOT_PATH}\\assets\\LangData\\characters.json5", "r", encoding="utf-8") as f:
#     characters = json5.load(f)
characters = load_json("characters_name.json", f"{ROOT_PATH}\\assets\\characters_data")
characters_name_dict = load_json("characters_name_dict.json", f"{ROOT_PATH}\\assets\\characters_data")
def get_all_characters_name():
    ret_list = []
    for item in characters:
        if "en" in item:
            ret_list.append(item["en"])
        if "zhCN" in item:
            ret_list.append(item["zhCN"])
        if "ja" in item:
            ret_list.append(item["ja"])
    return ret_list

# 定义一个函数，根据内容和语言输出英文翻译
# def translate_character(content, language:str = GLOBAL_LANG):
#     language = language.replace("zh_CN",'zhCN')
#     language = language.replace("en_US",'en')
#     # 遍历data中的每个字典
#     for item in characters:
#         # 如果字典中有对应的语言键值，并且值等于内容
#         if language in item and item[language] == content:
#             # 返回字典中的英文键值
#             return item["en"]
#         if language in item and item["en"] == content:
#             # 返回字典中的英文键值
#             return item["en"]
#     # 如果没有找到匹配的内容，返回None
#     return None

def translate_character_auto(content):
    """输入任何语言的角色名，返回角色标准名（英文）
    支持别名识别。
    只支持精确识别。
    如果角色名不存在，返回None。

    Args:
        content (_type_): _description_

    Returns:
        _type_: _description_
    """
    for item in characters_name_dict:
        if content in item['alias']+[item['standard_name']]:
            return item['standard_name']
    # 如果没有找到匹配的内容，返回None
    return None

def query_character(name:str):
    # 遍历data中的每个字典
    for item in characters:
        # 遍历字典中的每个键值对
        for key, value in item.items():
            # 如果值等于字符串
            if value == name:
                # 返回True
                return True
    # 如果没有找到匹配的字符串，返回False
    return False

if __name__ == '__main__':
    print(translate_character_auto("Kazuha"))