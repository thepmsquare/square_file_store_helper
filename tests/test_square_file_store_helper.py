import os
import tempfile
from io import BytesIO
from unittest.mock import Mock, mock_open, patch

import pytest
import requests

from square_file_store_helper import SquareFileStoreHelper


@pytest.fixture
def helper():
    """Fixture for SquareFileStoreHelper instance"""
    return SquareFileStoreHelper(
        param_str_square_file_store_protocol="http",
        param_str_square_file_store_ip="localhost",
        param_int_square_file_store_port=10100,
    )


@pytest.fixture
def temp_dir():
    """Fixture for temporary directory"""
    temp = tempfile.mkdtemp()
    yield temp
    # Cleanup
    import shutil

    if os.path.exists(temp):
        shutil.rmtree(temp)


class TestInitialization:
    """Tests for SquareFileStoreHelper initialization"""

    def test_default_params(self):
        """Test initialization with default parameters"""
        helper = SquareFileStoreHelper()
        assert helper.global_str_square_file_store_url_base == "http://localhost:10100"

    def test_custom_params(self):
        """Test initialization with custom parameters"""
        helper = SquareFileStoreHelper(
            param_str_square_file_store_protocol="https",
            param_str_square_file_store_ip="192.168.1.100",
            param_int_square_file_store_port=8080,
        )
        assert (
            helper.global_str_square_file_store_url_base == "https://192.168.1.100:8080"
        )


class TestUploadFileUsingFilePath:
    """Tests for upload_file_using_file_path_v0 method"""

    @patch("square_file_store_helper.main.make_request")
    @patch("builtins.open", new_callable=mock_open, read_data=b"file content")
    @patch("os.path.basename")
    @patch("mimetypes.guess_type")
    def test_success(
        self, mock_guess_type, mock_basename, mock_file, mock_request, helper
    ):
        """Test successful file upload using file path"""
        mock_basename.return_value = "test.txt"
        mock_guess_type.return_value = ("text/plain", None)
        mock_request.return_value = {"status": "success", "token": "abc123"}

        result = helper.upload_file_using_file_path_v0(
            file_path="/path/to/test.txt", app_id=1, system_relative_path="uploads/docs"
        )

        assert result["status"] == "success"
        assert result["token"] == "abc123"
        mock_request.assert_called_once()

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["endpoint"] == "upload_file/v0"
        assert call_kwargs["data"]["app_id"] == 1
        assert call_kwargs["data"]["system_relative_path"] == "uploads/docs"

    @patch("square_file_store_helper.main.make_request")
    @patch("builtins.open", new_callable=mock_open, read_data=b"file content")
    @patch("os.path.basename")
    @patch("mimetypes.guess_type")
    def test_unknown_mimetype(
        self, mock_guess_type, mock_basename, mock_file, mock_request, helper
    ):
        """Test file upload with unknown MIME type defaults to application/octet-stream"""
        mock_basename.return_value = "test.unknown"
        mock_guess_type.return_value = (None, None)
        mock_request.return_value = {"status": "success"}

        result = helper.upload_file_using_file_path_v0(
            file_path="/path/to/test.unknown"
        )

        files_arg = mock_request.call_args[1]["files"]
        assert files_arg["file"][2] == "application/octet-stream"

    @patch("square_file_store_helper.main.make_request")
    @patch("builtins.open", new_callable=mock_open, read_data=b"file content")
    @patch("os.path.basename")
    @patch("mimetypes.guess_type")
    def test_default_system_path(
        self, mock_guess_type, mock_basename, mock_file, mock_request, helper
    ):
        """Test file upload uses default system_relative_path"""
        mock_basename.return_value = "test.txt"
        mock_guess_type.return_value = ("text/plain", None)
        mock_request.return_value = {"status": "success"}

        helper.upload_file_using_file_path_v0(file_path="/path/to/test.txt")

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["data"]["system_relative_path"] == "others/misc"

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_file_not_found(self, mock_file, helper):
        """Test file upload raises FileNotFoundError for non-existent file"""
        with pytest.raises(FileNotFoundError):
            helper.upload_file_using_file_path_v0(file_path="/path/to/nonexistent.txt")

    @patch("square_file_store_helper.main.make_request")
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_permission_error(self, mock_file, mock_request, helper):
        """Test file upload raises PermissionError when file is not accessible"""
        with pytest.raises(PermissionError):
            helper.upload_file_using_file_path_v0(file_path="/path/to/protected.txt")


class TestUploadFileUsingTuple:
    """Tests for upload_file_using_tuple_v0 method"""

    @patch("square_file_store_helper.main.make_request")
    def test_success(self, mock_request, helper):
        """Test successful file upload using tuple"""
        mock_request.return_value = {"status": "success", "token": "xyz789"}

        file_tuple = ("test.pdf", BytesIO(b"PDF content"), "application/pdf")
        result = helper.upload_file_using_tuple_v0(
            file=file_tuple, app_id=2, system_relative_path="uploads/pdfs"
        )

        assert result["status"] == "success"
        assert result["token"] == "xyz789"

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["data"]["app_id"] == 2
        assert call_kwargs["files"]["file"] == file_tuple

    @patch("square_file_store_helper.main.make_request")
    def test_with_defaults(self, mock_request, helper):
        """Test file upload using tuple with default parameters"""
        mock_request.return_value = {"status": "success"}

        file_tuple = ("test.jpg", BytesIO(b"image content"), "image/jpeg")
        helper.upload_file_using_tuple_v0(file=file_tuple)

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["data"]["app_id"] is None
        assert call_kwargs["data"]["system_relative_path"] == "others/misc"

    @patch("square_file_store_helper.main.make_request")
    def test_various_file_types(self, mock_request, helper):
        """Test uploading different file types"""
        test_cases = [
            ("document.pdf", b"PDF", "application/pdf"),
            ("image.png", b"PNG", "image/png"),
            ("data.json", b"{}", "application/json"),
            ("style.css", b"body{}", "text/css"),
        ]

        for filename, content, mimetype in test_cases:
            mock_request.return_value = {"status": "success"}
            file_tuple = (filename, BytesIO(content), mimetype)
            result = helper.upload_file_using_tuple_v0(file=file_tuple)
            assert result["status"] == "success"


class TestDownloadFile:
    """Tests for download_file_v0 method"""

    @patch("square_file_store_helper.main.parse_it")
    @patch("square_file_store_helper.main.make_request")
    @patch("os.path.exists", return_value=False)
    @patch("os.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_success_with_filename(
        self, mock_file, mock_mkdir, mock_exists, mock_get, mock_parse, helper
    ):
        """Test successful file download with filename in headers"""
        # Create a proper response mock
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.content = b"downloaded content"
        mock_get.return_value = mock_response

        # Mock parse_it to return headers structure
        mock_headers = Mock()
        mock_content_disposition = Mock()
        mock_content_disposition.has.side_effect = lambda x: x == "filename"
        mock_content_disposition.__getitem__ = Mock(return_value="downloaded.txt")
        mock_headers.content_disposition = mock_content_disposition
        mock_parse.return_value = mock_headers

        result = helper.download_file_v0(
            file_storage_token="token123", output_folder_path="/tmp/downloads"
        )

        assert result == f"/tmp/downloads{os.sep}downloaded.txt"
        mock_mkdir.assert_called_once_with("/tmp/downloads")
        mock_file().write.assert_called_once_with(b"downloaded content")
        mock_get.assert_called_once()

    @patch("square_file_store_helper.main.parse_it")
    @patch("square_file_store_helper.main.make_request")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_success_with_filename_star(
        self, mock_file, mock_exists, mock_get, mock_parse, helper
    ):
        """Test successful file download with filename* (RFC 5987 encoded)"""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.content = b"downloaded content"
        mock_get.return_value = mock_response

        # Mock parse_it to return headers structure for filename*
        mock_headers = Mock()
        mock_content_disposition = Mock()
        mock_content_disposition.has.side_effect = lambda x: x == "filename*"
        mock_content_disposition.__getitem__ = Mock(
            return_value="UTF-8''test%20file.pdf"
        )
        mock_headers.content_disposition = mock_content_disposition
        mock_parse.return_value = mock_headers

        result = helper.download_file_v0(
            file_storage_token="token456", output_folder_path="/tmp/downloads"
        )

        assert result == f"/tmp/downloads{os.sep}test file.pdf"

    @patch("square_file_store_helper.main.parse_it")
    @patch("square_file_store_helper.main.make_request")
    @patch("os.path.exists", return_value=True)
    @patch("os.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_folder_already_exists(
        self, mock_file, mock_mkdir, mock_exists, mock_get, mock_parse, helper
    ):
        """Test download when output folder already exists"""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.content = b"content"
        mock_get.return_value = mock_response

        # Mock parse_it to return headers structure
        mock_headers = Mock()
        mock_content_disposition = Mock()
        mock_content_disposition.has.side_effect = lambda x: x == "filename"
        mock_content_disposition.__getitem__ = Mock(return_value="file.txt")
        mock_headers.content_disposition = mock_content_disposition
        mock_parse.return_value = mock_headers

        helper.download_file_v0("token", "/existing/folder")

        # mkdir should not be called since folder exists
        mock_mkdir.assert_not_called()

    @patch("square_file_store_helper.main.parse_it")
    @patch("square_file_store_helper.main.make_request")
    @patch("os.path.exists", return_value=False)
    @patch("os.mkdir")
    def test_missing_filename(
        self, mock_mkdir, mock_exists, mock_get, mock_parse, helper
    ):
        """Test file download raises exception when filename is missing"""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Mock parse_it to return headers without filename
        mock_headers = Mock()
        mock_content_disposition = Mock()
        mock_content_disposition.has.return_value = False
        mock_headers.content_disposition = mock_content_disposition
        mock_parse.return_value = mock_headers

        with pytest.raises(Exception) as exc_info:
            helper.download_file_v0(
                file_storage_token="token789", output_folder_path="/tmp/downloads"
            )

        assert "unable to download file" in str(exc_info.value)

    @patch("square_file_store_helper.main.make_request")
    def test_http_404_error(self, mock_get, helper):
        """Test file download with 404 error"""
        mock_get.side_effect = requests.HTTPError("Not Found")

        with pytest.raises(requests.HTTPError):
            helper.download_file_v0(
                file_storage_token="invalid_token", output_folder_path="/tmp/downloads"
            )

    @pytest.mark.parametrize(
        "status_code,error",
        [
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (500, "Internal Server Error"),
            (503, "Service Unavailable"),
        ],
    )
    @patch("square_file_store_helper.main.make_request")
    def test_various_http_errors(self, mock_get, status_code, error, helper):
        mock_get.side_effect = requests.HTTPError(error)

        with pytest.raises(requests.HTTPError):
            helper.download_file_v0("token", "/tmp")


class TestDeleteFile:
    """Tests for delete_file_v0 method"""

    @patch("square_file_store_helper.main.make_request")
    def test_single_file(self, mock_request, helper):
        """Test deleting a single file"""
        mock_request.return_value = {"status": "deleted", "count": 1}

        result = helper.delete_file_v0(list_file_storage_token=["token123"])

        assert result["status"] == "deleted"
        assert result["count"] == 1

        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["method"] == "DELETE"
        assert call_kwargs["endpoint"] == "delete_files/v0"
        assert call_kwargs["params"]["file_storage_tokens"] == ["token123"]

    @patch("square_file_store_helper.main.make_request")
    def test_multiple_files(self, mock_request, helper):
        """Test deleting multiple files"""
        mock_request.return_value = {"status": "deleted", "count": 3}

        tokens = ["token1", "token2", "token3"]
        result = helper.delete_file_v0(list_file_storage_token=tokens)

        assert result["count"] == 3
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["params"]["file_storage_tokens"] == tokens

    @patch("square_file_store_helper.main.make_request")
    def test_empty_list(self, mock_request, helper):
        """Test deleting with empty token list"""
        mock_request.return_value = {"status": "no files deleted", "count": 0}

        result = helper.delete_file_v0(list_file_storage_token=[])

        assert result["count"] == 0

    @pytest.mark.parametrize("token_count", [1, 5, 10, 50])
    @patch("square_file_store_helper.main.make_request")
    def test_various_token_counts(self, mock_request, token_count, helper):
        """Test deleting various numbers of files"""
        tokens = [f"token{i}" for i in range(token_count)]
        mock_request.return_value = {"status": "deleted", "count": token_count}

        result = helper.delete_file_v0(list_file_storage_token=tokens)

        assert result["count"] == token_count


class TestIntegration:
    """Integration tests with real file system operations"""

    @patch("square_file_store_helper.main.make_request")
    def test_upload_real_file(self, mock_request, helper, temp_dir):
        """Integration test: Upload a real temporary file"""
        mock_request.return_value = {"status": "success", "token": "real_token"}

        test_file_path = os.path.join(temp_dir, "test_upload.txt")
        with open(test_file_path, "w") as f:
            f.write("Test content for upload")

        result = helper.upload_file_using_file_path_v0(
            file_path=test_file_path, app_id=100
        )

        assert result["status"] == "success"
        assert result["token"] == "real_token"
        mock_request.assert_called_once()

    @patch("square_file_store_helper.main.make_request")
    def test_upload_binary_file(self, mock_request, helper, temp_dir):
        """Integration test: Upload a binary file"""
        mock_request.return_value = {"status": "success", "token": "binary_token"}

        test_file_path = os.path.join(temp_dir, "test.bin")
        with open(test_file_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")

        result = helper.upload_file_using_file_path_v0(file_path=test_file_path)

        assert result["status"] == "success"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "integration: mark test as integration test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
