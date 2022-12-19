import os
import re
from urllib.parse import urlparse
from tqdm import tqdm
import zipfile
import tarfile
import gzip
import requests


class Storage():

    def __init__(self, root="", force=False):
        self.root = root
        if not root:
            self.root = os.path.join(os.path.dirname(__file__), "../data")

    def path(self, directory):
        return os.path.join(self.root, directory)

    def download(self, url, directory="", file_name=""):
        _dir = os.path.join(self.root, directory)
        if not os.path.exists(_dir):
            raise Exception(f"{_dir} does not exist.")

        save_file_path = ""
        if file_name:
            save_file_path = os.path.abspath(os.path.join(_dir, file_name))
        else:
            parsed = urlparse(url)
            file_name = os.path.basename(parsed.path)
            _, ext = os.path.splitext(file_name)
            if ext:
                save_file_path = os.path.abspath(os.path.join(_dir, file_name))

        if os.path.exists(save_file_path):
            print(f"{save_file_path} already exist.")
            return save_file_path

        resp = requests.get(url, stream=True)
        if not resp.ok:
            raise Exception(f"Can not access {url}.")

        # save content in response to file
        total_size = int(resp.headers.get("content-length", 0))
        if not file_name:
            file_name = self._get_file_name_from_resp(url, resp)
            save_file_path = os.path.abspath(os.path.join(_dir, file_name))

        with open(save_file_path, "wb") as f:
            chunk_size = 1024
            limit = total_size / chunk_size
            for data in tqdm(resp.iter_content(chunk_size=chunk_size),
                             total=limit, unit="B", unit_scale=True):
                f.write(data)

        return save_file_path

    def _get_file_name_from_resp(self, url, resp):
        file_name = ""
        if resp and "content-disposition" in resp.headers:
            cd = resp.headers["content-disposition"]
            file_matches = re.search("filename=(.+)", cd)
            if file_matches:
                file_name = file_matches.group(0)
                file_name = file_name.split("=")[1]

        return file_name

    def extractall(self, path):
        target = os.path.dirname(path)
        if not os.path.exists(path):
            raise Exception(f"{path} does not exist.")

        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                extracted = z.namelist()
                z.extractall(path=target)
                target = os.path.join(target, extracted[0])
        elif tarfile.is_tarfile(path):
            with tarfile.open(path) as t:
                extracted = t.getnames()
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(t, path=target)
                target = os.path.join(target, extracted[0])
        elif path.endswith(".gz"):
            with gzip.open(path, "rb") as g:
                file_name = os.path.basename(path)
                file_base, _ = os.path.splitext(file_name)
                p = os.path.join(target, file_base)
                with open(p, "wb") as f:
                    for ln in g:
                        f.write(ln)

        os.remove(path)

        return target
