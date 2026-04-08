from ghostship_chaptarr import catalog


def test_operations_are_unique() -> None:
    commands = [op.command_name for op in catalog.OPERATIONS]
    assert len(commands) == len(set(commands))


def test_system_status_command_exists() -> None:
    operation = catalog.OPERATIONS_BY_COMMAND.get('get_api_v1_system_status')
    assert operation is not None
    assert operation.path == '/api/v1/system/status'
