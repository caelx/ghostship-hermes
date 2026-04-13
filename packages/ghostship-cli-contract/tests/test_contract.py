from __future__ import annotations

import base64
from pathlib import Path

import httpx

from ghostship_cli_contract import BaseHttpClient, decode_response, parse_file_params, write_response_output


def test_parse_file_params_serializes_real_file(tmp_path: Path) -> None:
    payload_path = tmp_path / 'example.txt'
    payload_path.write_text('hello')

    payload = parse_file_params([f'file={payload_path}'])

    assert payload['file'][0] == 'example.txt'
    assert payload['file'][1] == b'hello'
    assert payload['file'][2] == 'text/plain'


def test_decode_response_handles_text_and_binary() -> None:
    text_response = httpx.Response(200, text='hello', headers={'content-type': 'text/plain'})
    assert decode_response(text_response) == {'content_type': 'text/plain', 'body': 'hello'}

    binary_response = httpx.Response(200, content=b'png', headers={'content-type': 'image/png'})
    assert decode_response(binary_response) == {
        'content_type': 'image/png',
        'encoding': 'base64',
        'body_base64': base64.b64encode(b'png').decode('ascii'),
    }


def test_request_decoded_uses_additive_non_json_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text='openapi: 3.1.0', headers={'content-type': 'application/yaml'})

    client = BaseHttpClient('https://example.test', transport=httpx.MockTransport(handler))
    payload = client.request_decoded('GET', '/docs')

    assert payload == {'content_type': 'application/yaml', 'body': 'openapi: 3.1.0'}


def test_write_response_output_persists_content(tmp_path: Path) -> None:
    request = httpx.Request('GET', 'https://example.test/export')
    response = httpx.Response(200, request=request, content=b'book', headers={'content-type': 'application/zip'})

    result = write_response_output(response, tmp_path / 'book.zip')

    assert (tmp_path / 'book.zip').read_bytes() == b'book'
    assert result['bytes_written'] == 4
    assert result['content_type'] == 'application/zip'
