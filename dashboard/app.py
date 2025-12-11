# ETL Dashboard with Transform button
from flask import Flask, jsonify, render_template_string, request, send_file, send_from_directory
import os
import requests
import mysql.connector
import csv
import subprocess
import re
import json
from decimal import Decimal
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Custom JSON encoder to handle Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

app.json_encoder = DecimalEncoder

UPLOAD_FOLDER = '/tmp/csv_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

RABBIT_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBIT_USER = os.environ.get('RABBITMQ_DEFAULT_USER', 'guest')
RABBIT_PASS = os.environ.get('RABBITMQ_DEFAULT_PASS', 'guest')
RABBIT_MANAGEMENT = os.environ.get('RABBITMQ_MANAGEMENT_PORT', '15672')

MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))
MYSQL_DB = os.environ.get('MYSQL_DATABASE', 'etl_db')
MYSQL_USER = os.environ.get('MYSQL_USER', 'etl')
MYSQL_PASS = os.environ.get('MYSQL_PASSWORD', 'etlpass')

def get_mysql_connection():
    """Helper function to create MySQL connection with proper charset"""
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASS,
        database=MYSQL_DB,
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci',
        use_unicode=True
    )
    # Explicitly set charset for the connection
    cursor = conn.cursor()
    cursor.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
    cursor.execute("SET CHARACTER SET utf8mb4")
    cursor.close()
    return conn

TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ETL Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body {
        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 50%, #e0f2f1 100%);
        min-height: 100vh;
      }
      .btn-success {
        background: linear-gradient(135deg, #81c784 0%, #66bb6a 100%);
        border: none;
        box-shadow: 0 2px 8px rgba(129, 199, 132, 0.25);
        color: white;
      }
      .btn-success:hover {
        background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%);
        box-shadow: 0 4px 12px rgba(102, 187, 106, 0.35);
        transform: translateY(-1px);
      }
      .btn-primary {
        background: linear-gradient(135deg, #80cbc4 0%, #4db6ac 100%);
        border: none;
        box-shadow: 0 2px 8px rgba(128, 203, 196, 0.25);
        color: white;
      }
      .btn-primary:hover {
        background: linear-gradient(135deg, #4db6ac 0%, #26a69a 100%);
        box-shadow: 0 4px 12px rgba(77, 182, 172, 0.35);
        transform: translateY(-1px);
      }
      .btn-warning {
        background: linear-gradient(135deg, #ffcc80 0%, #ffb74d 100%);
        border: none;
        box-shadow: 0 2px 8px rgba(255, 204, 128, 0.25);
        color: white;
      }
      .btn-warning:hover {
        background: linear-gradient(135deg, #ffb74d 0%, #ffa726 100%);
        box-shadow: 0 4px 12px rgba(255, 183, 77, 0.35);
        transform: translateY(-1px);
      }
      .btn-info {
        background: linear-gradient(135deg, #81d4fa 0%, #4fc3f7 100%);
        border: none;
        box-shadow: 0 2px 8px rgba(129, 212, 250, 0.25);
        color: white;
      }
      .btn-info:hover {
        background: linear-gradient(135deg, #4fc3f7 0%, #29b6f6 100%);
        box-shadow: 0 4px 12px rgba(79, 195, 247, 0.35);
        transform: translateY(-1px);
      }
      .card {
        background: rgba(255, 255, 255, 0.95);
        border: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        border-radius: 12px;
      }
      .text-bg-success {
        background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%) !important;
        box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
      }
      .text-bg-danger {
        background: linear-gradient(135deg, #ef5350 0%, #e53935 100%) !important;
        box-shadow: 0 4px 8px rgba(239, 83, 80, 0.3);
      }
      h1, h2, h3, h5 {
        color: #2e7d32;
      }
      .table thead {
        background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
        color: #1b5e20;
      }
    </style>
  </head>
  <body class="p-4">
    <div class="container">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1>Dashboard Hệ Thống ETL</h1>
        <div class="text-end">
          <button class="btn btn-success btn-lg mb-2 me-2" onclick="runTransform()" id="transformBtn">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-wind" viewBox="0 0 16 16">
              <path d="M12.5 2A2.5 2.5 0 0 0 10 4.5a.5.5 0 0 1-1 0A3.5 3.5 0 1 1 12.5 8H.5a.5.5 0 0 1 0-1h12a2.5 2.5 0 0 0 0-5zm-7 1a1 1 0 0 0-1 1 .5.5 0 0 1-1 0 2 2 0 1 1 2 2h-5a.5.5 0 0 1 0-1h5a1 1 0 0 0 0-2zM0 9.5A.5.5 0 0 1 .5 9h10.042a3 3 0 1 1-3 3 .5.5 0 0 1 1 0 2 2 0 1 0 2-2H.5a.5.5 0 0 1-.5-.5z"/>
            </svg>
            <span id="transformBtnText">Chạy Transform</span>
            <span class="spinner-border spinner-border-sm ms-2 d-none" id="transformSpinner"></span>
          </button>
          <a href="/upload" class="btn btn-primary btn-lg mb-2 me-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-upload" viewBox="0 0 16 16">
              <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
              <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
            </svg>
            Tải Lên File CSV
          </a>
          <div class="btn-group mb-2 me-2" role="group">
            <a href="/export/employee" class="btn btn-info">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download" viewBox="0 0 16 16">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
              </svg>
              Export Nhân Viên
            </a>
            <a href="/export/order" class="btn btn-info">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download" viewBox="0 0 16 16">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
              </svg>
              Export Đơn Hàng
            </a>
          </div>
          <div class="btn-group mb-2 me-2" role="group">
            <a href="/edit-errors/employee" class="btn btn-warning">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil-square" viewBox="0 0 16 16">
                <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
                <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
              </svg>
              Sửa Lỗi NV
            </a>
            <a href="/edit-errors/order" class="btn btn-warning">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil-square" viewBox="0 0 16 16">
                <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
                <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
              </svg>
              Sửa Lỗi ĐH
            </a>
          </div>
          <div class="btn-group mb-2 me-2" role="group">
            <a href="/history" class="btn btn-info" style="background: linear-gradient(135deg, #81d4fa 0%, #4fc3f7 100%);">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-clock-history" viewBox="0 0 16 16">
                <path d="M8.515 1.019A7 7 0 0 0 8 1V0a8 8 0 0 1 .589.022l-.074.997zm2.004.45a7.003 7.003 0 0 0-.985-.299l.219-.976c.383.086.76.2 1.126.342l-.36.933zm1.37.71a7.01 7.01 0 0 0-.439-.27l.493-.87a8.025 8.025 0 0 1 .979.654l-.615.789a6.996 6.996 0 0 0-.418-.302zm1.834 1.79a6.99 6.99 0 0 0-.653-.796l.724-.69c.27.285.52.59.747.91l-.818.576zm.744 1.352a7.08 7.08 0 0 0-.214-.468l.893-.45a7.976 7.976 0 0 1 .45 1.088l-.95.313a7.023 7.023 0 0 0-.179-.483zm.53 2.507a6.991 6.991 0 0 0-.1-1.025l.985-.17c.067.386.106.778.116 1.17l-1 .025zm-.131 1.538c.033-.17.06-.339.081-.51l.993.123a7.957 7.957 0 0 1-.23 1.155l-.964-.267c.046-.165.086-.332.12-.501zm-.952 2.379c.184-.29.346-.594.486-.908l.914.405c-.16.36-.345.706-.555 1.038l-.845-.535zm-.964 1.205c.122-.122.239-.248.35-.378l.758.653a8.073 8.073 0 0 1-.401.432l-.707-.707z"/>
                <path d="M8 1a7 7 0 1 0 4.95 11.95l.707.707A8.001 8.001 0 1 1 8 0v1z"/>
                <path d="M7.5 3a.5.5 0 0 1 .5.5v5.21l3.248 1.856a.5.5 0 0 1-.496.868l-3.5-2A.5.5 0 0 1 7 9V3.5a.5.5 0 0 1 .5-.5z"/>
              </svg>
              📊 Transform History
            </a>
            <a href="/rules" class="btn" style="background: linear-gradient(135deg, #ffcc80 0%, #ffb74d 100%);">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-gear-fill" viewBox="0 0 16 16">
                <path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"/>
              </svg>
              ⚙️ Rules Config
            </a>
          </div>
          <div><small class="text-muted">RabbitMQ: {{ rabbit_host }} | MySQL: {{ mysql_host }} | Cập nhật: {{ ts }}</small></div>
        </div>
      </div>
      
      <!-- Transform Alert -->
      <div id="transformAlert" class="alert alert-dismissible fade d-none" role="alert">
        <span id="transformAlertText"></span>
        <button type="button" class="btn-close" onclick="document.getElementById('transformAlert').classList.add('d-none')"></button>
      </div>
      
      <!-- Normalization Info -->
      <div class="alert alert-dismissible fade show" role="alert" style="background: linear-gradient(135deg, #d4f1d4 0%, #e8f5e9 100%); border: 1px solid #81c784; color: #2e7d32;">
        <strong>🍃 Chuẩn Hóa Dữ Liệu Được Bật:</strong>
        <div class="row mt-2">
          <div class="col-md-6">
            <strong style="color: #1b5e20;">👤 Nhân Viên:</strong>
            <ul class="mb-0 mt-1">
              <li><strong>Họ Tên:</strong> Chuẩn hóa chữ hoa đầu từ (Title Case)</li>
              <li><strong>Email:</strong> Chữ thường, loại bỏ khoảng trắng</li>
              <li><strong>Số điện thoại:</strong> Định dạng E.164 (+84xxx)</li>
            </ul>
          </div>
          <div class="col-md-6">
            <strong style="color: #1b5e20;">📦 Đơn Hàng:</strong>
            <ul class="mb-0 mt-1">
              <li><strong>Mã sản phẩm:</strong> Chữ hoa, loại bỏ khoảng trắng</li>
              <li><strong>Số lượng:</strong> Số nguyên dương</li>
              <li><strong>Giá:</strong> Làm tròn 2 chữ số thập phân</li>
            </ul>
          </div>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>

      <!-- summary cards -->
      <div class="row my-3">
        <div class="col-sm-3">
          <div class="card p-3">
            <small class="text-muted">Tổng Số Bản Ghi</small>
            <h2 class="mb-0">{{ counts.main_employee + counts.main_order_detail + counts.staging_employee + counts.staging_order_detail }}</h2>
            <small class="text-muted">Tất cả dữ liệu trong hệ thống</small>
          </div>
        </div>
        <div class="col-sm-2">
          <div class="card p-3 border-warning">
            <small class="text-muted">⏳ Staging</small>
            <h3 class="mb-0">{{ counts.staging_employee + counts.staging_order_detail }}</h3>
            <small class="text-warning">Chờ xử lý + Lỗi</small>
          </div>
        </div>
        <div class="col-sm-2">
          <div class="card p-3">
            <small class="text-muted">DB Chính</small>
            <h3 class="mb-0">{{ counts.main_employee + counts.main_order_detail }}</h3>
            <small class="text-muted">Dữ liệu hợp lệ</small>
          </div>
        </div>
        <div class="col-sm-2">
          <div class="card p-3 text-bg-success text-white" style="cursor: pointer;" onclick="showPassedDetails()">
            <small>✓ Hợp Lệ</small>
            <h2 class="mb-1">{{ counts.main_employee + counts.main_order_detail }}</h2>
            <small>NV: {{ counts.main_employee }} | ĐH: {{ counts.main_order_detail }}</small>
            <div class="mt-2"><small>👆 Xem chi tiết</small></div>
          </div>
        </div>
        <div class="col-sm-3">
          <div class="card p-3 text-bg-danger text-white" style="cursor: pointer;" onclick="showErrorDetails()">
            <small>✗ Lỗi</small>
            <h2 class="mb-1">{{ counts_errors }}</h2>
            <small>NV: {{ counts_errors_emp }} | ĐH: {{ counts_errors_ord }}</small>
            <div class="mt-2"><small>👆 Xem chi tiết</small></div>
          </div>
        </div>
      </div>

      <!-- Details Section -->
      <div id="details-section" class="row mt-3" style="display:none;">
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="card-title mb-0" id="details-title">Chi Tiết</h5>
                <button class="btn btn-sm btn-secondary" onclick="hideDetails()">Đóng ✕</button>
              </div>
              <div id="details-content"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- two-column DQ view -->
      <div class="row">
        <div class="col-md-7">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">Dữ Liệu Đã Xử Lý (DB Chính)</h5>
              <div>
                <label for="main-entity">Loại Dữ Liệu</label>
                <select id="main-entity" class="form-select form-select-sm" style="width:200px; display:inline-block;" onchange="loadMain()">
                  <option value="employee">Nhân Viên</option>
                  <option value="order">Đơn Hàng</option>
                </select>
                <button class="btn btn-sm btn-secondary ms-2" onclick="loadMain()">Làm Mới</button>
              </div>
              <div id="main-table" class="mt-3"></div>
            </div>
          </div>
        </div>

        <div class="col-md-5">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">Lỗi Kiểm Tra Dữ Liệu</h5>
              <div>
                <label for="staging-entity">Loại Dữ Liệu</label>
                <select id="staging-entity" class="form-select form-select-sm" style="width:200px; display:inline-block;" onchange="loadErrors()">
                  <option value="employee">Nhân Viên</option>
                  <option value="order">Đơn Hàng</option>
                </select>
                <button class="btn btn-sm btn-secondary ms-2" onclick="loadErrors()">Làm Mới</button>
              </div>
              <div id="errors-list" class="mt-3" style="max-height:520px; overflow:auto;"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-3">
        <a class="btn btn-primary" href="/api/status" target="_blank">Xem Dữ Liệu JSON</a>
        <a class="btn btn-secondary" href="http://localhost:15672" target="_blank">Giao Diện RabbitMQ</a>
      </div>

    </div>

    <script>
      async function loadMain(){
        const entity = document.getElementById('main-entity').value;
        const el = document.getElementById('main-table');
        el.innerHTML = '<div>Đang tải...</div>';
        try{
          const resp = await fetch(`/api/main/${entity}?limit=50`);
          const data = await resp.json();
          if(!Array.isArray(data)) { el.innerText = JSON.stringify(data); return; }
          // build table
          if(data.length===0){ el.innerHTML = '<div class="text-muted">Không có dữ liệu</div>'; return; }
          let html = '<table class="table table-sm table-striped"><thead><tr>';
          const cols = Object.keys(data[0]);
          for(const c of cols) html += `<th>${c}</th>`;
          html += '</tr></thead><tbody>';
          for(const r of data){ html += '<tr>'; for(const c of cols){ let v = r[c]; if(v===null) v=''; html += `<td style="max-width:200px; word-break:break-word;">${String(v)}</td>` } html += '</tr>'; }
          html += '</tbody></table>';
          el.innerHTML = html;
        }catch(e){ el.innerText = 'Lỗi: '+e }
      }

      async function loadErrors(){
        const entity = document.getElementById('staging-entity').value;
        const el = document.getElementById('errors-list');
        el.innerHTML = '<div>Đang tải...</div>';
        try{
          const resp = await fetch(`/api/staging/${entity}/errors?limit=100`);
          const data = await resp.json();
          if(!Array.isArray(data)){ el.innerText = JSON.stringify(data); return; }
          if(data.length===0){ el.innerHTML = '<div class="text-muted">Không có lỗi kiểm tra</div>'; return; }
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
        }catch(e){ el.innerText = 'Lỗi: '+e }
      }

      // Functions to show/hide details
      function hideDetails(){
        document.getElementById('details-section').style.display = 'none';
      }

      async function showPassedDetails(){
        const section = document.getElementById('details-section');
        const title = document.getElementById('details-title');
        const content = document.getElementById('details-content');
        
        title.innerHTML = '✓ Dữ Liệu Hợp Lệ - Đã Lưu Vào Database Chính';
        content.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><div>Đang tải...</div></div>';
        section.style.display = 'block';
        
        try {
          // Load both employees and orders
          const [empResp, ordResp] = await Promise.all([
            fetch('/api/main/employee?limit=100'),
            fetch('/api/main/order?limit=100')
          ]);
          
          const employees = await empResp.json();
          const orders = await ordResp.json();
          
          let html = '<div class="row">';
          
          // Employees table
          html += '<div class="col-md-6"><h6 class="text-success">✓ Nhân Viên Hợp Lệ (' + employees.length + ')</h6>';
          if(employees.length > 0){
            html += '<div style="max-height:400px; overflow:auto;"><table class="table table-sm table-striped table-hover">';
            html += '<thead><tr><th>Mã NV</th><th>Họ Tên</th><th>Email</th><th>Điện Thoại</th></tr></thead><tbody>';
            for(const e of employees){
              html += `<tr><td>${e.employee_id || ''}</td><td>${e.full_name || ''}</td><td>${e.email || ''}</td><td>${e.phone || ''}</td></tr>`;
            }
            html += '</tbody></table></div>';
          } else {
            html += '<div class="text-muted">Không có dữ liệu</div>';
          }
          html += '</div>';
          
          // Orders table
          html += '<div class="col-md-6"><h6 class="text-success">✓ Đơn Hàng Hợp Lệ (' + orders.length + ')</h6>';
          if(orders.length > 0){
            html += '<div style="max-height:400px; overflow:auto;"><table class="table table-sm table-striped table-hover">';
            html += '<thead><tr><th>Mã ĐH</th><th>Mã SP</th><th>SL</th><th>Giá</th></tr></thead><tbody>';
            for(const o of orders){
              html += `<tr><td>${o.order_id || ''}</td><td>${o.product_id || ''}</td><td>${o.quantity || ''}</td><td>$${o.price || ''}</td></tr>`;
            }
            html += '</tbody></table></div>';
          } else {
            html += '<div class="text-muted">Không có dữ liệu</div>';
          }
          html += '</div></div>';
          
          content.innerHTML = html;
        } catch(e) {
          content.innerHTML = '<div class="alert alert-danger">Lỗi khi tải dữ liệu: ' + e + '</div>';
        }
      }

      async function showErrorDetails(){
        const section = document.getElementById('details-section');
        const title = document.getElementById('details-title');
        const content = document.getElementById('details-content');
        
        title.innerHTML = '✗ Dữ Liệu Lỗi - Không Đạt Kiểm Tra';
        content.innerHTML = '<div class="text-center"><div class="spinner-border text-danger" role="status"></div><div>Đang tải...</div></div>';
        section.style.display = 'block';
        
        try {
          // Load error records from both tables
          const [empResp, ordResp] = await Promise.all([
            fetch('/api/staging/employee/errors?limit=100'),
            fetch('/api/staging/order/errors?limit=100')
          ]);
          
          const empErrors = await empResp.json();
          const ordErrors = await ordResp.json();
          
          let html = '<div class="row">';
          
          // Employee errors
          html += '<div class="col-md-6"><h6 class="text-danger">✗ Lỗi Nhân Viên (' + empErrors.length + ')</h6>';
          if(empErrors.length > 0){
            html += '<div style="max-height:400px; overflow:auto;">';
            for(const row of empErrors){
              html += '<div class="border border-danger rounded p-2 mb-2 bg-light">';
              html += `<strong>Mã NV:</strong> ${row.employee_id || row.id}<br/>`;
              html += `<strong>Họ Tên:</strong> ${row.full_name || 'Không có'}<br/>`;
              html += `<strong>Email:</strong> ${row.email || 'Không có'}<br/>`;
              html += `<strong>Điện Thoại:</strong> ${row.phone || 'Không có'}<br/>`;
              html += '<div class="mt-2 p-2 bg-white border-start border-danger border-3">';
              html += '<strong class="text-danger">Lỗi Kiểm Tra:</strong><br/>';
              try{
                const errs = row.validation_errors;
                if(Array.isArray(errs)){
                  for(const e of errs){
                    html += `<div class="text-danger">⚠ <strong>[${e.field || ''}]:</strong> ${e.message || JSON.stringify(e)}</div>`;
                  }
                } else {
                  html += `<pre class="text-danger mb-0">${JSON.stringify(errs, null, 2)}</pre>`;
                }
              }catch(x){
                html += `<pre class="text-danger mb-0">${row.validation_errors}</pre>`;
              }
              html += '</div></div>';
            }
            html += '</div>';
          } else {
            html += '<div class="alert alert-success">Không có lỗi nhân viên! Tất cả hợp lệ ✓</div>';
          }
          html += '</div>';
          
          // Order errors
          html += '<div class="col-md-6"><h6 class="text-danger">✗ Lỗi Đơn Hàng (' + ordErrors.length + ')</h6>';
          if(ordErrors.length > 0){
            html += '<div style="max-height:400px; overflow:auto;">';
            for(const row of ordErrors){
              html += '<div class="border border-danger rounded p-2 mb-2 bg-light">';
              html += `<strong>Mã ĐH:</strong> ${row.order_id || row.id}<br/>`;
              html += `<strong>Mã SP:</strong> ${row.product_id || 'Không có'}<br/>`;
              html += `<strong>Số Lượng:</strong> ${row.quantity || 'Không có'}<br/>`;
              html += `<strong>Giá:</strong> ${row.price || 'Không có'} VNĐ<br/>`;
              html += '<div class="mt-2 p-2 bg-white border-start border-danger border-3">';
              html += '<strong class="text-danger">Lỗi Kiểm Tra:</strong><br/>';
              try{
                const errs = row.validation_errors;
                if(Array.isArray(errs)){
                  for(const e of errs){
                    html += `<div class="text-danger">⚠ <strong>[${e.field || ''}]:</strong> ${e.message || JSON.stringify(e)}</div>`;
                  }
                } else {
                  html += `<pre class="text-danger mb-0">${JSON.stringify(errs, null, 2)}</pre>`;
                }
              }catch(x){
                html += `<pre class="text-danger mb-0">${row.validation_errors}</pre>`;
              }
              html += '</div></div>';
            }
            html += '</div>';
          } else {
            html += '<div class="alert alert-success">Không có lỗi đơn hàng! Tất cả hợp lệ ✓</div>';
          }
          html += '</div></div>';
          
          content.innerHTML = html;
        } catch(e) {
          content.innerHTML = '<div class="alert alert-danger">Lỗi khi tải dữ liệu: ' + e + '</div>';
        }
      }

      // Run Transform function
      async function runTransform(){
        const btn = document.getElementById('transformBtn');
        const btnText = document.getElementById('transformBtnText');
        const spinner = document.getElementById('transformSpinner');
        const alert = document.getElementById('transformAlert');
        const alertText = document.getElementById('transformAlertText');
        
        btn.disabled = true;
        btnText.textContent = 'Đang xử lý...';
        spinner.classList.remove('d-none');
        alert.classList.add('d-none');
        
        try {
          const response = await fetch('/api/run-transform-v2', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
          });
          
          // Check if response is OK before parsing JSON
          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server returned ${response.status}: ${errorText.substring(0, 200)}`);
          }
          
          const result = await response.json();
          
          if(result.success){
            alert.className = 'alert alert-success alert-dismissible fade show';
            alertText.innerHTML = `<strong>✓ Transform thành công!</strong><br/>` +
              `- Nhân viên: ${result.employees || 0} records hợp lệ đã chuyển sang DB chính<br/>` +
              `- Đơn hàng: ${result.orders || 0} records hợp lệ đã chuyển sang DB chính<br/>` +
              `- Lỗi: ${result.errors || 0} records có validation errors<br/>` +
              `- Thời gian xử lý: ${result.processing_time_ms || 0}ms`;
            
            // Reload data after 2 seconds
            setTimeout(() => {
              location.reload();
            }, 2000);
          } else {
            alert.className = 'alert alert-danger alert-dismissible fade show';
            alertText.innerHTML = `<strong>✗ Lỗi:</strong> ${result.error || 'Lỗi không xác định'}`;
          }
        } catch(e) {
          alert.className = 'alert alert-danger alert-dismissible fade show';
          alertText.innerHTML = `<strong>✗ Lỗi kết nối:</strong> ${e.message}`;
          console.error('Transform error:', e);
        } finally {
          btn.disabled = false;
          btnText.textContent = 'Chạy Transform';
          spinner.classList.add('d-none');
        }
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
    counts_errors = get_errors_count()
    
    # Get detailed error counts
    counts_errors_emp = 0
    counts_errors_ord = 0
    try:
        conn = get_mysql_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM staging_employee WHERE validation_errors IS NOT NULL")
        counts_errors_emp = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM staging_order_detail WHERE validation_errors IS NOT NULL")
        counts_errors_ord = cur.fetchone()[0]
        cur.close()
        conn.close()
    except:
        pass
    
    return render_template_string(
        TEMPLATE,
        queues=status.get('queues', []),
        counts=status.get('counts', {}),
        counts_errors=counts_errors,
        counts_errors_emp=counts_errors_emp,
        counts_errors_ord=counts_errors_ord,
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
        conn = get_mysql_connection()
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
        conn = get_mysql_connection()
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
        conn = get_mysql_connection()
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
        conn = get_mysql_connection()
        cur = conn.cursor()
        if entity == 'employee':
            cur.execute(f"SELECT id, employee_id, full_name, email, phone, created_at FROM main_employee ORDER BY id DESC LIMIT %s", (limit,))
            cols = [d[0] for d in cur.description]
            for row in cur.fetchall():
                out.append({cols[i]: row[i] for i in range(len(cols))})
        elif entity == 'order':
            cur.execute(f"SELECT id, order_id, product_id, quantity, price, created_at FROM main_order_detail ORDER BY id DESC LIMIT %s", (limit,))
            cols = [d[0] for d in cur.description]
            for row in cur.fetchall():
                out.append({cols[i]: row[i] for i in range(len(cols))})
        else:
            return jsonify({'error': 'loại dữ liệu không xác định'}), 400
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
        conn = get_mysql_connection()
        cur = conn.cursor()
        if entity == 'employee':
            cur.execute("SELECT id, employee_id, full_name, email, phone, created_at, validation_errors FROM staging_employee WHERE validation_errors IS NOT NULL ORDER BY created_at DESC LIMIT %s", (limit,))
        elif entity == 'order':
            cur.execute("SELECT id, order_id, product_id, quantity, price, created_at, validation_errors FROM staging_order_detail WHERE validation_errors IS NOT NULL ORDER BY created_at DESC LIMIT %s", (limit,))
        else:
            return jsonify({'error': 'loại dữ liệu không xác định'}), 400
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


@app.route('/upload')
def upload_page():
    with open('upload.html', 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Không có file'}), 400
        
        file = request.files['file']
        filename = request.form.get('filename', 'upload')
        file_type = request.form.get('type', 'employee')
        
        # Generate batch_id for this upload
        from datetime import datetime
        batch_id = f"{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Secure filename
        filename = secure_filename(filename) + '.csv'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Insert to database
        inserted = 0
        skipped = 0
        errors = []
        conn = get_mysql_connection()
        cur = conn.cursor()
        
        # Try different encodings
        encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        content = None
        used_encoding = None
        
        for encoding in encodings_to_try:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                    used_encoding = encoding
                    break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return jsonify({'success': False, 'error': 'Không thể đọc file. Encoding không hợp lệ.'}), 400
        
        # Parse CSV from content
        from io import StringIO
        csv_file = StringIO(content)
        reader = csv.reader(csv_file)
        
        # Skip header row
        try:
            header = next(reader)
            print(f"CSV Header: {header}")
        except StopIteration:
            return jsonify({'success': False, 'error': 'File CSV trống!'}), 400
        
        # Process data rows
        row_num = 1
        for row in reader:
            row_num += 1
            
            # Skip empty rows
            if not row or all(not cell.strip() for cell in row):
                skipped += 1
                continue
            
            # Debug: print row info
            print(f"Row {row_num}: {row} (length: {len(row)})")
            
            try:
                if file_type == 'employee':
                    if len(row) < 4:
                        errors.append(f"Dòng {row_num}: Thiếu cột (cần 4 cột, có {len(row)})")
                        skipped += 1
                        continue
                    
                    emp_id = row[0].strip() if len(row) > 0 else ''
                    full_name = row[1].strip() if len(row) > 1 else ''
                    email = row[2].strip() if len(row) > 2 else ''
                    phone = row[3].strip() if len(row) > 3 else ''
                    
                    if not emp_id:
                        errors.append(f"Dòng {row_num}: Thiếu mã nhân viên")
                        skipped += 1
                        continue
                    
                    cur.execute("INSERT INTO staging_employee (employee_id, full_name, email, phone, batch_id) VALUES (%s, %s, %s, %s, %s)",
                               (emp_id, full_name, email, phone, batch_id))
                    inserted += 1
                    
                elif file_type == 'order':
                    if len(row) < 5:
                        errors.append(f"Dòng {row_num}: Thiếu cột (cần 5 cột, có {len(row)})")
                        skipped += 1
                        continue
                    
                    order_id = row[0].strip() if len(row) > 0 else ''
                    product_id = row[1].strip() if len(row) > 1 else ''
                    product_name = row[2].strip() if len(row) > 2 else ''
                    quantity = row[3].strip() if len(row) > 3 else '0'
                    price = row[4].strip() if len(row) > 4 else '0'
                    
                    if not order_id:
                        errors.append(f"Dòng {row_num}: Thiếu mã đơn hàng")
                        skipped += 1
                        continue
                    
                    cur.execute("INSERT INTO staging_order_detail (order_id, product_id, quantity, price, batch_id) VALUES (%s, %s, %s, %s, %s)",
                               (order_id, product_id, int(quantity), float(price), batch_id))
                    inserted += 1
                    
            except Exception as e:
                error_msg = f"Dòng {row_num}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                skipped += 1
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        result = {
            'success': True, 
            'rows': inserted, 
            'skipped': skipped,
            'filename': filename, 
            'batch_id': batch_id,
            'encoding': used_encoding
        }
        
        if errors:
            result['errors'] = errors[:10]  # Only return first 10 errors
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Upload error: {error_detail}")
        return jsonify({'success': False, 'error': str(e), 'detail': error_detail}), 500


@app.route('/api/process-etl', methods=['POST'])
def process_etl():
    try:
        data = request.json or {}
        clear_data = data.get('clearData', False)
        run_transform = data.get('runTransform', True)
        
        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)
        
        if clear_data:
            cur.execute("TRUNCATE staging_employee")
            cur.execute("TRUNCATE staging_order_detail")
            cur.execute("TRUNCATE main_employee")
            cur.execute("TRUNCATE main_order_detail")
            conn.commit()
        
        result = {'success': True}
        
        if run_transform:
            # Call the transform function directly
            cur.close()
            conn.close()
            
            # Call run_transform_v2 internally
            transform_result = run_transform_v2()
            transform_data = transform_result.get_json()
            
            if transform_data.get('success'):
                result['transferred'] = {
                    'employees': transform_data.get('employees', 0),
                    'orders': transform_data.get('orders', 0)
                }
                result['errors'] = transform_data.get('errors', 0)
            else:
                cur.close()
                conn.close()
                return jsonify({'success': False, 'error': transform_data.get('error', 'Transform failed')}), 500
        else:
            # Just count staging records
            cur.execute("SELECT COUNT(*) as cnt FROM staging_employee")
            emp_count = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM staging_order_detail")
            ord_count = cur.fetchone()['cnt']
            
            result['transferred'] = {
                'employees': emp_count,
                'orders': ord_count
            }
            result['errors'] = 0
            
            cur.close()
            conn.close()
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/list-csv')
def list_csv():
    try:
        files = {'employees': [], 'orders': []}
        if os.path.exists(UPLOAD_FOLDER):
            for f in os.listdir(UPLOAD_FOLDER):
                if f.endswith('.csv'):
                    filepath = os.path.join(UPLOAD_FOLDER, f)
                    size = os.path.getsize(filepath)
                    size_str = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/(1024*1024):.1f} MB"
                    
                    # Read first line to detect file type
                    try:
                        with open(filepath, 'r', encoding='utf-8') as csvfile:
                            first_line = csvfile.readline().lower()
                            if 'email' in first_line or 'phone' in first_line or 'employee' in first_line:
                                files['employees'].append({'name': f, 'size': size_str})
                            elif 'order' in first_line or 'product' in first_line or 'quantity' in first_line:
                                files['orders'].append({'name': f, 'size': size_str})
                            else:
                                # Fallback to filename
                                if 'employee' in f.lower() or 'emp' in f.lower() or 'nhanvien' in f.lower() or 'nv' in f.lower():
                                    files['employees'].append({'name': f, 'size': size_str})
                                elif 'order' in f.lower() or 'ord' in f.lower() or 'donhang' in f.lower() or 'dh' in f.lower():
                                    files['orders'].append({'name': f, 'size': size_str})
                    except:
                        pass
        
        return jsonify(files)
    except Exception as e:
        return jsonify({'employees': [], 'orders': [], 'error': str(e)})


def normalize_name(name):
    """Normalize Vietnamese name: proper case, remove extra spaces"""
    import re
    if not name:
        return name
    # Remove extra spaces
    name = ' '.join(name.split())
    # Title case for each word
    return name.title()

def normalize_phone(phone):
    """Normalize phone to E.164 format with +84 country code"""
    import re
    if not phone:
        return phone
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', phone)
    # If starts with 0, replace with +84
    if phone.startswith('0'):
        phone = '+84' + phone[1:]
    # If no country code, add +84
    elif not phone.startswith('84'):
        phone = '+84' + phone
    # If starts with 84, add +
    elif phone.startswith('84'):
        phone = '+' + phone
    return phone

def normalize_email(email):
    """Normalize email: lowercase, trim"""
    if not email:
        return email
    return email.strip().lower()

def send_email_notification(subject, body, to_email=None):
    """Send email notification for errors"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Email configuration from environment variables
        smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SMTP_USER', '')
        smtp_pass = os.environ.get('SMTP_PASSWORD', '')
        default_to = os.environ.get('SMTP_TO_EMAIL', 'admin@example.com')
        
        if not smtp_user or not smtp_pass:
            write_log_file('system', 'email', 'SMTP credentials not configured, skipping email', 'WARNING')
            return False
        
        recipient = to_email or default_to
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        write_log_file('system', 'email', f'Email sent to {recipient}: {subject}', 'INFO')
        return True
    
    except Exception as e:
        write_log_file('system', 'email', f'Failed to send email: {str(e)}', 'ERROR')
        return False

def check_and_notify_errors(cur, batch_id):
    """Check for errors and send notification if threshold exceeded"""
    try:
        # Count errors
        cur.execute("SELECT COUNT(*) as cnt FROM staging_employee WHERE validation_errors IS NOT NULL")
        emp_errors = cur.fetchone()['cnt']
        
        cur.execute("SELECT COUNT(*) as cnt FROM staging_order_detail WHERE validation_errors IS NOT NULL")
        ord_errors = cur.fetchone()['cnt']
        
        total_errors = emp_errors + ord_errors
        
        # Threshold for notification (configurable)
        error_threshold = int(os.environ.get('ERROR_NOTIFICATION_THRESHOLD', '10'))
        
        if total_errors >= error_threshold:
            subject = f'🚨 ETL Transform Alert - {total_errors} Errors Detected'
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d32f2f;">ETL Transform Error Report</h2>
                <p><strong>Batch ID:</strong> {batch_id}</p>
                <p><strong>Total Errors:</strong> {total_errors}</p>
                <ul>
                    <li><strong>Employee Errors:</strong> {emp_errors}</li>
                    <li><strong>Order Errors:</strong> {ord_errors}</li>
                </ul>
                <p>Please check the dashboard for details: <a href="http://localhost:8080">ETL Dashboard</a></p>
                <hr>
                <p style="color: #666; font-size: 12px;">This is an automated message from ETL System</p>
            </body>
            </html>
            """
            send_email_notification(subject, body)
            return True
        
        return False
    
    except Exception as e:
        write_log_file(batch_id, 'email', f'Error checking notifications: {str(e)}', 'ERROR')
        return False

def write_log_file(batch_id, entity_type, message, level='INFO'):
    """Write log entry to file"""
    import logging
    from datetime import datetime
    
    # Create logs directory if not exists
    log_dir = '/app/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Log filename: etl_YYYYMMDD.log
    log_file = os.path.join(log_dir, f"etl_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Configure logger
    logger = logging.getLogger('etl')
    if not logger.handlers:
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(batch_id)s] - %(entity_type)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # Log with context
    extra = {'batch_id': batch_id or 'N/A', 'entity_type': entity_type or 'N/A'}
    
    if level == 'ERROR':
        logger.error(message, extra=extra)
    elif level == 'WARNING':
        logger.warning(message, extra=extra)
    else:
        logger.info(message, extra=extra)

def log_transform_start(cur, batch_id, entity_type, total_records):
    """Log the start of a transform operation"""
    cur.execute("""
        INSERT INTO transform_log (batch_id, entity_type, total_records, status)
        VALUES (%s, %s, %s, 'processing')
    """, (batch_id, entity_type, total_records))
    
    # Write to log file
    write_log_file(batch_id, entity_type, f"Transform started: {total_records} records to process", 'INFO')
    
    return cur.lastrowid

def log_transform_complete(cur, log_id, valid_records, error_records, processing_time_ms, batch_id=None, entity_type=None):
    """Log the completion of a transform operation"""
    from datetime import datetime
    cur.execute("""
        UPDATE transform_log 
        SET valid_records = %s, error_records = %s, processing_time_ms = %s, 
            status = 'completed', completed_at = %s
        WHERE id = %s
    """, (valid_records, error_records, processing_time_ms, datetime.now(), log_id))
    
    # Write to log file
    if batch_id and entity_type:
        write_log_file(
            batch_id, 
            entity_type, 
            f"Transform completed: {valid_records} valid, {error_records} errors, {processing_time_ms}ms", 
            'INFO' if error_records == 0 else 'WARNING'
        )

def log_field_transformation(cur, batch_id, entity_type, entity_id, field_name, original_value, transformed_value, transform_rule):
    """Log individual field transformations for audit trail"""
    if original_value != transformed_value:
        cur.execute("""
            INSERT INTO data_transformation_audit 
            (batch_id, entity_type, entity_id, field_name, original_value, transformed_value, transform_rule)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (batch_id, entity_type, entity_id, field_name, str(original_value), str(transformed_value), transform_rule))

def update_daily_metrics(cur):
    """Update daily data quality metrics"""
    from datetime import date
    today = date.today()
    
    for entity_type in ['employee', 'order']:
        if entity_type == 'employee':
            table_staging = 'staging_employee'
            table_main = 'main_employee'
        else:
            table_staging = 'staging_order_detail'
            table_main = 'main_order_detail'
        
        # Count records
        cur.execute(f"SELECT COUNT(*) as cnt FROM {table_staging}")
        staging_count = cur.fetchone()['cnt']
        
        cur.execute(f"SELECT COUNT(*) as cnt FROM {table_main}")
        main_count = cur.fetchone()['cnt']
        
        cur.execute(f"SELECT COUNT(*) as cnt FROM {table_staging} WHERE validation_errors IS NOT NULL")
        error_count = cur.fetchone()['cnt']
        
        total_records = staging_count + main_count
        valid_records = main_count
        
        # Calculate rates
        valid_rate = (valid_records / total_records * 100) if total_records > 0 else 0
        error_rate = (error_count / total_records * 100) if total_records > 0 else 0
        
        # Insert or update metrics
        cur.execute("""
            INSERT INTO data_quality_metrics 
            (metric_date, entity_type, total_records, valid_records, error_records, valid_rate, error_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                total_records = %s,
                valid_records = %s,
                error_records = %s,
                valid_rate = %s,
                error_rate = %s
        """, (today, entity_type, total_records, valid_records, error_count, valid_rate, error_rate,
              total_records, valid_records, error_count, valid_rate, error_rate))

def get_active_rules_by_stage(cur, stage_number, entity_type):
    """Get active rules for a specific stage and entity type"""
    cur.execute("""
        SELECT r.rule_code, r.rule_name, r.rule_type, r.field_name, 
               r.validation_logic, r.error_message, r.severity
        FROM validation_rules r
        INNER JOIN rule_stage_mapping rsm ON r.id = rsm.rule_id
        INNER JOIN transform_stages s ON rsm.stage_id = s.id
        WHERE s.stage_number = %s 
          AND r.entity_type = %s 
          AND r.is_enabled = TRUE 
          AND s.is_enabled = TRUE
        ORDER BY rsm.execution_order
    """, (stage_number, entity_type))
    return cur.fetchall()

def apply_validation_rule(rule, field_value, record):
    """Apply a validation rule and return error if fails"""
    import re
    
    logic = rule['validation_logic']
    field_name = rule['field_name']
    
    if logic == 'not_empty':
        if not field_value or str(field_value).strip() == '':
            return {'field': field_name, 'message': rule['error_message']}
    
    elif logic.startswith('^') and logic.endswith('$'):  # Regex pattern
        if not re.match(logic, str(field_value)):
            return {'field': field_name, 'message': rule['error_message']}
    
    elif logic == 'positive_integer':
        try:
            if int(field_value) <= 0:
                return {'field': field_name, 'message': rule['error_message']}
        except:
            return {'field': field_name, 'message': rule['error_message']}
    
    elif logic == 'positive_number':
        try:
            if float(field_value) <= 0:
                return {'field': field_name, 'message': rule['error_message']}
        except:
            return {'field': field_name, 'message': rule['error_message']}
    
    return None  # No error

def apply_transformation_rule(rule, field_value):
    """Apply a transformation rule and return transformed value"""
    import re
    
    logic = rule['validation_logic']
    
    if logic == 'title_case':
        return normalize_name(field_value)
    
    elif logic == 'lowercase_trim':
        return normalize_email(field_value)
    
    elif logic == 'e164_format':
        return normalize_phone(field_value)
    
    elif logic == 'uppercase_trim':
        return str(field_value).strip().upper()
    
    elif logic == 'round_2_decimals':
        try:
            return round(float(field_value), 2)
        except:
            return field_value
    
    return field_value  # No transformation

@app.route('/api/run-transform-v2', methods=['POST'])
def run_transform_v2():
    """
    NEW: Two-Stage Rules-Based Transform
    Stage 1: Data Cleansing (Validation)
    Stage 2: Data Enrichment (Transformation)
    """
    import time
    start_time = time.time()
    
    try:
        import re
        import json
        from datetime import datetime
        
        batch_id = f"transform_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Try to connect to MySQL with proper error handling
        try:
            conn = get_mysql_connection()
        except mysql.connector.Error as db_err:
            print(f"Database connection error: {db_err}")
            return jsonify({
                'success': False, 
                'error': f'Không thể kết nối MySQL: {str(db_err)}'
            }), 500
            
        cur = conn.cursor(dictionary=True)
        
        # Validate that required tables exist
        try:
            cur.execute("SHOW TABLES LIKE 'validation_rules'")
            if not cur.fetchone():
                return jsonify({
                    'success': False,
                    'error': 'Bảng validation_rules chưa tồn tại. Vui lòng chạy script rules_configuration.sql'
                }), 500
        except mysql.connector.Error as e:
            return jsonify({
                'success': False,
                'error': f'Lỗi kiểm tra bảng validation_rules: {str(e)}'
            }), 500
        
        write_log_file(batch_id, 'system', '=== Starting Two-Stage Transform ===', 'INFO')
        
        employees_transferred = 0
        orders_transferred = 0
        employees_errors = 0
        orders_errors = 0
        
        # ====== STAGE 1: DATA CLEANSING (VALIDATION) ======
        write_log_file(batch_id, 'employee', 'Stage 1: Data Cleansing - Validation Started', 'INFO')
        
        # Get validation rules for Stage 1
        validation_rules_emp = get_active_rules_by_stage(cur, 1, 'employee')
        
        if not validation_rules_emp:
            write_log_file(batch_id, 'employee', 'WARNING: No validation rules found for Stage 1', 'WARNING')
        
        # Process Employees - Stage 1
        cur.execute("SELECT id, employee_id, full_name, email, phone, batch_id FROM staging_employee WHERE validation_errors IS NULL")
        staging_employees = cur.fetchall()
        total_employees = len(staging_employees)
        
        if total_employees > 0:
            emp_log_id = log_transform_start(cur, batch_id, 'employee', total_employees)
            conn.commit()
        
        for emp in staging_employees:
            errors = []
            emp_id = str(emp.get('id', ''))
            employee_id = str(emp.get('employee_id', ''))
            
            # Apply Stage 1 validation rules
            for rule in validation_rules_emp:
                field_value = emp.get(rule['field_name'], '')
                error = apply_validation_rule(rule, field_value, emp)
                if error:
                    errors.append(error)
            
            if errors:
                cur.execute("UPDATE staging_employee SET validation_errors = %s WHERE id = %s",
                           (json.dumps(errors, cls=DecimalEncoder), emp_id))
                employees_errors += 1
        
        conn.commit()
        write_log_file(batch_id, 'employee', f'Stage 1 Complete: {employees_errors} validation errors found', 
                      'WARNING' if employees_errors > 0 else 'INFO')
        
        # ====== STAGE 2: DATA ENRICHMENT (TRANSFORMATION) ======
        write_log_file(batch_id, 'employee', 'Stage 2: Data Enrichment - Transformation Started', 'INFO')
        
        # Get transformation rules for Stage 2
        transform_rules_emp = get_active_rules_by_stage(cur, 2, 'employee')
        
        # Re-query valid records for Stage 2
        cur.execute("SELECT id, employee_id, full_name, email, phone, batch_id FROM staging_employee WHERE validation_errors IS NULL")
        valid_employees = cur.fetchall()
        
        for emp in valid_employees:
            emp_id = str(emp.get('id', ''))
            employee_id = str(emp.get('employee_id', ''))
            source_batch_id = emp.get('batch_id', batch_id)
            
            # Store original data
            original_data = {
                'employee_id': employee_id,
                'full_name': str(emp.get('full_name', '')),
                'email': str(emp.get('email', '')),
                'phone': str(emp.get('phone', ''))
            }
            
            # Apply Stage 2 transformation rules
            transformed_data = dict(original_data)
            for rule in transform_rules_emp:
                field_name = rule['field_name']
                original_value = transformed_data.get(field_name, '')
                transformed_value = apply_transformation_rule(rule, original_value)
                
                if original_value != transformed_value:
                    transformed_data[field_name] = transformed_value
                    log_field_transformation(cur, batch_id, 'employee', employee_id, 
                                           field_name, original_value, transformed_value, rule['rule_code'])
            
            # Check duplicate
            cur.execute("SELECT COUNT(*) as cnt FROM main_employee WHERE employee_id = %s", (employee_id,))
            if cur.fetchone()['cnt'] == 0:
                cur.execute("""
                    INSERT INTO main_employee (employee_id, full_name, email, phone, batch_id, original_data) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (employee_id, transformed_data['full_name'], transformed_data['email'], 
                      transformed_data['phone'], source_batch_id, json.dumps(original_data)))
                employees_transferred += 1
            
            cur.execute("DELETE FROM staging_employee WHERE id = %s", (emp_id,))
        
        conn.commit()
        
        if total_employees > 0:
            processing_time = int((time.time() - start_time) * 1000)
            log_transform_complete(cur, emp_log_id, employees_transferred, employees_errors, processing_time, batch_id, 'employee')
            conn.commit()
        
        write_log_file(batch_id, 'employee', f'Stage 2 Complete: {employees_transferred} records transformed', 'INFO')
        
        # ====== ORDERS PROCESSING - STAGE 1 & 2 ======
        write_log_file(batch_id, 'order', 'Stage 1: Data Cleansing - Validation Started', 'INFO')
        
        # Get validation rules for Stage 1 - Orders
        validation_rules_ord = get_active_rules_by_stage(cur, 1, 'order')
        
        # Process Orders - Stage 1
        cur.execute("SELECT id, order_id, product_id, quantity, price, batch_id FROM staging_order_detail WHERE validation_errors IS NULL")
        staging_orders = cur.fetchall()
        total_orders = len(staging_orders)
        
        if total_orders > 0:
            ord_log_id = log_transform_start(cur, batch_id, 'order', total_orders)
            conn.commit()
        
        for order in staging_orders:
            errors = []
            order_rec_id = str(order.get('id', ''))
            order_id = str(order.get('order_id', ''))
            
            # Apply Stage 1 validation rules
            for rule in validation_rules_ord:
                field_value = order.get(rule['field_name'], '')
                error = apply_validation_rule(rule, field_value, order)
                if error:
                    errors.append(error)
            
            if errors:
                cur.execute("UPDATE staging_order_detail SET validation_errors = %s WHERE id = %s",
                           (json.dumps(errors, cls=DecimalEncoder), order_rec_id))
                orders_errors += 1
        
        conn.commit()
        write_log_file(batch_id, 'order', f'Stage 1 Complete: {orders_errors} validation errors found', 
                      'WARNING' if orders_errors > 0 else 'INFO')
        
        # ====== ORDERS - STAGE 2: DATA ENRICHMENT (TRANSFORMATION) ======
        write_log_file(batch_id, 'order', 'Stage 2: Data Enrichment - Transformation Started', 'INFO')
        
        # Get transformation rules for Stage 2 - Orders
        transform_rules_ord = get_active_rules_by_stage(cur, 2, 'order')
        
        # Re-query valid records for Stage 2
        cur.execute("SELECT id, order_id, product_id, quantity, price, batch_id FROM staging_order_detail WHERE validation_errors IS NULL")
        valid_orders = cur.fetchall()
        
        for order in valid_orders:
            order_rec_id = str(order.get('id', ''))
            order_id = str(order.get('order_id', ''))
            source_batch_id = order.get('batch_id', batch_id)
            
            # Store original data
            original_data = {
                'order_id': order_id,
                'product_id': str(order.get('product_id', '')),
                'quantity': int(order.get('quantity', 0)),
                'price': float(order.get('price', 0.0))
            }
            
            # Apply Stage 2 transformation rules
            transformed_data = dict(original_data)
            for rule in transform_rules_ord:
                field_name = rule['field_name']
                original_value = transformed_data.get(field_name, '')
                transformed_value = apply_transformation_rule(rule, original_value)
                
                if original_value != transformed_value:
                    transformed_data[field_name] = transformed_value
                    log_field_transformation(cur, batch_id, 'order', order_id, 
                                           field_name, str(original_value), str(transformed_value), rule['rule_code'])
            
            # Check duplicate
            cur.execute("SELECT COUNT(*) as cnt FROM main_order_detail WHERE order_id = %s", (order_id,))
            if cur.fetchone()['cnt'] == 0:
                cur.execute("""
                    INSERT INTO main_order_detail (order_id, product_id, quantity, price, batch_id, original_data) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (order_id, transformed_data['product_id'], transformed_data['quantity'], 
                      transformed_data['price'], source_batch_id, json.dumps(original_data, cls=DecimalEncoder)))
                orders_transferred += 1
            
            cur.execute("DELETE FROM staging_order_detail WHERE id = %s", (order_rec_id,))
        
        conn.commit()
        
        if total_orders > 0:
            processing_time = int((time.time() - start_time) * 1000)
            log_transform_complete(cur, ord_log_id, orders_transferred, orders_errors, processing_time, batch_id, 'order')
            conn.commit()
        
        write_log_file(batch_id, 'order', f'Stage 2 Complete: {orders_transferred} records transformed', 'INFO')
        
        conn.commit()
        
        # Count total errors
        cur.execute("SELECT COUNT(*) as cnt FROM staging_employee WHERE validation_errors IS NOT NULL")
        errors_emp = int(cur.fetchone()['cnt'])
        cur.execute("SELECT COUNT(*) as cnt FROM staging_order_detail WHERE validation_errors IS NOT NULL")
        errors_ord = int(cur.fetchone()['cnt'])
        
        # Update daily metrics
        update_daily_metrics(cur)
        
        # Check errors and send notifications if threshold exceeded
        check_and_notify_errors(cur, batch_id)
        
        conn.commit()
        
        cur.close()
        conn.close()
        
        total_processing_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'employees': int(employees_transferred),
            'orders': int(orders_transferred),
            'errors': int(errors_emp + errors_ord),
            'processing_time_ms': total_processing_time
        })
            
    except Exception as e:
        import traceback
        print("=" * 50)
        print("TRANSFORM ERROR:")
        traceback.print_exc()
        print("=" * 50)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/export/<entity>', methods=['GET'])
def export_csv(entity):
    """Export normalized data from main DB to CSV file"""
    import tempfile
    from datetime import datetime
    
    try:
        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)
        
        # Create temporary file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if entity == 'employee':
            # Export employees
            cur.execute("""
                SELECT employee_id as 'EmployeeID', 
                       full_name as 'FullName', 
                       email as 'Email', 
                       phone as 'Phone',
                       created_at as 'ProcessedDate'
                FROM main_employee 
                ORDER BY id DESC
            """)
            rows = cur.fetchall()
            filename = f'nhanvien_chuanhoa_{timestamp}.csv'
            
        elif entity == 'order':
            # Export orders
            cur.execute("""
                SELECT order_id as 'OrderID',
                       product_id as 'ProductID',
                       quantity as 'Quantity',
                       price as 'Price',
                       created_at as 'ProcessedDate'
                FROM main_order_detail 
                ORDER BY id DESC
            """)
            rows = cur.fetchall()
            filename = f'donhang_chuanhoa_{timestamp}.csv'
        else:
            return jsonify({'error': 'Loại dữ liệu không hợp lệ'}), 400
        
        cur.close()
        conn.close()
        
        if not rows:
            return jsonify({'error': 'No data to export'}), 404
        
        # Write to temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8-sig')
        
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temp_file.close()
        
        # Send file
        return send_file(
            temp_file.name,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/edit-errors/<entity>', methods=['GET'])
def edit_errors(entity):
    """Display form to edit error records in staging"""
    try:
        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)
        
        if entity == 'employee':
            cur.execute("""
                SELECT id, employee_id, full_name, email, phone, validation_errors
                FROM staging_employee 
                WHERE validation_errors IS NOT NULL
                ORDER BY id DESC
                LIMIT 50
            """)
            records = cur.fetchall()
            entity_name = 'Nhân Viên'
            fields = ['employee_id', 'full_name', 'email', 'phone']
            labels = ['Mã NV', 'Họ Tên', 'Email', 'Số Điện Thoại']
            
        elif entity == 'order':
            cur.execute("""
                SELECT id, order_id, product_id, quantity, price, validation_errors
                FROM staging_order_detail 
                WHERE validation_errors IS NOT NULL
                ORDER BY id DESC
                LIMIT 50
            """)
            records = cur.fetchall()
            entity_name = 'Đơn Hàng'
            fields = ['order_id', 'product_id', 'quantity', 'price']
            labels = ['Mã ĐH', 'Mã Sản Phẩm', 'Số Lượng', 'Giá']
        else:
            return "Loại dữ liệu không hợp lệ", 400
        
        cur.close()
        conn.close()
        
        # Convert Decimal to string for display
        for rec in records:
            for key, value in rec.items():
                if isinstance(value, Decimal):
                    rec[key] = float(value)
                elif value is not None:
                    rec[key] = str(value)
            # Parse errors
            if rec.get('validation_errors'):
                try:
                    rec['errors_list'] = json.loads(rec['validation_errors'])
                except:
                    rec['errors_list'] = []
        
        html = f"""
<!doctype html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sửa Lỗi {entity_name}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-4">
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2>✏️ Sửa Dữ Liệu Lỗi - {entity_name}</h2>
        <div>
            <a href="/" class="btn btn-secondary">← Về Dashboard</a>
            <button class="btn btn-success" onclick="saveAll()">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                  <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
                </svg>
                Lưu Tất Cả & Chạy Transform
            </button>
        </div>
    </div>
    
    <div id="alert" class="alert d-none"></div>
    
    <div class="table-responsive">
        <table class="table table-bordered table-hover">
            <thead class="table-warning">
                <tr>
                    <th style="width:50px">#</th>
                    {''.join(f'<th>{label}</th>' for label in labels)}
                    <th style="width:250px">Lỗi</th>
                    <th style="width:100px">Thao Tác</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for idx, rec in enumerate(records, 1):
            rec_id = rec['id']
            errors_html = '<br/>'.join([f"<small class='text-danger'>• {err.get('field', '')}: {err.get('message', '')}</small>" for err in rec.get('errors_list', [])])
            
            html += f"""
                <tr id="row-{rec_id}">
                    <td>{idx}</td>
"""
            for field in fields:
                value = rec.get(field, '')
                html += f"""<td><input type="text" class="form-control form-control-sm" id="{field}-{rec_id}" value="{value}"></td>"""
            
            html += f"""
                    <td>{errors_html}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="saveOne('{rec_id}', '{entity}')">Lưu</button>
                    </td>
                </tr>
"""
        
        html += f"""
            </tbody>
        </table>
    </div>
</div>

<script>
async function saveOne(id, entity) {{
    const fields = {fields};
    const data = {{}};
    
    fields.forEach(field => {{
        const input = document.getElementById(field + '-' + id);
        if(input) data[field] = input.value;
    }});
    
    try {{
        const response = await fetch('/api/update-error/' + entity + '/' + id, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(data)
        }});
        const result = await response.json();
        
        if(result.success) {{
            showAlert('success', 'Đã lưu record ID ' + id);
            document.getElementById('row-' + id).style.backgroundColor = '#d4edda';
        }} else {{
            showAlert('danger', 'Lỗi lưu dữ liệu: ' + result.error);
        }}
    }} catch(e) {{
        showAlert('danger', 'Lỗi kết nối: ' + e.message);
    }}
}}

async function saveAll() {{
    const rows = document.querySelectorAll('tbody tr');
    let saved = 0;
    
    for(let row of rows) {{
        const id = row.id.replace('row-', '');
        await saveOne(id, '{entity}');
        saved++;
    }}
    
    setTimeout(() => {{
        window.location.href = '/';
    }}, 1500);
}}

function showAlert(type, message) {{
    const alert = document.getElementById('alert');
    alert.className = 'alert alert-' + type;
    alert.textContent = message;
    alert.classList.remove('d-none');
    
    setTimeout(() => {{
        alert.classList.add('d-none');
    }}, 3000);
}}
</script>
</body>
</html>
"""
        
        return html
        
    except Exception as e:
        return f"Error: {{str(e)}}", 500


@app.route('/api/update-error/<entity>/<int:record_id>', methods=['POST'])
def update_error_record(entity, record_id):
    """Update a single error record in staging and clear validation_errors"""
    try:
        data = request.get_json()
        
        conn = get_mysql_connection()
        cur = conn.cursor()
        
        if entity == 'employee':
            cur.execute("""
                UPDATE staging_employee 
                SET employee_id = %s, full_name = %s, email = %s, phone = %s, validation_errors = NULL
                WHERE id = %s
            """, (data.get('employee_id'), data.get('full_name'), data.get('email'), data.get('phone'), record_id))
            
        elif entity == 'order':
            cur.execute("""
                UPDATE staging_order_detail 
                SET order_id = %s, product_id = %s, quantity = %s, price = %s, validation_errors = NULL
                WHERE id = %s
            """, (data.get('order_id'), data.get('product_id'), data.get('quantity'), data.get('price'), record_id))
        else:
            return jsonify({{'success': False, 'error': 'Loại dữ liệu không hợp lệ'}}), 400
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({{'success': True}})
        
    except Exception as e:
        return jsonify({{'success': False, 'error': str(e)}}), 500


@app.route('/export-errors/<entity>', methods=['GET'])
def export_errors(entity):
    """Export error records from staging to CSV for correction"""
    import tempfile
    from datetime import datetime
    
    try:
        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if entity == 'employee':
            # Export error employees with error details
            cur.execute("""
                SELECT employee_id as 'EmployeeID',
                       full_name as 'FullName',
                       email as 'Email',
                       phone as 'Phone',
                       validation_errors as 'Errors'
                FROM staging_employee 
                WHERE validation_errors IS NOT NULL
                ORDER BY id DESC
            """)
            rows = cur.fetchall()
            filename = f'nhanvien_loi_{timestamp}.csv'
            
        elif entity == 'order':
            # Export error orders with error details
            cur.execute("""
                SELECT order_id as 'OrderID',
                       product_id as 'ProductID',
                       quantity as 'Quantity',
                       price as 'Price',
                       validation_errors as 'Errors'
                FROM staging_order_detail 
                WHERE validation_errors IS NOT NULL
                ORDER BY id DESC
            """)
            rows = cur.fetchall()
            filename = f'donhang_loi_{timestamp}.csv'
        else:
            return jsonify({'error': 'Loại dữ liệu không hợp lệ'}), 400
        
        cur.close()
        conn.close()
        
        if not rows:
            return jsonify({'error': 'Không có dữ liệu lỗi để export'}), 404
        
        # Format errors column to readable text
        for row in rows:
            if row.get('Errors'):
                try:
                    errors_obj = json.loads(row['Errors']) if isinstance(row['Errors'], str) else row['Errors']
                    error_msgs = [f"{e.get('field', '?')}: {e.get('message', '?')}" for e in errors_obj]
                    row['Errors'] = ' | '.join(error_msgs)
                except:
                    row['Errors'] = str(row['Errors'])
        
        # Write to CSV
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8-sig')
        
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-logs')
def download_logs():
    """Download ETL log files"""
    try:
        from datetime import datetime
        import zipfile
        
        log_dir = '/app/logs'
        if not os.path.exists(log_dir):
            return jsonify({'error': 'Không có log files'}), 404
        
        # Get date parameter or default to today
        date_str = request.args.get('date', datetime.now().strftime('%Y%m%d'))
        log_file = os.path.join(log_dir, f"etl_{date_str}.log")
        
        if not os.path.exists(log_file):
            return jsonify({'error': f'Log file cho ngày {date_str} không tồn tại'}), 404
        
        return send_file(
            log_file,
            mimetype='text/plain',
            as_attachment=True,
            download_name=f'etl_log_{date_str}.log'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-logs')
def list_logs():
    """List all available log files"""
    try:
        log_dir = '/app/logs'
        if not os.path.exists(log_dir):
            return jsonify({'files': []})
        
        files = []
        for f in os.listdir(log_dir):
            if f.endswith('.log'):
                filepath = os.path.join(log_dir, f)
                size = os.path.getsize(filepath)
                size_str = f"{size/1024:.1f} KB" if size < 1024*1024 else f"{size/(1024*1024):.1f} MB"
                mtime = os.path.getmtime(filepath)
                from datetime import datetime
                modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                files.append({
                    'name': f,
                    'size': size_str,
                    'modified': modified,
                    'date': f.replace('etl_', '').replace('.log', '')
                })
        
        # Sort by date descending
        files.sort(key=lambda x: x['date'], reverse=True)
        return jsonify({'files': files})
    
    except Exception as e:
        return jsonify({'files': [], 'error': str(e)})

@app.route('/rules')
def rules_page():
    """Serve the Rules Configuration page"""
    return send_from_directory('.', 'rules.html')

@app.route('/api/validation-rules')
def get_validation_rules():
    """Get all validation rules"""
    try:
        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT r.*, 
                   GROUP_CONCAT(DISTINCT s.stage_number ORDER BY s.stage_number) as stage_number
            FROM validation_rules r
            LEFT JOIN rule_stage_mapping rsm ON r.id = rsm.rule_id
            LEFT JOIN transform_stages s ON rsm.stage_id = s.id
            GROUP BY r.id
            ORDER BY r.entity_type, r.execution_order
        """)
        rules = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify(rules)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rule-detail/<rule_code>')
def get_rule_detail(rule_code):
    """Get detailed info about a specific rule"""
    try:
        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("SELECT * FROM validation_rules WHERE rule_code = %s", (rule_code,))
        rule = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        return jsonify(rule)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/toggle-rule', methods=['POST'])
def toggle_rule():
    """Enable/disable a rule"""
    try:
        data = request.json
        rule_code = data.get('rule_code')
        enabled = data.get('enabled', True)
        
        conn = get_mysql_connection()
        cur = conn.cursor()
        
        cur.execute("UPDATE validation_rules SET is_enabled = %s WHERE rule_code = %s", (enabled, rule_code))
        conn.commit()
        
        cur.close()
        conn.close()
        
        # Log the change
        write_log_file('system', 'rules', f"Rule {rule_code} {'enabled' if enabled else 'disabled'}", 'INFO')
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/history')
def history_page():
    """Serve the Transform History & Audit Trail page"""
    return send_from_directory('.', 'history.html')

@app.route('/api/transform-history')
def get_transform_history():
    """Get transform history log"""
    try:
        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)
        
        # Get recent transform logs (last 50)
        cur.execute("""
            SELECT id, batch_id, entity_type, total_records, valid_records, error_records,
                   processing_time_ms, status, error_message, created_at, completed_at
            FROM transform_log
            ORDER BY created_at DESC
            LIMIT 50
        """)
        logs = cur.fetchall()
        
        # Convert datetime to string
        for log in logs:
            if log.get('created_at'):
                log['created_at'] = log['created_at'].isoformat()
            if log.get('completed_at'):
                log['completed_at'] = log['completed_at'].isoformat()
        
        cur.close()
        conn.close()
        
        return jsonify(logs)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/audit-trail')
def get_audit_trail():
    """Get transformation audit trail"""
    try:
        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)
        
        batch_id = request.args.get('batch_id')
        limit = request.args.get('limit', 100)
        
        if batch_id:
            # Get audit trail for specific batch
            cur.execute("""
                SELECT batch_id, entity_type, entity_id, field_name, 
                       original_value, transformed_value, transform_rule, transformed_at
                FROM data_transformation_audit
                WHERE batch_id = %s
                ORDER BY transformed_at DESC
                LIMIT %s
            """, (batch_id, int(limit)))
        else:
            # Get recent audit trail
            cur.execute("""
                SELECT batch_id, entity_type, entity_id, field_name, 
                       original_value, transformed_value, transform_rule, transformed_at
                FROM data_transformation_audit
                ORDER BY transformed_at DESC
                LIMIT %s
            """, (int(limit),))
        
        audits = cur.fetchall()
        
        # Convert datetime to string
        for audit in audits:
            if audit.get('transformed_at'):
                audit['transformed_at'] = audit['transformed_at'].isoformat()
        
        cur.close()
        conn.close()
        
        return jsonify(audits)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quality-metrics')
def get_quality_metrics():
    """Get data quality metrics"""
    try:
        conn = get_mysql_connection()
        cur = conn.cursor(dictionary=True)
        
        days = request.args.get('days', 7)
        
        # Get metrics for last N days
        cur.execute("""
            SELECT metric_date, entity_type, total_records, valid_records, error_records,
                   valid_rate, error_rate, duplicate_count, duplicate_rate, completeness_score
            FROM data_quality_metrics
            WHERE metric_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY metric_date DESC, entity_type
        """, (int(days),))
        
        metrics = cur.fetchall()
        
        # Convert date to string
        for metric in metrics:
            if metric.get('metric_date'):
                metric['metric_date'] = metric['metric_date'].isoformat()
        
        cur.close()
        conn.close()
        
        return jsonify(metrics)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))


