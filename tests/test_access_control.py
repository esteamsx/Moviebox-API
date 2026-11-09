import os
import unittest

# These tests use a disposable key and never start the application lifespan.
os.environ["API_ACCESS_KEY"] = "unit-test-moviebox-key"
os.environ["CATALOG_DB"] = "/tmp/moviebox-api-auth-tests.db"

from fastapi.testclient import TestClient
from main import app


class ApiAccessControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_dashboard_and_frontend_remain_public(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/app").status_code, 200)

    def test_protected_endpoint_rejects_missing_and_invalid_keys(self):
        self.assertEqual(self.client.get("/providers").status_code, 401)
        invalid = self.client.get("/providers", headers={"Authorization": "Bearer wrong-test-key"})
        self.assertEqual(invalid.status_code, 401)

    def test_protected_endpoint_accepts_disposable_test_key(self):
        response = self.client.get("/providers", headers={"Authorization": "Bearer unit-test-moviebox-key"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("providers", response.json())

    def test_preflight_does_not_require_the_shared_key(self):
        response = self.client.options(
            "/providers",
            headers={
                "Origin": "https://esteamstv.devs.surf",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "https://esteamstv.devs.surf")


if __name__ == "__main__":
    unittest.main()
