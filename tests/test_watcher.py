import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from watcher.watcher import app, check_account_states, watched_accounts, last_states

class WatcherTestCase(unittest.TestCase):
    
    def setUp(self):
        # Set up the test client
        self.app = app.test_client()
        self.app.testing = True
    
    def test_watch_account(self):
        # Test the /watch endpoint
        response = self.app.post('/watch', json={'address': 'test-address'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('test-address', watched_accounts)
    
    @patch('watcher.watcher.algod_client')
    def test_list_accounts(self, mock_algod_client):
        # Mock account_info to return a test account
        mock_algod_client.account_info.return_value = {
            'amount': 1000,
            'pending-rewards': 10,
            'status': 'Online',
            'total-apps-opted-in': 2,
            'total-assets-opted-in': 3,
            'min-balance': 100,
            'rewards': 5
        }
        
        # Add test address to watched accounts
        watched_accounts['test-address'] = True
        
        # Test the /accounts endpoint
        response = self.app.get('/accounts')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['amount'], 1000)
    
    @patch('watcher.watcher.algod_client')
    def test_check_account_states(self, mock_algod_client):
        # Mock account_info to return a test account
        mock_algod_client.account_info.return_value = {
            'amount': 1000,
            'pending-rewards': 10,
            'status': 'Online',
            'total-apps-opted-in': 2,
            'total-assets-opted-in': 3,
            'min-balance': 100,
            'rewards': 5
        }
        
        # Add test address to watched accounts
        watched_accounts['test-address'] = True
        
        # Run the check_account_states function once
        with patch('time.sleep', return_value=None):
            check_account_states(run_once=True)
        
        # Verify that the state was updated
        self.assertIn('test-address', last_states)
        self.assertEqual(last_states['test-address']['amount'], 1000)

if __name__ == '__main__':
    unittest.main()
