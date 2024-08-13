from multiprocessing import Event, Process
import webview, time, threading

def show_qt_window():
    window = webview.create_window("GenshinImpactAssistant", "http://localhost:22268/", width=1600, height=900) # 1024 576
    webview.start(http_server=True, gui='qt')
    # window.show()
# import source.config
# print(source.config.template_translator())
# print(source.config.template_translator_tactic())

if __name__ == '__main__':
    from source.webio.webio import server_thread
    threading.Thread(target=server_thread, daemon=False).start()
    WEBUI_PROCESS = Process(target=show_qt_window)
    WEBUI_PROCESS.start()
    import source.listening
    source.listening.listening()


