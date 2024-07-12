import unittest
import requests

BASE_URL = "http://127.0.0.1:8181/api/sessions"

class TestSessionAPI(unittest.TestCase):

    def setUp(self):
        # Create a session for testing
        response = requests.post(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.session_id = response.json()['session_id']

    def tearDown(self):
        # Cleanup the session after tests
        response = requests.delete(f"{BASE_URL}/{self.session_id}")
        self.assertEqual(response.status_code, 200)

    def test_create_session(self):
        response = requests.post(BASE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn('session_id', response.json())

    def test_get_session(self):
        response = requests.get(f"{BASE_URL}/{self.session_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn('session_id', response.json())
        self.assertEqual(response.json()['session_id'], self.session_id)

    def test_update_chat_history(self):
        chat_history = [{"message": "Hello, world!"}]
        response = requests.put(f"{BASE_URL}/{self.session_id}/chat_history", json=chat_history)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Chat history updated successfully")

        response = requests.get(f"{BASE_URL}/{self.session_id}/fetch_data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["chat_history"], chat_history)

    def test_update_current_plan(self):
        current_plan = {"task": "Write unit tests"}
        response = requests.put(f"{BASE_URL}/{self.session_id}/current_plan", json=current_plan)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Current plan updated successfully")

        response = requests.get(f"{BASE_URL}/{self.session_id}/fetch_data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["current_plan"], current_plan)

    def test_update_step_codes(self):
        step_codes = {"step1": "Import libraries"}
        response = requests.put(f"{BASE_URL}/{self.session_id}/step_codes", json=step_codes)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Step codes updated successfully")

        response = requests.get(f"{BASE_URL}/{self.session_id}/fetch_data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["step_codes"], step_codes)

    def test_update_data(self):
        data = {"key": "value"}
        response = requests.put(f"{BASE_URL}/{self.session_id}/data", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Data updated successfully")

        response = requests.get(f"{BASE_URL}/{self.session_id}/fetch_data")
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
