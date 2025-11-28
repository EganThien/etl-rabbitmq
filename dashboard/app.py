from flask import Flask, jsonify, render_template_string, request
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
      <div class="d-flex justify-content-between align-items-center">
        <h1>ETL Pipeline Dashboard</h1>
        <small class="text-muted">RabbitMQ: {{ rabbit_host }} | MySQL: {{ mysql_host }} | Last refresh: {{ ts }}</small>
      </div>

      <!-- summary cards -->
      <div class="row my-3">
        <div class="col-sm-2"><div class="card p-2"><small>Total Checked</small><h3>{{ counts.main_employee + counts.main_order_detail + counts.staging_employee + counts.staging_order_detail }}</h3></div></div>
        <div class="col-sm-2"><div class="card p-2"><small>Staging</small><h3>{{ counts.staging_employee + counts.staging_order_detail }}</h3></div></div>
        <div class="col-sm-2"><div class="card p-2"><small>Main</small><h3>{{ counts.main_employee + counts.main_order_detail }}</h3></div></div>
        <div class="col-sm-2"><div class="card p-2 text-bg-success"><small>Passed</small><h3>—</h3></div></div>
        <div class="col-sm-2"><div class="card p-2 text-bg-danger"><small>Errors</small><h3>{{ counts_errors }}</h3></div></div>
      </div>

      <!-- two-column DQ view -->
      <div class="row">
        <div class="col-md-7">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">Dữ Liệu Đã Transform</h5>
              <div>
                <label for="main-entity">Entity</label>
                <select id="main-entity" class="form-select form-select-sm" style="width:200px; display:inline-block;" onchange="loadMain()">
                  <option value="employee">Employees</option>
                  <option value="order">Orders</option>
                </select>
                <button class="btn btn-sm btn-secondary ms-2" onclick="loadMain()">Refresh</button>
              </div>
              <div id="main-table" class="mt-3"></div>
            </div>
          </div>
        </div>

        <div class="col-md-5">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">Lỗi Validation</h5>
              <div>
                <label for="staging-entity">Entity</label>
                <select id="staging-entity" class="form-select form-select-sm" style="width:200px; display:inline-block;" onchange="loadErrors()">
                  <option value="employee">Employees</option>
                  <option value="order">Orders</option>
                </select>
                <button class="btn btn-sm btn-secondary ms-2" onclick="loadErrors()">Refresh</button>
              </div>
              <div id="errors-list" class="mt-3" style="max-height:520px; overflow:auto;"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-3">
        <a class="btn btn-primary" href="/api/status" target="_blank">View JSON</a>
        <a class="btn btn-secondary" href="http://localhost:15672" target="_blank">RabbitMQ UI</a>
      </div>

    </div>

    <script>
      async function loadMain(){
        const entity = document.getElementById('main-entity').value;
        const el = document.getElementById('main-table');
        el.innerHTML = '<div>Loading...</div>';
        try{
          const resp = await fetch(`/api/main/${entity}?limit=50`);
          const data = await resp.json();
          if(!Array.isArray(data)) { el.innerText = JSON.stringify(data); return; }
          // build table
          if(data.length===0){ el.innerHTML = '<div class="text-muted">No records</div>'; return; }
          let html = '<table class="table table-sm table-striped"><thead><tr>';
          const cols = Object.keys(data[0]);
          for(const c of cols) html += `<th>${c}</th>`;
          html += '</tr></thead><tbody>';
          for(const r of data){ html += '<tr>'; for(const c of cols){ let v = r[c]; if(v===null) v=''; html += `<td style="max-width:200px; word-break:break-word;">${String(v)}</td>` } html += '</tr>'; }
          html += '</tbody></table>';
          el.innerHTML = html;
        }catch(e){ el.innerText = 'Error: '+e }
      }

      async function loadErrors(){
        const entity = document.getElementById('staging-entity').value;
        const el = document.getElementById('errors-list');
        el.innerHTML = '<div>Loading...</div>';
        try{
          const resp = await fetch(`/api/staging/${entity}/errors?limit=100`);
          const data = await resp.json();
          if(!Array.isArray(data)){ el.innerText = JSON.stringify(data); return; }
          if(data.length===0){ el.innerHTML = '<div class="text-muted">No validation errors</div>'; return; }
          let html='';
          for(const row of data){
            html += `<div class="border rounded p-2 mb-2"><strong>id:</strong> ${row.id} <br/><small class="text-muted">source: ${row.source} created: ${row.created_at}</small><div style="margin-top:8px;">`;
            try{
              const errs = row.validation_errors;
              if(Array.isArray(errs)){
                for(const e of errs){ html += `<div class="text-danger">[${e.field || ''}] ${e.message || JSON.stringify(e)}</div>` }
              } else {
                html += `<pre style="white-space:pre-wrap">${JSON.stringify(errs)}</pre>`
              }
            }catch(x){ html += `<pre>${row.validation_errors}</pre>` }
            html += '</div></div>';
          }
          el.innerHTML = html;
        }catch(e){ el.innerText = 'Error: '+e }
      }

      // initial load
      loadMain(); loadErrors();
    </script>
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
    'errors_count': get_errors_count(),
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


  def get_errors_count():
    try:
      conn = mysql.connector.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB)
      cur = conn.cursor()
      cur.execute("SELECT COUNT(*) FROM (SELECT id FROM staging_employee WHERE validation_errors IS NOT NULL UNION ALL SELECT id FROM staging_order_detail WHERE validation_errors IS NOT NULL) t")
      row = cur.fetchone()
      cur.close()
      conn.close()
      return int(row[0]) if row and row[0] is not None else 0
    except Exception:
      return 0


  # API: main data
  @app.route('/api/main/<entity>')
  def api_main(entity):
    limit = int(request.args.get('limit', '50'))
    out = []
    try:
      conn = mysql.connector.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB)
      cur = conn.cursor()
      if entity == 'employee':
        cur.execute(f"SELECT id, first_name, last_name, email FROM main_employee ORDER BY id DESC LIMIT %s", (limit,))
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
          out.append({cols[i]: row[i] for i in range(len(cols))})
      elif entity == 'order':
        cur.execute(f"SELECT id, order_id, product_code, quantity, price FROM main_order_detail ORDER BY id DESC LIMIT %s", (limit,))
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
          out.append({cols[i]: row[i] for i in range(len(cols))})
      else:
        return jsonify({'error': 'unknown entity'}), 400
      cur.close()
      conn.close()
    except Exception as ex:
      return jsonify({'error': str(ex)}), 500
    return jsonify(out)


  # API: staging errors
  @app.route('/api/staging/<entity>/errors')
  def api_staging_errors(entity):
    limit = int(request.args.get('limit', '100'))
    out = []
    try:
      conn = mysql.connector.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB)
      cur = conn.cursor()
      if entity == 'employee':
        cur.execute("SELECT id, created_at, raw_payload, validation_errors FROM staging_employee WHERE validation_errors IS NOT NULL ORDER BY created_at DESC LIMIT %s", (limit,))
      elif entity == 'order':
        cur.execute("SELECT id, created_at, raw_payload, validation_errors FROM staging_order_detail WHERE validation_errors IS NOT NULL ORDER BY created_at DESC LIMIT %s", (limit,))
      else:
        return jsonify({'error': 'unknown entity'}), 400
      cols = [d[0] for d in cur.description]
      for row in cur.fetchall():
        rec = {cols[i]: row[i] for i in range(len(cols))}
        # try to parse validation_errors if it's JSON
        try:
          import json
          ve = rec.get('validation_errors')
          if ve is not None and isinstance(ve, str):
            rec['validation_errors'] = json.loads(ve)
        except Exception:
          pass
        rec['source'] = entity
        out.append(rec)
      cur.close()
      conn.close()
    except Exception as ex:
      return jsonify({'error': str(ex)}), 500
    return jsonify(out)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
