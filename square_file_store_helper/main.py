import os
import urllib.parse
from typing import BinaryIO

import requests
from kiss_headers import parse_it


class SquareFileStoreHelper:
    def __init__(
        self,
        param_str_square_file_store_protocol: str = "http",
        param_str_square_file_store_ip: str = "localhost",
        param_int_square_file_store_port: int = 10100,
    ):
        try:
            self.global_str_square_file_store_url_base = (
                f"{param_str_square_file_store_protocol}://"
                f"{param_str_square_file_store_ip}:{param_int_square_file_store_port}"
            )
        except Exception:
            raise

    def upload_file_using_file_path_v0(
        self,
        file_path: str,
        app_id: int | None = None,
        system_relative_path: str = "others/misc",
    ):
        try:
            endpoint = "upload_file/v0"
            payload = {
                "app_id": app_id,
                "system_relative_path": system_relative_path,
            }
            with open(file_path, "rb") as file:
                files = {"file": (file_path, file, "multipart/form-data")}
                response = requests.post(
                    self.global_str_square_file_store_url_base + "/" + endpoint,
                    files=files,
                    data=payload,
                )
                if response.status_code == 201:
                    return response.json()
                else:
                    response.raise_for_status()
        except Exception:
            raise

    def upload_file_using_binary_io_v0(
        self,
        file: BinaryIO,
        app_id: int | None = None,
        system_relative_path: str = "others/misc",
    ):
        try:
            endpoint = "upload_file/v0"
            payload = {
                "app_id": app_id,
                "system_relative_path": system_relative_path,
            }

            files = {"file": (file.name, file, "multipart/form-data")}
            response = requests.post(
                self.global_str_square_file_store_url_base + "/" + endpoint,
                files=files,
                data=payload,
            )

            if response.status_code == 201:
                return response.json()
            else:
                response.raise_for_status()

        except Exception:
            raise

    def download_file_v0(self, file_storage_token: str, output_folder_path: str) -> str:
        """
        :param file_storage_token:
        :param output_folder_path:
        :return: filepath
        """
        try:
            endpoint = "download_file/v0"
            payload = {
                "file_storage_token": file_storage_token,
            }

            response = requests.get(
                self.global_str_square_file_store_url_base + "/" + endpoint,
                params=payload,
            )
            if response.status_code == 200:
                if not os.path.exists(output_folder_path):
                    os.mkdir(output_folder_path)

                headers = parse_it(response)
                if headers.content_disposition.has("filename*"):
                    file_name = urllib.parse.unquote(
                        headers.content_disposition["filename*"][7:]
                    )
                elif headers.content_disposition.has("filename"):
                    file_name = headers.content_disposition["filename"]
                else:
                    raise Exception(
                        f"unable to download file - not able to get file name. headers: {headers}",
                    )

                downloaded_file_path = output_folder_path + os.sep + file_name
                with open(downloaded_file_path, "wb") as file:
                    file.write(response.content)

                return downloaded_file_path
            else:
                response.raise_for_status()
        except Exception:
            raise

    def delete_file_v0(self, list_file_storage_token: list) -> str:
        """
        :param list_file_storage_token:
        :return: filepath
        """
        try:
            endpoint = "delete_files/v0"
            params = {
                "file_storage_tokens": list_file_storage_token,
            }

            response = requests.delete(
                self.global_str_square_file_store_url_base + "/" + endpoint,
                params=params,
            )
            if response.status_code == 200:
                return response.json()
            else:
                response.raise_for_status()
        except Exception:
            raise
