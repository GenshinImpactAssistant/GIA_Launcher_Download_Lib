import shutil, os
path1 = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(path1)
path2 = os.path.abspath(os.path.join(path1,r"../GIA_Launcher_Download_Lib"))

def verify_path(root):
    if not os.path.exists(root):
        verify_path(os.path.join(root, "../"))
        os.mkdir(root)
        print(f"dir {root} has been created")

def copy_from_to(rootpath):
    times = 0
    for root, dirs, files in os.walk(rootpath):
        if ".git" in root:
            continue
        if ".github" in root:
            continue
        for f in files:
            if f not in [".gitmodules", ".git"]:
                flag1 = False
                for iii in ["POI_JSON_API", "TeyvatMovePath", "PPOCRModels", "YoloxModels"]:
                    if iii in root:
                        flag1 = True
                        # print(f"{f} has been copied.\n from {os.path.join(root, f)}\n to {os.path.join(root.replace(path1, path2), f)}")
                if not flag1:
                    verify_path(root.replace(path1, path2))
                    shutil.copy(os.path.join(root, f), os.path.join(root.replace(path1, path2), f))
                    times+=1
    print(times)
    # for d in dirs:
    #     if d not in [".git"]:
    #         copy_from_to(os.path.join(root, d))

def del_files():
    import os
    import shutil

    dirPath = os.path.abspath(r"../GIA_Launcher_Download_Lib") # 你要删除的文件夹路径
    exceptFolder = [".git",".github"] # 你要保留的文件夹名称

    for fileName in os.listdir(dirPath):
        if fileName not in exceptFolder:
            filePath = os.path.join(dirPath, fileName)
            if os.path.isfile(filePath):
                os.remove(filePath) # 删除文件
            elif os.path.isdir(filePath):
                shutil.rmtree(filePath) # 删除文件夹

# del_files()
copy_from_to(path1)
