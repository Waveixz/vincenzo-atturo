from datetime import date, timedelta

from core.ui import euro, parse_date


def _contains(record: dict, fields: tuple[str, ...], needle: str) -> bool:
    return any(needle in str(record.get(field, "")).casefold() for field in fields)


def search_workspace(data: dict, query: str, limit: int = 12) -> list[dict]:
    """Return navigable matches from the operational collections."""
    needle = query.strip().casefold()
    if len(needle) < 2:
        return []

    results = []
    clients = {item.get("id"): item for item in data.get("clients", [])}
    projects = {item.get("id"): item for item in data.get("projects", [])}

    for item in data.get("clients", []):
        if _contains(item, ("name", "contact", "contact_person", "email", "phone", "vat_code", "notes"), needle):
            results.append({
                "kind": "Cliente",
                "title": item.get("name", "Cliente"),
                "meta": " · ".join(value for value in (item.get("contact") or item.get("contact_person", ""), item.get("email", "")) if value),
                "href": f"?module=clienti_progetti&client={item.get('id', '')}",
            })

    for item in data.get("projects", []):
        if _contains(item, ("name", "status", "owner", "notes"), needle):
            client = clients.get(item.get("client_id"), {})
            results.append({
                "kind": "Progetto",
                "title": item.get("name", "Progetto"),
                "meta": " · ".join(value for value in (client.get("name", ""), item.get("status", "")) if value),
                "href": f"?module=clienti_progetti&client={item.get('client_id', '')}&project={item.get('id', '')}",
            })

    for item in data.get("leads", []):
        if _contains(item, ("name", "company", "email", "phone", "service", "next_action", "notes"), needle):
            results.append({
                "kind": "Opportunità",
                "title": item.get("company") or item.get("name") or "Opportunità",
                "meta": " · ".join(value for value in (item.get("stage", ""), item.get("service", "")) if value),
                "href": "?module=clienti_progetti&section=crm",
            })

    for item in data.get("documents", []):
        if _contains(item, ("title", "category", "context", "notes", "path"), needle):
            results.append({
                "kind": "Documento",
                "title": item.get("title", "Documento"),
                "meta": " · ".join(value for value in (item.get("category", ""), item.get("context", "")) if value),
                "href": "?module=documenti",
            })

    return results[:limit]


def build_work_queue(data: dict, today: date | None = None) -> list[dict]:
    """Build a single priority-ordered queue from agenda, tasks, cashflow and CRM."""
    today = today or date.today()
    horizon = today + timedelta(days=14)
    clients = {item.get("id"): item for item in data.get("clients", [])}
    projects = {item.get("id"): item for item in data.get("projects", [])}
    queue = []

    def add(kind, title, due, client_id="", project_id="", meta="", priority=2, href=""):
        day = parse_date(due)
        if not day or day > horizon:
            return
        if not href:
            href = "?module=clienti_progetti"
            if client_id:
                href += f"&client={client_id}"
            if project_id:
                href += f"&project={project_id}"
        context = " · ".join(
            value for value in (
                clients.get(client_id, {}).get("name", ""),
                projects.get(project_id, {}).get("name", ""),
                meta,
            ) if value
        )
        queue.append({
            "kind": kind,
            "title": title,
            "date": day,
            "context": context,
            "href": href,
            "priority": 0 if day < today else 1 if day == today else priority,
            "state": "Scaduto" if day < today else "Oggi" if day == today else "In arrivo",
        })

    for item in data.get("payments", []):
        if item.get("status", "Previsto") == "Previsto":
            add("Incasso", item.get("description", "Pagamento"), item.get("due_date"), item.get("client_id", ""), item.get("project_id", ""), euro(item.get("amount")))

    for item in data.get("tasks", []):
        if item.get("status") != "Completata":
            project = projects.get(item.get("project_id"), {})
            add("Attività", item.get("title", "Attività"), item.get("due_date"), project.get("client_id", ""), item.get("project_id", ""), item.get("priority", ""))

    for item in data.get("appointments", []):
        if item.get("status") != "Annullato":
            add("Appuntamento", item.get("title", "Appuntamento"), item.get("date"), item.get("client_id", ""), item.get("project_id", ""), item.get("start_time", ""), priority=3, href=f"?module=agenda&agenda_date={item.get('date', '')}&agenda_view=Giorno")

    leads = {item.get("id"): item for item in data.get("leads", [])}
    for item in data.get("followups", []):
        if item.get("status", "Da fare") != "Completato":
            lead = leads.get(item.get("lead_id"), {})
            add("Follow-up", item.get("text", "Follow-up commerciale"), item.get("date"), meta=lead.get("company") or lead.get("name", ""), href="?module=clienti_progetti&section=crm")

    return sorted(queue, key=lambda item: (item["priority"], item["date"], item["kind"], item["title"].casefold()))


def monthly_cashflow(data: dict, year: int) -> list[dict]:
    months = [{"Mese": month, "Entrate": 0.0, "Uscite": 0.0, "Saldo": 0.0} for month in range(1, 13)]
    for item in data.get("payments", []):
        if item.get("status") != "Incassato":
            continue
        day = parse_date(item.get("paid_date") or item.get("due_date"))
        if day and day.year == year:
            months[day.month - 1]["Entrate"] += float(item.get("amount") or 0)
    for item in data.get("expenses", []):
        day = parse_date(item.get("date"))
        if day and day.year == year:
            months[day.month - 1]["Uscite"] += float(item.get("amount") or 0)
    for row in months:
        row["Saldo"] = row["Entrate"] - row["Uscite"]
    return months
