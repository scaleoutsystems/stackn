import os
from unittest import TestCase, mock, skip

import stackn.auth as auth


class CLIAuthTests(TestCase):

    @mock.patch.dict(os.environ, {
        "STACKN_CONFIG_PATH": os.getcwd(), 
        "STACKN_CONFIG_FILE": "test_config.json"
        })
    def test_get_stackn_config_path(self):
        config_path = auth._get_stackn_config_path()
        self.assertEqual(config_path, os.getcwd()+"/test_config.json")

    
    @mock.patch.dict(os.environ, {
        "STACKN_CONFIG_PATH": os.getcwd(), 
        "STACKN_CONFIG_FILE": "test_config.json"
        })
    def test_load_config_file_full(self):
        config_full = auth._load_config_file_full({})
        expected_config = {
                "http://studio.test.domain": {
                    "STACKN_URL": "test_url",
                    "STACKN_PROJECT": "test_project",
                    "STACKN_ACCESS_TOKEN": "test_token",
                    "STACKN_USER": "test_user"
                    },
                "studio._test.domain": {
                    "STACKN_URL": "_test_url",
                    "STACKN_PROJECT": "_test_project",
                    "STACKN_ACCESS_TOKEN": "_test_token",
                    "STACKN_USER": "_test_user"
                },
                "current": {
                    "STACKN_URL": "",
                    "STACKN_PROJECT": "",
                    "STACKN_SECURE": ""
                    }
                }
        
        self.assertEqual(config_full, expected_config)

        

    
    @mock.patch.dict(os.environ, {"STACKN_CONFIG_PATH": os.getcwd(), 
                                 'STACKN_CONFIG_FILE': 'test_config.json'
                                 })
    def test_load_config_file_url_with_scheme(self):
        stackn_url = {'STACKN_URL': 'http://studio.test.domain'}
        config_for_url = auth._load_config_file_url(stackn_url)
        expected_config = {
            "STACKN_URL": "test_url",
            "STACKN_PROJECT": "test_project",
            "STACKN_ACCESS_TOKEN": "test_token",
            "STACKN_USER": "test_user"
            }
        
        self.assertEqual(config_for_url, expected_config)
    
    @mock.patch.dict(os.environ, {
        "STACKN_CONFIG_PATH": os.getcwd(), 
        "STACKN_CONFIG_FILE": "test_config.json"
        })
    def test_load_config_file_url_without_scheme(self):
        stackn_url = {'STACKN_URL': 'http://studio._test.domain'}
        config_for_url = auth._load_config_file_url(stackn_url)
        expected_config = {
            "STACKN_URL": "_test_url",
            "STACKN_PROJECT": "_test_project",
            "STACKN_ACCESS_TOKEN": "_test_token",
            "STACKN_USER": "_test_user"
            }
        
        self.assertEqual(config_for_url, expected_config)