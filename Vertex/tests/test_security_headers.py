def test_headers_de_seguridad_presentes(client):
    r = client.get('/')
    assert r.status_code == 200
    assert r.headers.get('X-Frame-Options') == 'DENY'
    assert r.headers.get('X-Content-Type-Options') == 'nosniff'
    assert r.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    assert 'Permissions-Policy' in r.headers
    csp = r.headers.get('Content-Security-Policy', '')
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_headers_de_seguridad_tambien_en_404(client):
    r = client.get('/esta-ruta-no-existe')
    assert r.status_code == 404
    assert r.headers.get('X-Frame-Options') == 'DENY'
    assert 'Content-Security-Policy' in r.headers
