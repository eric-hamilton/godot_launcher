import os   
import sys
from datetime import datetime
from configparser import ConfigParser
from godot_launcher import utils
from godot_launcher.exceptions import *

class Config():
    def __init__(self, app):
        self.app = app
        self.time_format = "%Y-%m-%d_%H-%M-%S"
        self.cfg = ConfigParser()
        self.app_dir, self.config_file = self.get_app_dir()
        self.logfile = os.path.join(self.app_dir, "launcher.log")

    def initialize(self):
        if not os.path.exists(self.config_file):
            self.create_initial_config()
            self.app.logger.info("Config file created successfully")
        else:
            self.cfg.read(self.config_file)
            last_ran = self.cfg["Config"]["last_run"]
            now = datetime.now().strftime(self.time_format)
            self.cfg["Config"]["last_run"] = now
            last_versions = self.cfg["AvailableVersions"]
            
            """
            Only pull new releases if more than a day has passed since last pull
            or the initial 'AvailableVersions' config was blank, indicating it failed
            when running for the first time
            """
            
            scanned_this_init = False                       
            if utils.time_diff_greater_than(last_ran, now, 1):
                scanned_this_init = True
                available_versions = {}
                try:
                    available_versions = self.app.scraper.get_release_versions()
                except APIError as e:
                    self.app.logger.error(e)
                
                if available_versions:
                    self.cfg["AvailableVersions"] = available_versions
                
            
            if not last_versions and not scanned_this_init:
                
                available_versions = {}
                try:
                    available_versions = self.app.scraper.get_release_versions()
                except APIError as e:
                    self.app.logger.error(e)
                
                if available_versions:
                    self.cfg["AvailableVersions"] = available_versions

        self.save_config()
        self.app.logger.info("Config file read successfully")

    def create_initial_config(self):
        """ Runs when no `config.ini` file is found"""
        installed, latest = self.import_installed_versions()
        
        available_versions = {}
        try:
            available_versions = self.app.scraper.get_release_versions()
        except APIError as e:
            self.app.logger.error(e)
            
        
        self.cfg["InstalledVersions"] = installed
        self.cfg["AvailableVersions"] = available_versions
        self.cfg["Config"] = {
            "last_run":datetime.now().strftime(self.time_format),
            "selected_version":"",
            "latest_installed_version":latest
        }
        if latest:
            self.cfg["Config"]["selected_version"] = latest
        
        self.save_config()
    
    def get_installed_versions(self):
        return [name for name, _ in self.cfg["InstalledVersions"].items()]
    
    def get_available_versions(self):        
        return [name for name, _ in self.cfg["AvailableVersions"].items()]
        
    def get_selected_version(self):
        return self.cfg["Config"]["selected_version"]
    
    def get_version_url(self, version):
        return self.cfg["AvailableVersions"][version]
        
    def get_engine_folder_from_url(self, version_url, use_mono=False):        
        base_dir = "versions"
        if use_mono:
            base_dir = "mono"
            
        for key, val in self.cfg["AvailableVersions"].items():
            if val == version_url:
                engine_folder = os.path.join(self.app_dir, base_dir, key)
                return engine_folder
                
    def get_engine_version_path(self, version):
        return self.cfg["InstalledVersions"][version]
    
    def update_installed_versions(self):
        installed, latest = self.import_installed_versions()
        self.cfg["InstalledVersions"] = installed
        self.cfg["Config"]["latest_installed_version"] = latest
        self.cfg["Config"]["selected_version"] = latest
        
        self.save_config()
        
    def import_installed_versions(self):
        installed_versions = {}
        versions_dir = os.path.join(self.app_dir, "versions")
        mono_dir = os.path.join(self.app_dir, "mono")
        for version_path in os.scandir(versions_dir):
            if version_path.is_dir():
                installed_versions[version_path.name] = version_path.path
        
        for mono_version_path in os.scandir(mono_dir):
            if mono_version_path.is_dir():
                installed_versions[f"{mono_version_path.name} (mono)"] = mono_version_path.path
        
        latest = utils.get_latest_version(installed_versions.keys())
        return installed_versions, latest
        
    def get_app_dir(self):
        appdata_dir = os.getenv('APPDATA')
        app_dir = os.path.join(appdata_dir, "godot_launcher")
        version_dir = os.path.join(app_dir, "versions")
        mono_dir = os.path.join(app_dir, "mono")
        config_file = os.path.join(app_dir, "config.ini")
        
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        if not os.path.exists(version_dir):
            os.makedirs(version_dir)        
        if not os.path.exists(mono_dir):
            os.makedirs(mono_dir)

        return app_dir, config_file
    
    def version_is_installed(self, version):
        if version in [name for name, _ in self.cfg["InstalledVersions"].items()]:
            return True
        else:
            return False
    
    def set_selected_version(self, version):
        self.cfg["Config"]["selected_version"] = version
        self.save_config()
    
    def get_installed_version_path(version):
        return self.cfg["InstalledVersions"][version]
        
    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.cfg.write(configfile)
        self.app.logger.info("Config saved successfully")
            
    

        