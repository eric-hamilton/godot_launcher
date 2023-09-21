import requests
from godot_launcher import utils
from godot_launcher.exceptions import *
import os
import urllib.request


class Scraper:
    def __init__(self, app):
        self.app = app
        
    def get_release_versions(self):
        """Pull available releases from Godot repo.

        Returns:
            Returns a dict of version names and their url.
        """
        versions = {}
        url = 'https://api.github.com/repos/godotengine/godot/releases'
        try:
            response = requests.get(url)
            response.raise_for_status()
            releases = response.json()
            for release in releases:                
                versions[release["name"]] = release["url"]
            return versions
        except requests.RequestException as e:
            raise APIError(f"Error retrieving release versions: {e}")
            
    def install_version(self, version_url, temp_dir, use_mono):
        """Download and install a version of Godot.

        Zip file is downloaded and unzipped to "versions" folder.

        Args:
            version_url: Godot repo release url.
            temp_dir: Path to temporary folder where zip file will be downloaded to.
            use_mono: Boolean to download with c# compatibility or not.
        """
        
        response = requests.get(version_url)
        if response.status_code != 200:
            raise DownloadError(f"Could not retrieve assets from {version_url}")
        else:
            data = response.json()
            asset_data = {}            
            for asset in data["assets"]:
                asset_data[asset["name"]] = asset["browser_download_url"]                
            
            download_url = utils.get_download_url_for_platform(asset_data, use_mono)
 
            if download_url:
                _, file_extension = os.path.splitext(download_url)
                temp_file = os.path.join(temp_dir, f"{utils.generate_hex(8)}{file_extension}")
                try:
                    utils.download_file_with_progress(download_url, temp_file)
                except Exception as e:
                    raise DownloadError(f"Error downloading file: {e}")
                
                engine_folder = self.app.config.get_engine_folder_from_url(version_url, use_mono)
                try:
                    utils.unzip_file_with_progress(temp_file, engine_folder)
                except Exception as e:
                    raise UnzipError(f"Error unzipping file: {e}")
                    
                self.app.config.update_installed_versions()
            
            else:
                raise DownloadError(f"Could not find appropriate download url")

        
    