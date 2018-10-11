#
# Copyright (C) 2018  FreeIPA Contributors see COPYING for license
#

import os
import unittest

try:
    import yaml
    NO_YAML = False
except ImportError:
    NO_YAML = True

# pylint: disable=import-error
from six.moves.urllib.error import URLError
# pylint: enable=import-error

import pytest

try:
    from selenium import webdriver
    from selenium.webdriver.common.desired_capabilities import (
        DesiredCapabilities,
    )
    from selenium.webdriver.chrome.options import Options as ChromeOptions
except ImportError:
    webdriver = None

from ipaplatform.paths import paths
from ipatests.test_webui.config import Config
import ipatests.util

DEFAULT_BROWSER = 'firefox'
DEFAULT_PORT = 4444
DEFAULT_TYPE = 'local'

ENV_MAP = {
    'MASTER': 'ipa_server',
    'ADMINID': 'ipa_admin',
    'ADMINPW': 'ipa_password',
    'DOMAIN': 'ipa_domain',
    'IPA_REALM': 'ipa_realm',
    'IPA_IP': 'ipa_ip',
    'IPA_NO_CA': 'no_ca',
    'IPA_NO_DNS': 'no_dns',
    'IPA_HAS_TRUSTS': 'has_trusts',
    'IPA_HAS_KRA': 'has_kra',
    'IPA_HOST_CSR_PATH': 'host_csr_path',
    'IPA_SERVICE_CSR_PATH': 'service_csr_path',
    'AD_DOMAIN': 'ad_domain',
    'AD_DC': 'ad_dc',
    'AD_ADMIN': 'ad_admin',
    'AD_PASSWORD': 'ad_password',
    'AD_DC_IP': 'ad_dc_ip',
    'TRUST_SECRET': 'trust_secret',
    'SEL_TYPE': 'type',
    'SEL_BROWSER': 'browser',
    'SEL_HOST': 'host',
    'FF_PROFILE': 'ff_profile',
}


@pytest.fixture(scope='session')
def config():
    """
    Load configuration

    1) From ~/.ipa/ui_test.conf
    2) From environmental variables
    """

    # load config file
    path = os.path.join(os.path.expanduser("~"), ".ipa/ui_test.conf")
    if not NO_YAML and os.path.isfile(path):
        try:
            with open(path, 'r') as conf:
                config = Config(yaml.load(conf))
        except yaml.YAMLError as e:
            raise unittest.SkipTest("Invalid Web UI config.\n%s" % e)
        except IOError as e:
            raise unittest.SkipTest(
                "Can't load Web UI test config: %s" % e
            )
    else:
        config = {}

    # override with environmental variables
    for k, v in ENV_MAP.items():
        val = os.environ.get(k)
        if val is not None:
            config[v] = val

    # apply defaults
    if 'port' not in config:
        config['port'] = DEFAULT_PORT
    if 'browser' not in config:
        config['browser'] = DEFAULT_BROWSER
    if 'type' not in config:
        config['type'] = DEFAULT_TYPE

    return config


@pytest.fixture(scope='class')
def driver(config):
    """
    Get WebDriver according to configuration
    """

    if not webdriver:
        raise unittest.SkipTest('Selenium not installed')

    browser = config["browser"]
    port = config["port"]
    driver_type = config["type"]

    options = None

    if browser == 'chromium':
        options = ChromeOptions()
        options.binary_location = paths.CHROMIUM_BROWSER

    if driver_type == 'remote':
        if 'host' not in config:
            raise unittest.SkipTest('Selenium server host not configured')
        host = config["host"]

        if browser == 'chrome':
            capabilities = DesiredCapabilities.CHROME
        elif browser == 'chromium':
            capabilities = options.to_capabilities()
        elif browser == 'ie':
            capabilities = DesiredCapabilities.INTERNETEXPLORER
        else:
            capabilities = DesiredCapabilities.FIREFOX
        try:
            driver = webdriver.Remote(
                command_executor='http://%s:%d/wd/hub' % (host, port),
                desired_capabilities=capabilities
            )
        except URLError as e:
            raise unittest.SkipTest(
                'Error connecting to selenium server: %s' % e
            )
        except RuntimeError as e:
            raise unittest.SkipTest(
                'Error while establishing webdriver: %s' % e
            )
    else:
        try:
            if browser == 'chrome' or browser == 'chromium':
                driver = webdriver.Chrome(chrome_options=options)
            elif browser == 'ie':
                driver = webdriver.Ie()
            else:
                fp = None
                if "ff_profile" in config:
                    fp = webdriver.FirefoxProfile(config["ff_profile"])
                ff_log_path = config.get("geckodriver_log_path")
                driver = webdriver.Firefox(fp, log_path=ff_log_path)
        except URLError as e:
            raise unittest.SkipTest(
                'Error connecting to selenium server: %s' % e
            )
        except RuntimeError as e:
            raise unittest.SkipTest(
                'Error while establishing webdriver: %s' % e
            )

    driver.maximize_window()

    yield driver

    driver.delete_all_cookies()
    driver.quit()


def pytest_configure(config):
    """
    :param config: pytest config object
    """
    ipatests.util.check_ipaclient_unittests(config)
    ipatests.util.check_no_ipaapi(config)
