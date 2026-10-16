import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import app

class FeedbackTests(unittest.TestCase):
    def test_valid_without_email(self):
        x = dict(settore="commercio", frequenza="mensile", utilita="molto", prezzo="forse", ricontatto=False)
        self.assertEqual(app.validate(x)[-2:], (None, 0))

    def test_email_requires_consent(self):
        x = dict(settore="commercio", frequenza="mensile", utilita="molto", prezzo="forse", email="a@example.com", ricontatto=False)
        with self.assertRaises(ValueError):
            app.validate(x)

    def test_sqlite_and_purge(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(app, "DB_PATH", Path(d) / "feedback.sqlite3"):
                with app.connect() as conn:
                    conn.execute("INSERT INTO feedback (created_at,settore,frequenza,utilita,prezzo,ricontatto) VALUES ('2020-01-01T00:00:00+00:00','commercio','mensile','molto','si',0)")
                    app.purge(conn)
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0], 0)

if __name__ == "__main__":
    unittest.main()
