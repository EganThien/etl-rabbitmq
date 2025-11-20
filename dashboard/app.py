from flask import Flask, jsonify, render_template_string
import os
import requests
import mysql.connector

app = Flask(__name__)

RABBIT_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBIT_USER = os.environ.get('RABBITMQ_DEFAULT_USER', 'guest')
RABBIT_PASS = os.environ.get('RABBITMQ_DEFAULT_PASS', 'guest')
RABBIT_MANAGEMENT = os.environ.get('RABBITMQ_MANAGEMENT_PORT', '15672')

MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))
MYSQL_DB = os.environ.get('MYSQL_DATABASE', 'etl_db')
MYSQL_USER = os.environ.get('MYSQL_USER', 'etl')
MYSQL_PASS = os.environ.get('MYSQL_PASSWORD', 'etlpass')

TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ETL Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="p-4">
    <div class="container">
      <h1>ETL RabbitMQ Dashboard</h1>
      <p class="text-muted">RabbitMQ: {{ rabbit_host }} | MySQL: {{ mysql_host }} | Last refresh: {{ ts }}</p>

      <div class="row">
        <div class="col-md-6">
          <h4>RabbitMQ Queues</h4>
          <table class="table table-sm table-striped">
            <thead><tr><th>Queue</th><th>Ready</th><th>Unacked</th></tr></thead>
            <tbody>
            {% for q in queues %}
              <tr><td>{{ q.name }}</td><td>{{ q.messages_ready }}</td><td>{{ q.messages_unacknowledged }}</td></tr>
            {% endfor %}
            </tbody>
          </table>
        </div>

        <div class="col-md-6">
          <h4>Database Counts</h4>
          <table class="table table-sm">
            <tbody>
              <tr><td>staging_employee</td><td>{{ counts.staging_employee }}</td></tr>
              <tr><td>staging_order_detail</td><td>{{ counts.staging_order_detail }}</td></tr>
              <tr><td>main_employee</td><td>{{ counts.main_employee }}</td></tr>
              <tr><td>main_order_detail</td><td>{{ counts.main_order_detail }}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="row mt-4">
        <div class="col-12">
          <h4>Recent Staging Rows (raw_payload + validation_errors)</h4>
          <table class="table table-sm table-bordered">
            <thead><tr><th>Source</th><th>ID</th><th>Created At</th><th>Payload (truncated)</th><th>Validation Errors</th></tr></thead>
            <tbody>
            {% for r in recent %}
              <tr>
                <td>{{ r.source }}</td>
                <td>{{ r.id }}</td>
                <td>{{ r.created_at }}</td>
                <td style="max-width:400px;"><pre style="white-space: pre-wrap; max-height:120px; overflow:auto;">{{ r.payload }}</pre></td>
                <td style="max-width:300px; word-break:break-word;">{{ r.errors }}</td>
              </tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
      </div>

      <div class="mt-3">
        <a class="btn btn-primary" href="/api/status" target="_blank">View JSON</a>
        <a class="btn btn-secondary" href="http://localhost:15672" target="_blank">RabbitMQ UI</a>
      </div>

    </div>
  </body>
</html>
"""


@app.route('/')
def index():
    status = get_status()
    import datetime
    recent = get_recent_staging()
    return render_template_string(
        TEMPLATE,
        queues=status.get('queues', []),
        counts=status.get('counts', {}),
        rabbit_host=RABBIT_HOST,
        mysql_host=MYSQL_HOST,
        ts=datetime.datetime.utcnow().isoformat(),
        recent=recent,
    )


@app.route('/api/status')
def api_status():
    return jsonify(get_status())


def get_status():
    return {
        'queues': get_queues(),
        'counts': get_counts(),
        'recent': get_recent_staging(),
    }


def get_queues():
    url = f'http://{RABBIT_HOST}:{RABBIT_MANAGEMENT}/api/queues'
    try:
        resp = requests.get(url, auth=(RABBIT_USER, RABBIT_PASS), timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # return simplified list
        simplified = []
        for q in data:
            simplified.append({
                'name': q.get('name'),
                'messages_ready': q.get('messages_ready', 0),
                'messages_unacknowledged': q.get('messages_unacknowledged', 0)
            })
        return simplified
    except Exception as ex:
        return [{'name': 'error', 'messages_ready': 0, 'messages_unacknowledged': 0, 'error': str(ex)}]


def get_counts():
    counts = {
        'staging_employee': 0,
        'staging_order_detail': 0,
        'main_employee': 0,
        'main_order_detail': 0
    }
    try:
        conn = mysql.connector.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB)
        cur = conn.cursor()
        for table in ['staging_employee','staging_order_detail','main_employee','main_order_detail']:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            row = cur.fetchone()
            counts[table] = int(row[0]) if row and row[0] is not None else 0
        cur.close()
        conn.close()
    except Exception as ex:
        # return error info in counts keys
        counts = {k: f'error: {str(ex)}' for k in counts}
    return counts


def get_recent_staging(limit=10, truncate=500):
    """Return last `limit` rows from staging tables combined, with raw_payload truncated."""
    out = []
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB
        )
        cur = conn.cursor()
        # combine employee and order staging rows
        sql = (
          "SELECT source, id, created_at, raw_payload, validation_errors FROM ("
          " SELECT 'employee' AS source, id, created_at, raw_payload, validation_errors FROM staging_employee"
          " UNION ALL"
          " SELECT 'order' AS source, id, created_at, raw_payload, validation_errors FROM staging_order_detail"
          " ) t ORDER BY created_at DESC LIMIT %s"
        )
        cur.execute(sql, (limit,))
        rows = cur.fetchall()
        for src, idv, created_at, raw, errors in rows:
          payload = raw if raw is not None else ''
          if len(payload) > truncate:
            payload = payload[:truncate] + '...'
          errtxt = errors if errors is not None else ''
          out.append({'source': src, 'id': idv, 'created_at': str(created_at), 'payload': payload, 'errors': errtxt})
        cur.close()
        conn.close()
    except Exception as ex:
        out = [{'source': 'error', 'id': '', 'created_at': '', 'payload': str(ex)}]
    return out


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
