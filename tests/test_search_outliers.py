# -*- coding: utf-8 -*-
"""Test of weird search behaviours."""
import binascii


def test_unicode_post_search(webapp):
    """Test POSTing Unicode will fail.

    GET cannot be tested through webtest but has been tested manually to
    ensure it has the same behaviour - using url:
        http://localhost:5000/search/www.example.新加坡
    """
    # TLD is Singapore/Chinese: 新加坡 OR xn--yfro4i67o
    domain = u'www.example.\u65b0\u52a0\u5761'
    response = webapp.post(
        '/search', {'domains': domain},
        content_type='application/x-www-form-urlencoded; charset=utf-8'
    )

    assert response.status_code == 302
    assert response.headers['location'] == 'http://localhost:80/error/3'


def test_no_domains_key(webapp):
    """Test a POST without 'domains' being set fails."""
    response = webapp.post('/search')

    assert response.status_code == 302
    assert response.headers['location'] == 'http://localhost:80/error/2'


def test_empty_domains_key(webapp):
    """Test a POST with 'domains' being set to whitespace fails."""
    response = webapp.post('/search', {'domains': ' '})

    assert response.status_code == 302
    assert response.headers['location'] == 'http://localhost:80/error/2'


def test_no_valid_domains(webapp):
    """Test that submitting no valid domains fails after a GET to the
    redirect.
    """
    response = webapp.post('/search', {'domains': '...'})

    assert response.status_code == 302

    second_response = response.follow()
    assert second_response.status_code == 302
    assert second_response.headers['location'] == 'http://localhost:80/error/0'


def test_suggestion(webapp):
    """Test that submitting no valid domains fails.

    Where a domain could be reasonably suggested, it is.
    """
    response = webapp.post('/search', {'domains': 'example'}).follow()

    assert response.status_code == 302

    domain = 'example.com'
    enc_domain = binascii.hexlify(domain)
    expected_redirect = 'http://localhost:80/error/0?suggestion=' + enc_domain
    assert response.headers['location'] == expected_redirect


def test_no_valid_domains_only(webapp):
    """Test invalid domains not in suggestions."""
    query = 'abc ?@<>.'
    response = webapp.post('/search', {'domains': query}).follow()

    assert response.status_code == 302
    assert response.headers['location'].endswith('=6162632e636f6d')
    assert binascii.unhexlify('6162632e636f6d') == 'abc.com'


def test_suggestion_rendered(webapp):
    """Test suggestion rendered on index."""
    response = webapp.post('/search', {'domains': 'example'}).follow().follow()

    assert 'example.com' in response.body


def test_get_errors(webapp):
    """Test funny URLs for a GET search."""
    response = webapp.get('/search/__<<>')

    assert response.status_code == 302
    assert response.headers['location'] == 'http://localhost:80/error/0'


def test_no_suggestion_many_words(webapp):
    """Test many search terms are dropped in suggestions."""
    query = 'j s d f i j s'
    response = webapp.post('/search', {'domains': query}).follow()

    assert response.status_code == 302
    assert response.headers['location'] == 'http://localhost:80/error/0'


def test_suggestion_bad_data(webapp):
    """Test that submitting invalid data in suggestion doesn't crash the page.
    """
    response = webapp.get('/error/0?suggestion')
    assert response.status_code == 200

    response = webapp.get('/error/0?suggestion=')
    assert response.status_code == 200

    response = webapp.get('/error/0?suggestion=sdlkfjsdlfkjsdf')
    assert response.status_code == 200

    response = webapp.get('/error/0?suggestion=<script>...<?')
    assert response.status_code == 200

    response = webapp.get('/error/0?suggestion=a.com&cat=2')
    assert response.status_code == 200


def test_fix_comma_typo(webapp):
    """Test accidentally entering in a comma instead of period is corrected.
    """
    malformed_domain = 'example,com'
    expected_suggestion = 'example.com'

    response = webapp.post('/search', {'domains': malformed_domain}).follow().follow()

    assert expected_suggestion in response.body


def test_fix_slash_typo(webapp):
    """Test accidentally entering in a slash instead of period is corrected.
    """
    malformed_domain = 'example/com'
    expected_suggestion = 'example.com'

    response = webapp.post('/search', {'domains': malformed_domain}).follow().follow()

    assert expected_suggestion in response.body


def test_fix_space_typo(webapp):
    """Test accidentally entering in a space instead of period is corrected.
    """
    malformed_domain = 'example com'
    expected_suggestion = 'example.com'

    response = webapp.post('/search', {'domains': malformed_domain}).follow().follow()

    assert expected_suggestion in response.body
