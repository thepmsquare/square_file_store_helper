# square_file_store_helper

## about

helper to access the file store layer for my personal server.

## installation

```shell
pip install square_file_store_helper
```

## usage

[reference python file](./example/example.py)

## env

- python>=3.12.0

## changelog

### v3.0.0

- remove upload_file_using_binary_io_v0 and replace it with upload_file_using_tuple_v0.
- update example.

### v2.1.2

- bugfix in upload_file_using_file_path_v0 for filename and content type.

### v2.1.1

- bump square_commons to >=2.0.0.

### v2.1.0

- use make_request_json_output from square_commons to make requests.

### v2.0.0

- add versions to api endpoints.
- standard output format.

### v1.0.1

- replace file_purpose with app_id.

### v1.0.0

- initial implementation.

## Feedback is appreciated. Thank you!
