from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import sys
import json
from minecraft_launcher_lib import *
import minecraft_launcher_lib as mll
import subprocess

config = json.load(open('config.json', 'rb'))
settings = utils.generate_test_options()
settings['username'] = config['username']
settings['customResolution'] = config['customRes']
settings['resolutionWidth'] = str(config['size']['x'])
settings['resolutionHeight'] = str(config['size']['y'])

window_css = """
background-color: #303030;
"""

class SettingsWindow(QMainWindow):
    def __init__(self, mv):
        super().__init__()
        self.main_window = mv

        self.setStyleSheet(window_css)
        self.setWindowTitle('Настройки')
        self.setFixedSize(QSize(600, 400))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowIcon(QIcon('icon.png'))

        container = QFrame()
        container_layout = QVBoxLayout()
        container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.nickname = QLineEdit()
        self.nickname.setMaxLength(22)
        self.nickname.setPlaceholderText('Имя пользователя')
        self.nickname.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.nickname.setStyleSheet('color:white; width: 200px;')
        
        self.nickname.setText(config['username'])

        self.custom_size = QCheckBox('Кастомный размер')
        self.custom_size.setStyleSheet('color: white')
        self.custom_size.setChecked(config['customRes'])

        sc = QFrame()
        scl = QHBoxLayout()

        self.size_x = QLineEdit()
        self.size_x.setValidator(QIntValidator())
        self.size_x.setStyleSheet('color: white')
        self.size_x.setText(str(config['size']['x']))

        x = QLabel('x')
        x.setStyleSheet('color:white')

        self.size_y = QLineEdit()
        self.size_y.setValidator(QIntValidator())
        self.size_y.setStyleSheet('color: white')
        self.size_y.setText(str(config['size']['y']))


        self.hide_main_win = QCheckBox('Прятать основное окно при игре')
        self.hide_main_win.setStyleSheet('color: white')
        self.hide_main_win.setChecked(config['hideMainWindow'])

        scl.addWidget(self.size_x)
        scl.addWidget(x)
        scl.addWidget(self.size_y)
        scl.setContentsMargins(0, 0, 0, 0)
        sc.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sc.setLayout(scl)

        gitlink = QLabel('<a href="https://github.com/nosleepfor">Github</a>')


        save_button = QPushButton('Сохранить')
        save_button.pressed.connect(self.save)
        save_button.setStyleSheet('QPushButton { color: white; border:none; background-color: #202020; padding: 7px 15px; margin: 0; width: 100%; } QPushButton:hover {background-color: #111111}')
        

        container_layout.addWidget(self.nickname)
        container_layout.addWidget(self.custom_size)
        container_layout.addWidget(sc)
        container_layout.addWidget(self.hide_main_win)
        container_layout.addWidget(save_button)
        container_layout.addWidget(gitlink, alignment=Qt.AlignmentFlag.AlignBottom)
        container.setLayout(container_layout)

        self.setCentralWidget(container)

    def save(self):
        config['username'] = self.nickname.text()
        settings['username'] = self.nickname.text()

        config['customRes'] = self.custom_size.isChecked()
        settings['customResolution'] = self.custom_size.isChecked()

        config['size']['x'] = int(self.size_x.text())
        settings['resolutionWidth'] = self.size_x.text()

        config['size']['y'] = int(self.size_y.text())
        settings['resolutionHeight'] = self.size_y.text()

        config['hideMainWindow'] = self.hide_main_win.isChecked()
        json.dump(config, open('config.json', 'w'), indent=2)
        self.main_window.username_label.setText(config['username'])

class PlayWindow(QMainWindow):
    def __init__(self, mv):
        super().__init__()

        self.main_window = mv

        self.setStyleSheet('background-color: #303030;')
        self.setWindowTitle('Лог игры')
        self.setFixedSize(QSize(600, 400))
        self.setWindowIcon(QIcon('icon.png'))

        self.container = QFrame()
        self.clayout = QVBoxLayout()

        self.log = QTextEdit()
        self.log.setStyleSheet('color:white;')
        self.log.setReadOnly(True)
        
        self.stop_btn = QPushButton('Остановить')
        self.stop_btn.setStyleSheet('QPushButton { color: white; border:none; background-color: #202020; padding: 7px 15px; margin: 0; width: 100%; } QPushButton:hover {background-color: #111111}')
        self.stop_btn.pressed.connect(self.stop_game)

        self.clayout.addWidget(self.log)
        self.clayout.addWidget(self.stop_btn)
        self.container.setLayout(self.clayout)

        self.setCentralWidget(self.container)

    def appendLog(self, log_text):
        self.log.append(log_text)

    def stop_game(self):
        if self.main_window.playing:
            self.main_window.play_worker.end()

class InstallationWorker(QObject):
    finished = pyqtSignal()
    set_text_visible = pyqtSignal(bool)
    set_prog_visible = pyqtSignal(bool)
    set_text = pyqtSignal(str)
    set_max_prog = pyqtSignal(int)
    set_prog = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def run(self):
        mc_dir = utils.get_minecraft_directory()

        print(self.parent)

                
        self.set_text_visible.emit(True)
        self.set_prog_visible.emit(True)
        
        mll.install.install_minecraft_version(self.parent.versions_combobox.currentText(), mc_dir, {
                        'setMax': lambda x: self.set_max_prog.emit(x),
                        'setProgress': lambda x: self.set_prog.emit(x),
                        'setStatus': lambda x: self.set_text.emit(x)
        })

        self.set_prog_visible.emit(False)
        self.set_text_visible.emit(False)

        self.finished.emit()

class PlayWorker(QObject):
    finished = pyqtSignal()

    append_log = pyqtSignal(str)

    def __init__(self, ver):
        super().__init__()
        self.ver = ver

    def run(self):
        

        self.proc = subprocess.Popen(
            command.get_minecraft_command(self.ver, utils.get_minecraft_directory(), settings),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            text=True,
            bufsize=1
            )
        
        for line in self.proc.stdout:
            self.append_log.emit(line)

        self.proc.wait()

        self.finished.emit()

    def end(self):
        self.proc.terminate()
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.installation_going = False
        self.installation_thread = None
        self.installation_worker = None

        self.playing = False
        self.play_thread = None
        self.play_worker = None



        self.setFixedSize(QSize(800, 600))
        self.setStyleSheet(window_css)
        self.setWindowTitle('ZaLauncher')
        self.setWindowIcon(QIcon('icon.png'))

        settings_window = SettingsWindow(self)
        self.play_window = PlayWindow(self)

        container = QFrame()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

        top_bar = QFrame()
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        self.username_label = QLabel(config['username'])
        self.username_label.setStyleSheet('color: white; font-size: 32px')
        


        bottom_bar = QFrame()
        bottom_bar.setStyleSheet('margin: 0 0; padding: 0 0;')
        bottom_bar_layout = QHBoxLayout()

        


        self.installation_text = QLabel('And have a stab')
        #self.installation_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.installation_text.setStyleSheet('color: white; text-align: center; width: 100%')
        self.installation_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.installation_text.setVisible(False)

        

        self.installation_progressbar = QProgressBar()
        #self.installation_progressbar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.installation_progressbar.setStyleSheet('width: 100%; color:white;')
        self.installation_progressbar.setTextVisible(False)
        self.installation_progressbar.setVisible(False)
        

        self.versions_combobox = QComboBox()
        self.versions_combobox.setStyleSheet('color: white; border: none; background-color: #202020;')
        self.updateVersions()
        self.versions_combobox.setCurrentText(config['selected_version'])

        self.versions_combobox.currentTextChanged.connect(self.versionSelected)
        self.versions_combobox.currentTextChanged.connect(self.confSelectedVersion)
        

        self.play_button = QPushButton('Play')
        self.play_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.play_button.setStyleSheet('QPushButton { color: white; border:none; background-color: #202020; padding: 7px 15px; margin: 0; width: 100%; } QPushButton:hover {background-color: #111111}')
        self.play_button.pressed.connect(self.buttonPressed)

        bottom_bar_layout.addWidget(self.play_button)
        bottom_bar.setLayout(bottom_bar_layout)
        bottom_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        bottom_bar.setStyleSheet('width: 100%')
        #bottom_bar_layout.addStretch()

        top_bar_layout.addWidget(self.username_label)

        top_bar.setLayout(top_bar_layout)

        bottom_bar_layout.setContentsMargins(0, 0, 0, 0)

        bottom_bar2 = QFrame()
        bottom_bar2_layout = QHBoxLayout()
        bottom_bar2_layout.setContentsMargins(0, 0, 0, 0)

        show_log_button = QPushButton('Показать окно с логом')
        show_log_button.setStyleSheet('QPushButton { color: white; border:none; background-color: #202020; padding: 7px 15px; margin: 0; width: 100%; } QPushButton:hover {background-color: #111111}')
        show_log_button.pressed.connect(self.play_window.show)

        show_settings_button = QPushButton('Настройки')
        show_settings_button.setStyleSheet('QPushButton { color: white; border:none; background-color: #202020; padding: 7px 15px; margin: 0; width: 100%; } QPushButton:hover {background-color: #111111}')
        show_settings_button.pressed.connect(lambda: settings_window.show())


        bottom_bar2_layout.addWidget(show_log_button)
        bottom_bar2_layout.addWidget(show_settings_button)
        bottom_bar2.setLayout(bottom_bar2_layout)


        layout.addWidget(top_bar)
        layout.addStretch()
        layout.addWidget(self.installation_text)
        layout.addWidget(self.installation_progressbar)
        layout.addWidget(self.versions_combobox)
        layout.addWidget(bottom_bar, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(bottom_bar2, alignment=Qt.AlignmentFlag.AlignBottom)

        container.setLayout(layout)
        self.setCentralWidget(container)

           

    def updateVersions(self):
        for ver in utils.get_version_list():
            if ver['type'] == 'release': self.versions_combobox.addItem(ver['id'])

    def isVersionInstalled(self, version):
        if version in [ver['id'] for ver in utils.get_installed_versions(utils.get_minecraft_directory())]:
            return True
        else:
            return False
        
    def confSelectedVersion(self):
        config['selected_version'] = self.versions_combobox.currentText()
        json.dump(config, open('config.json', 'w'), indent=2)
        
    def versionSelected(self):
        if self.isVersionInstalled(self.versions_combobox.currentText()):
            self.play_button.setText('Играть')
        else:
            self.play_button.setText('Установить')

    def buttonPressed(self):
        # TODO: SPLIT THOSE LINES WITH SOME SENSE
        if not self.installation_going and not self.playing and not self.isVersionInstalled(self.versions_combobox.currentText()):
            self.installation_thread = QThread()
            self.installation_worker = InstallationWorker(self)
            self.installation_worker.moveToThread(self.installation_thread)

            self.installation_thread.started.connect(self.installation_worker.run)
            self.installation_worker.finished.connect(self.installation_thread.quit)
            self.installation_worker.finished.connect(self.installation_worker.deleteLater)
            self.installation_thread.finished.connect(self.installation_thread.deleteLater)

            self.installation_worker.set_text_visible.connect(self.installation_text.setVisible)
            self.installation_worker.set_prog_visible.connect(self.installation_progressbar.setVisible)
            self.installation_worker.set_text.connect(self.installation_text.setText)
            self.installation_worker.set_prog.connect(self.installation_progressbar.setValue)
            self.installation_worker.set_max_prog.connect(self.installation_progressbar.setMaximum)
            

            self.installation_thread.start()
        
        elif not self.playing:
            self.play_thread = QThread()
            self.play_worker = PlayWorker(self.versions_combobox.currentText())
            self.play_worker.moveToThread(self.play_thread)

            self.play_thread.started.connect(self.play_worker.run)

            self.play_worker.finished.connect(self.play_thread.quit)
            self.play_worker.finished.connect(self.play_worker.deleteLater)
            
            self.play_thread.finished.connect(lambda: setattr(self, 'playing', False))
            self.play_thread.finished.connect(self.play_window.hide)
            self.play_thread.finished.connect(lambda: self.play_window.log.setText(''))
            self.play_thread.finished.connect(self.play_thread.deleteLater)

            self.play_worker.append_log.connect(self.play_window.appendLog)

            if config['hideMainWindow']:
                self.hide()
                self.play_thread.finished.connect(self.show)

            self.playing = True
            self.play_window.show()
            self.play_thread.start()



if __name__ == '__main__':
    app = QApplication(sys.argv)

    win = MainWindow()
    win.show()

    app.exec()