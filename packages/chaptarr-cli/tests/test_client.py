from ghostship_chaptarr import ChaptarrClient, catalog


def test_build_operation_request_applies_path_overrides() -> None:
    client = ChaptarrClient('http://localhost', 'api-key', api_path='api', api_version='v2')
    operation = catalog.OPERATIONS_BY_COMMAND['get_api_v1_system_status']
    spec = client.build_operation_request(operation.command_name)
    assert spec.path == '/api/v2/system/status'


def test_build_operation_request_missing_param_raises() -> None:
    client = ChaptarrClient('http://localhost', 'key')
    # find operation with a path parameter
    operation = next(
        op for op in catalog.OPERATIONS if '{' in op.path and op.path_params
    )
    try:
        client.build_operation_request(operation.command_name)
    except Exception as exc:
        assert 'missing' in str(exc)
    else:
        raise AssertionError('expected missing parameter error')
