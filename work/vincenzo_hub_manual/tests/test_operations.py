import unittest
from datetime import date

from core.operations import build_work_queue, monthly_cashflow, search_workspace


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "clients": [{"id": "c1", "name": "Comune Demo", "email": "ufficio@example.it"}],
            "projects": [{"id": "p1", "client_id": "c1", "name": "WebGIS", "status": "In corso"}],
            "tasks": [{"id": "t1", "project_id": "p1", "title": "Consegna mappa", "due_date": "2026-09-29", "status": "Da fare", "priority": "Alta"}],
            "payments": [{"id": "m1", "client_id": "c1", "project_id": "p1", "description": "Acconto", "amount": 500, "due_date": "2026-09-28", "status": "Previsto"}, {"id": "m2", "client_id": "c1", "project_id": "p1", "description": "Saldo", "amount": 700, "paid_date": "2026-09-12", "status": "Incassato"}],
            "expenses": [{"id": "e1", "project_id": "p1", "description": "Hosting", "amount": 100, "date": "2026-09-10"}],
            "appointments": [], "leads": [], "followups": [], "documents": [],
        }

    def test_search_links_to_client_and_project(self):
        results = search_workspace(self.data, "webgis")
        self.assertEqual(results[0]["kind"], "Progetto")
        self.assertIn("project=p1", results[0]["href"])

    def test_queue_prioritises_overdue_items(self):
        queue = build_work_queue(self.data, date(2026, 9, 29))
        self.assertEqual(queue[0]["state"], "Scaduto")
        self.assertEqual(queue[1]["state"], "Oggi")

    def test_monthly_cashflow(self):
        september = monthly_cashflow(self.data, 2026)[8]
        self.assertEqual(september["Entrate"], 700)
        self.assertEqual(september["Uscite"], 100)
        self.assertEqual(september["Saldo"], 600)


if __name__ == "__main__":
    unittest.main()
