from flask import Flask, render_template, jsonify, request, send_file, redirect, session
import pymysql
import pandas as pd

app = Flask(__name__)
app.secret_key = 'admin123'  # Change this to a random secret key
db = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="fatih_market",
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

def get_db():
    return db

def ambil_semua_barang():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT kode_barang, nama_barang, kategori, stok
        FROM barang
        ORDER BY kode_barang
    """)

    rows = cur.fetchall()
    data = []

    for r in rows:
        cur.execute(
            "SELECT IFNULL(SUM(jumlah),0) total FROM barang_masuk WHERE kode_barang=%s",
            (r["kode_barang"],)
        )
        masuk = cur.fetchone()["total"]

        cur.execute(
            "SELECT IFNULL(SUM(jumlah),0) total FROM barang_keluar WHERE kode_barang=%s",
            (r["kode_barang"],)
        )
        keluar = cur.fetchone()["total"]

        data.append({
            "kode": r["kode_barang"],
            "nama": r["nama_barang"],
            "kategori": r["kategori"],
            "stok_awal": int(r["stok"]),
            "masuk": int(masuk),
            "keluar": int(keluar)
        })

    cur.close()
    return data


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["login"] = True
            return redirect("/home")

    return render_template("login.html")


@app.route("/home")
def home():
    if "login" not in session:
        return redirect("/")
    return render_template("index.html")


@app.route("/api/stok", methods=["GET"])
def api_stok():
    return jsonify(ambil_semua_barang())


@app.route("/api/stok", methods=["POST"])
def simpan():
    return jsonify({
        "status": "ok",
        "pesan": "Endpoint POST belum dihubungkan ke MySQL."
    })


@app.route("/download_excel")
def download_excel():

    data = ambil_semua_barang()

    for item in data:
        item["stok_akhir"] = (
            item["stok_awal"] +
            item["masuk"] -
            item["keluar"]
        )

    df = pd.DataFrame(data)

    nama_file = "Data_Persediaan_Fatih_Market.xlsx"

    df.rename(columns={
        "kode": "Kode Barang",
        "nama": "Nama Barang",
        "kategori": "Kategori",
        "stok_awal": "Stok Awal",
        "masuk": "Barang Masuk",
        "keluar": "Barang Keluar",
        "stok_akhir": "Stok Akhir"
    }, inplace=True)

    df.to_excel(nama_file, index=False)

    return send_file(
        nama_file,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)