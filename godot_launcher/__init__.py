from godot_launcher.config import Config
from godot_launcher.ui import UI
from godot_launcher.scraper import Scraper
from godot_launcher import utils
from godot_launcher.exceptions import *
import tempfile
import shutil
import sys
import subprocess
import platform
import logging

class App():
    logger = logging.getLogger("App")
    
    def __init__(self):
        machine_info = utils.get_machine_info()
        if not machine_info:
            input("ERROR: Unsupported OS! Press Enter to exit")
            sys.exit()
        self.version = "0.1.0"
        self.config = Config(self)
        self.ui = UI(self)
        self.scraper = Scraper(self)
        self.temp_install_dir = ""
        
        logging.basicConfig(filename=self.config.logfile, level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        self.logger.info(f"Succuessfully initialized GodotLauncher v{self.version}. Running on {machine_info['bits']}-bit {machine_info['os_name']}")

    def launch(self, version_folder):
        engine_path = utils.get_executable_in_folder(version_folder)
        if platform.system() == 'windows':
            creation_flags = subprocess.CREATE_NEW_CONSOLE
        else:
            creation_flags = 0

        try:
            subprocess.Popen([engine_path], creationflags=creation_flags)
        except OSError as e:
            self.logger.error(f"Error launching the engine: {e}")

    def install_version(self, version, use_mono):
        self.temp_install_dir = tempfile.mkdtemp()
        version_url = self.config.get_version_url(version)
        try:
            self.scraper.install_version(version_url, self.temp_install_dir, use_mono)
             
        except CustomException as e:
            self.logger.error(e)
            
        except Exception as e:
            self.logger.error(f"Error installing version: {e}")
 
        self.cleanup_temp_dir()
        
    def cleanup_temp_dir(self):
        if self.temp_install_dir:
            try:
                shutil.rmtree(self.temp_install_dir)
                self.temp_install_dir = ""
            except OSError as e:
                self.logger.warning(f"Error cleaning up temp directory: {e}")

    def uninstall_version(self, engine_folder):
        try:
            shutil.rmtree(engine_folder)
            self.config.update_installed_versions()
        except OSError as e:
            self.logger.error(f"Error uninstalling version: {e}")

    def run(self):
        try:
            self.config.initialize()
            self.ui.initialize()
            self.ui.launch()
        except Exception as e:
            self.logger.error(f"Launcher Runtime Error: {e}")
            self.logger.info(f"Application will now close")
            sys.exit()

def create_app():
    app = App()
    return app
