import brotli

def compress_response(response):
    if response.is_streamed:
        return response
    mode = brotli.MODE_GENERIC
    if response.headers.get('content-type', '').startswith('text/'):
        mode = brotli.MODE_TEXT
    response.set_data(brotli.compress(response.get_data(), mode=mode))
    response.headers.set('content-encoding', 'br')
    response.headers.set('vary', 'content-encoding')
    return response
