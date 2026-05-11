from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_SAMPLE = ROOT / "data" / "sample" / "sample.csv"
DATA_PROCESSED = ROOT / "data" / "processed"
CHARTS = ROOT / "charts"
REPORTS = ROOT / "reports"
PROJECT = {
  "code": "R-07",
  "slug": "wifi-scan-analyzer-lab",
  "title": "Laboratorio De Analise De Redes Wi-Fi",
  "kind": "wifi_scan",
  "description": "Analisa SSID, canal, RSSI e seguranca usando amostras sinteticas seguras."
}

def ensure_dirs() -> None:
    for directory in (DATA_PROCESSED, CHARTS, REPORTS):
        directory.mkdir(parents=True, exist_ok=True)


def read_csv() -> pd.DataFrame:
    return pd.read_csv(DATA_SAMPLE)


def read_json() -> list[dict]:
    return json.loads(DATA_SAMPLE.read_text(encoding="utf-8"))


def save_df(df: pd.DataFrame, filename: str) -> str:
    ensure_dirs()
    path = DATA_PROCESSED / filename
    df.to_csv(path, index=False)
    return str(path.relative_to(ROOT))


def save_chart(filename: str) -> str:
    ensure_dirs()
    path = CHARTS / filename
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()
    return str(path.relative_to(ROOT))


def save_report(text: str, filename: str) -> str:
    ensure_dirs()
    path = REPORTS / filename
    path.write_text(text, encoding="utf-8")
    return str(path.relative_to(ROOT))


def run_faq_chatbot() -> dict:
    rules = read_json()
    prompts = ["grade do curso", "portfolio github", "wifi no laboratorio"]
    rows = []
    for prompt in prompts:
        answer = "Nenhuma resposta sintética encontrada."
        for rule in rules:
            if any(pattern in prompt for pattern in rule["patterns"]):
                answer = rule["answer"]
                break
        rows.append({"prompt": prompt, "answer": answer})
    return {"rows": len(rows), "outputs": [save_df(pd.DataFrame(rows), "faq_transcript.csv")]}


def run_iot_simulator() -> dict:
    df = read_csv()
    df["alert"] = np.where((df["temperature_c"] > 29) | (df["humidity_percent"] < 60), "revisar", "normal")
    df.plot(x="timestamp", y=["temperature_c", "humidity_percent"], marker="o", figsize=(8, 4), title="IoT sintético de sala de aula")
    plt.xticks(rotation=25, ha="right")
    return {"rows": len(df), "alerts": int((df["alert"] == "revisar").sum()), "outputs": [save_df(df, "iot_alerts.csv"), save_chart("iot_timeseries.png")]}


def run_ai_heatmap() -> dict:
    df = read_csv()
    pivot = df.pivot(index="region", columns="indicator", values="value")
    plt.figure(figsize=(7, 4))
    plt.imshow(pivot, aspect="auto")
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=20, ha="right")
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.colorbar(label="Índice sintético")
    return {"rows": len(df), "outputs": [save_df(pivot.reset_index(), "ai_use_pivot.csv"), save_chart("ai_use_heatmap.png")]}


def run_helpdesk_sla() -> dict:
    df = read_csv()
    df["opened_at"] = pd.to_datetime(df["opened_at"])
    df["closed_at"] = pd.to_datetime(df["closed_at"])
    df["hours_to_close"] = ((df["closed_at"] - df["opened_at"]).dt.total_seconds() / 3600).round(2)
    df["sla_met"] = (df["hours_to_close"].fillna(df["sla_hours"] + 1) <= df["sla_hours"])
    summary = df.groupby("technician", dropna=False)["sla_met"].mean().mul(100).round(1).reset_index(name="sla_percent")
    return {"rows": len(df), "outputs": [save_df(df, "tickets_processed.csv"), save_df(summary, "technician_sla.csv")]}


def run_inventory_dashboard() -> dict:
    df = read_csv()
    status = df.groupby(["lab", "status"]).size().reset_index(name="total")
    status.pivot(index="lab", columns="status", values="total").fillna(0).plot(kind="bar", stacked=True, figsize=(7, 4), title="Status do inventário de laboratório")
    report = "<h1>Resumo Do Inventário</h1>" + status.to_html(index=False)
    return {"rows": len(df), "outputs": [save_df(status, "inventory_status.csv"), save_report(report, "inventory_report.html"), save_chart("inventory_status.png")]}


def run_gantt() -> dict:
    df = read_csv()
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    start = df["start_date"].min()
    fig, axis = plt.subplots(figsize=(8, 4))
    for index, row in df.iterrows():
        offset = (row["start_date"] - start).days
        duration = (row["end_date"] - row["start_date"]).days + 1
        axis.broken_barh([(offset, duration)], (index - 0.35, 0.7))
    axis.set_yticks(range(len(df)))
    axis.set_yticklabels(df["task"])
    axis.set_xlabel("Dias desde o início do projeto")
    return {"rows": len(df), "outputs": [save_df(df, "project_schedule.csv"), save_chart("gantt_chart.png")]}


def run_network_topology() -> dict:
    df = read_csv()
    nodes = sorted(set(df["device"]).union(df["peer"]))
    angles = np.linspace(0, 2 * math.pi, len(nodes), endpoint=False)
    positions = {node: (math.cos(angle), math.sin(angle)) for node, angle in zip(nodes, angles)}
    plt.figure(figsize=(6, 6))
    for _, row in df.iterrows():
        x1, y1 = positions[row["device"]]
        x2, y2 = positions[row["peer"]]
        plt.plot([x1, x2], [y1, y2], color="#64748b")
    for node, (x, y) in positions.items():
        plt.scatter([x], [y], s=520, color="#0f766e")
        plt.text(x, y, node, ha="center", va="center", fontsize=8, color="white")
    plt.axis("off")
    return {"rows": len(df), "outputs": [save_df(df, "topology_links.csv"), save_chart("network_topology.png")]}


def run_requirements_report() -> dict:
    df = read_csv()
    summary = df.groupby(["category", "priority"]).size().reset_index(name="total")
    lines = ["# Especificação De Requisitos", "", "Respostas sintéticas de entrevista agrupadas para prática em sala.", ""]
    for _, row in df.iterrows():
        lines.append(f"- [{row['priority']}] {row['category']}: {row['need']} ({row['stakeholder']})")
    return {"rows": len(df), "outputs": [save_df(summary, "requirements_summary.csv"), save_report("\n".join(lines) + "\n", "requirements_report.md")]}


def run_support_flowchart() -> dict:
    edges = read_json()
    nodes = list(dict.fromkeys([edge["from"] for edge in edges] + [edge["to"] for edge in edges]))
    plt.figure(figsize=(8, 3))
    for index, node in enumerate(nodes):
        plt.scatter([index], [0], s=900, color="#14213d")
        plt.text(index, 0, node, ha="center", va="center", color="white", fontsize=8)
        if index < len(nodes) - 1:
            plt.arrow(index + 0.18, 0, 0.62, 0, head_width=0.06, length_includes_head=True, color="#64748b")
    plt.axis("off")
    return {"rows": len(edges), "outputs": [save_df(pd.DataFrame(edges), "support_process_edges.csv"), save_chart("support_flowchart.png")]}


def run_privacy_analyzer() -> dict:
    text = DATA_SAMPLE.read_text(encoding="utf-8").lower()
    terms = ["consent", "purpose", "security", "retention", "access", "deletion", "rights", "lgpd"]
    counts = pd.DataFrame({"term": terms, "count": [text.count(term) for term in terms]})
    counts.plot(kind="bar", x="term", y="count", figsize=(7, 4), legend=False, title="Amostra de vocabulário LGPD")
    return {"rows": len(counts), "outputs": [save_df(counts, "privacy_term_counts.csv"), save_chart("privacy_terms.png")]}


def run_cyber_incidents() -> dict:
    df = read_csv()
    pivot = df.set_index("month")
    pivot.plot(marker="o", figsize=(8, 4), title="Synthetic cyber incident trends")
    totals = pivot.sum().reset_index()
    totals.columns = ["category", "total"]
    return {"rows": len(df), "outputs": [save_df(totals, "incident_totals.csv"), save_chart("incident_trends.png")]}


def run_aup_simulator() -> dict:
    rules = pd.DataFrame(read_json())
    summary = rules.groupby("classification").size().reset_index(name="total")
    return {"rows": len(rules), "outputs": [save_df(rules, "policy_decisions.csv"), save_df(summary, "policy_summary.csv")]}


def run_wifi_scan() -> dict:
    df = read_csv()
    df["quality"] = pd.cut(df["rssi_dbm"], bins=[-100, -70, -55, 0], labels=["weak", "medium", "strong"])
    df.plot(kind="bar", x="ssid", y="rssi_dbm", figsize=(7, 4), legend=False, title="Synthetic Wi-Fi RSSI")
    return {"rows": len(df), "outputs": [save_df(df, "wifi_scan_analysis.csv"), save_chart("wifi_rssi.png")]}


def run_connection_quality() -> dict:
    df = read_csv()
    df["sla_status"] = np.where((df["download_mbps"] >= 150) & (df["latency_ms"] <= 40), "ok", "revisar")
    df.plot(x="timestamp", y=["download_mbps", "latency_ms"], marker="o", figsize=(8, 4), title="Connection quality sample")
    plt.xticks(rotation=25, ha="right")
    return {"rows": len(df), "revisar_points": int((df["sla_status"] == "revisar").sum()), "outputs": [save_df(df, "connection_quality.csv"), save_chart("connection_quality.png")]}


def run_wifi_heatmap() -> dict:
    df = read_csv()
    grid = df.pivot(index="y", columns="x", values="rssi_dbm").sort_index(ascending=False)
    plt.figure(figsize=(6, 5))
    plt.imshow(grid, cmap="viridis", aspect="equal")
    plt.colorbar(label="RSSI dBm")
    plt.xticks(range(len(grid.columns)), grid.columns)
    plt.yticks(range(len(grid.index)), grid.index)
    weak = df[df["rssi_dbm"] < -68]
    return {"rows": len(df), "weak_points": len(weak), "outputs": [save_df(weak, "weak_wifi_points.csv"), save_chart("wifi_coverage_heatmap.png")]}


def run_iot_traffic() -> dict:
    df = read_csv()
    stats = df.groupby("device")["bandwidth_kbps"].agg(["mean", "std"]).reset_index()
    df = df.merge(stats, on="device")
    df["z_score"] = ((df["bandwidth_kbps"] - df["mean"]) / df["std"].replace(0, np.nan)).fillna(0).round(2)
    df["anomaly"] = df["z_score"].abs() > 1.0
    df.boxplot(column="bandwidth_kbps", by="device", figsize=(7, 4))
    plt.suptitle("")
    plt.title("IoT bandwidth by device")
    return {"rows": len(df), "anomalies": int(df["anomaly"].sum()), "outputs": [save_df(df, "iot_traffic_scored.csv"), save_chart("iot_traffic_boxplot.png")]}


def run_availability_monitor() -> dict:
    df = read_csv()
    df["is_up"] = df["status"] == "up"
    summary = df.groupby("host").agg(availability_percent=("is_up", lambda s: round(float(s.mean() * 100), 1)), avg_latency_ms=("latency_ms", "mean")).reset_index()
    summary.plot(kind="bar", x="host", y="availability_percent", figsize=(7, 4), legend=False, title="Availability sample")
    return {"rows": len(df), "outputs": [save_df(summary, "availability_summary.csv"), save_chart("availability.png")]}


def run_log_analyzer() -> dict:
    pattern = re.compile(r'^(?P<client>\S+) .* \[(?P<date>[^:]+):(?P<hour>\d{2}):.*\] "(?P<method>\S+) (?P<route>\S+) .*" (?P<status>\d{3}) (?P<size>\d+)')
    rows = []
    for line in DATA_SAMPLE.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            rows.append(match.groupdict())
    df = pd.DataFrame(rows)
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "total"]
    return {"rows": len(df), "outputs": [save_df(df, "parsed_logs.csv"), save_df(status_counts, "status_counts.csv")]}


def run_backup_report() -> dict:
    df = read_csv()
    df["computed_hash"] = df.apply(lambda row: hashlib.md5(f"{row['file_name']}:{row['size_kb']}".encode()).hexdigest(), axis=1)
    df["checked"] = True
    return {"rows": len(df), "outputs": [save_df(df, "backup_report.csv")]}


def run_network_inventory() -> dict:
    df = read_csv()
    df["open_port_count"] = df["ports"].fillna("").apply(lambda value: 0 if not value else len(str(value).split(";")))
    ensure_dirs()
    json_path = DATA_PROCESSED / "network_inventory.json"
    json_path.write_text(df.to_json(orient="records", indent=2), encoding="utf-8")
    return {"rows": len(df), "outputs": [save_df(df, "network_inventory.csv"), str(json_path.relative_to(ROOT))]}


RUNNERS = {
    "faq_chatbot": run_faq_chatbot,
    "iot_simulator": run_iot_simulator,
    "ai_heatmap": run_ai_heatmap,
    "helpdesk_sla": run_helpdesk_sla,
    "inventory_dashboard": run_inventory_dashboard,
    "gantt": run_gantt,
    "network_topology": run_network_topology,
    "requirements_report": run_requirements_report,
    "support_flowchart": run_support_flowchart,
    "privacy_analyzer": run_privacy_analyzer,
    "cyber_incidents": run_cyber_incidents,
    "aup_simulator": run_aup_simulator,
    "wifi_scan": run_wifi_scan,
    "connection_quality": run_connection_quality,
    "wifi_heatmap": run_wifi_heatmap,
    "iot_traffic": run_iot_traffic,
    "availability_monitor": run_availability_monitor,
    "log_analyzer": run_log_analyzer,
    "backup_report": run_backup_report,
    "network_inventory": run_network_inventory,
}


def run_sample() -> dict:
    result = RUNNERS[PROJECT["kind"]]()
    result["project"] = PROJECT["slug"]
    result["code"] = PROJECT["code"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=PROJECT["description"])
    parser.add_argument("--sample", action="store_true", help="Run the safe sample workflow.")
    args = parser.parse_args()
    if not args.sample:
        print("External or live operations are disabled by default. Re-run with --sample.")
        return
    print(json.dumps(run_sample(), indent=2))


if __name__ == "__main__":
    main()
