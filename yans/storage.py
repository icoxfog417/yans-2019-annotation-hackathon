import os
import re
from urllib.parse import urlparse
from tqdm import tqdm
import zipfile
import tarfile
import gzip
import requests


class Storage():

    def __init__(self, root=""):
        self.root = root
        if not root:
            self.root = os.path.join(os.path.dirname(__file__), "../data")

    def path(self, directory):
        return os.path.join(self.root, directory)

    def download(self, url, path=""):
        _path = os.path.join(self.root, path)
        if not os.path.exists(_path):
            raise Exception(f"{_path} does not exist.")

        resp = requests.get(url, stream=True)
        if not resp.ok:
            raise Exception(f"Can not access {url}.")

        # save content in response to file
        total_size = int(resp.headers.get("content-length", 0))
        file_name = self._get_file_name(url, resp)
        save_file_path = os.path.abspath(os.path.join(_path, file_name))
        with open(save_file_path, "wb") as f:
            chunk_size = 1024
            limit = total_size / chunk_size
            for data in tqdm(resp.iter_content(chunk_size=chunk_size),
                             total=limit, unit="B", unit_scale=True):
                f.write(data)

        return save_file_path

    def _get_file_name(self, url, resp):
        file_name = ""
        if resp and "content-disposition" in resp.headers:
            cd = resp.headers["content-disposition"]
            file_matches = re.search("filename=(.+)", cd)
            if file_matches:
                file_name = file_matches.group(0)
                file_name = file_name.split("=")[1]
        else:
            parsed = urlparse(url)
            file_name = os.path.basename(parsed.path)

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
                t.extractall(path=target)
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
