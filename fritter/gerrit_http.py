
from collections import namedtuple
import json
import logging
import requests
from requests.auth import HTTPDigestAuth

NO_JSON = ")]}'"

PatchSet = namedtuple('PatchSet', ['project', 'branch', 'change_id', 'revision'])

class GerritHTTP(object):
    def __init__(self, root, username, http_password, verify_ssl = True):
        """Create a new wrapper around a Gerrit instance's HTTP API.

        Parameters
        ----------
        root : str
            The base url to the Gerrit instance.
        username : str
            The username to access Gerrit using.
        http_password : str
            The HTTP password for the user. Note that Gerrit uses a separate
            password for HTTP API authentication than it does for ordinary
            web based logins. The HTTP password can be found in the user's
            settings, at /gerrit/#/settings/http-password.
        verify_ssl : bool, optional
            Whether or not to verify the SSL certificate of the server.
            This is only relevant if the server is using SSL (which it
            should be), but is intended to ease development using
            self-signed certificates.
        """
        if not root.endswith('/'):
            root += '/'
        self._root = root + 'a/'
        self._credentials = HTTPDigestAuth(username, http_password)
        self._verify_ssl = verify_ssl

    def _post(self, endpoint, data):
        json_data = json.dumps(data)
        url = self._root + endpoint
        r = requests.post(url,
                          auth = self._credentials,
                          data = json_data,
                          headers = {'Content-Type': 'application/json'},
                          verify = self._verify_ssl,
                         )

        if r.status_code != 200:
            logging.error("Request to '%s' failed with status code %d, content: '%s'.",
                          endpoint, r.status_code, r.text)

        t = r.text
        if t.startswith(NO_JSON):
            t = t[len(NO_JSON):]

        returned_data = json.loads(t)
        return returned_data

    def set_review(self, patch_set, message, verified):
        """Add a review to the given patch set.

        Parameters
        ----------
        patch_set : PatchSet
            A ``PatchSet`` instance describing the patch set to review.
        message : str
            The main body of the review.
        verified : {0, -1, 1}
        """
        endpoint_tpl = "changes/{project}~{branch}~{change_id}/revisions/{revision}/review"
        endpoint = endpoint_tpl.format(**patch_set._asdict())

        valid_verified = (0, -1, 1)
        assert verified in valid_verified, "Bad value for 'verified', expecting one of {}.".format(valid_verified)

        review_data = {
            'message': message,
            'labels': {
                'Verified': verified,
            },
        }

        self._post(endpoint, review_data)
