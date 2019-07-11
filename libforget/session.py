from requests import Session


def make_session():
    s = requests.Session()
    s.headers.update(
        {
            "user-agent": "Forget/{version} +https://forget.codl.fr".format(
                version=version.get_versions()["version"]
            )
        }
    )
    return s
