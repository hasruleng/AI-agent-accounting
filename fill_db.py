from sqlalchemy.orm import sessionmaker
from init_db import engine, KodeAkuntansiTable, ObjectTable, JurnalUmumTable
from datetime import datetime
from decimal import Decimal
import random

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Insert Kode Akuntansi Data, termasuk akun baru untuk HPP (520)
kode_akuntansi_data = [
    (101, "Kas"),
    (102, "Persediaan barang dagang"),
    (103, "Piutang usaha"),
    (104, "Penyisihan piutang usaha"),
    (105, "Wesel tagih"),
    (106, "Perlengkapan"),
    (107, "Iklan dibayar dimuka"),
    (108, "Sewa dibayar dimuka"),
    (109, "Asuransi dibayar dimuka"),
    (111, "Investasi saham"),
    (112, "Investasi obligasi"),
    (121, "Peralatan"),
    (122, "Akumulasi penyusutan peralatan"),
    (123, "Kendaraan"),
    (124, "Akumulasi penyusutan kendaraan"),
    (125, "Gedung"),
    (126, "Akumulasi penyusutan gedung"),
    (127, "Tanah"),
    (131, "Hak paten"),
    (132, "Hak cipta"),
    (133, "Merk dagang"),
    (134, "Goodwill"),
    (135, "Franchise"),
    (141, "Mesin yang tidak digunakan"),
    (142, "Beban yang ditangguhkan"),
    (143, "Piutang kepada pemegang saham"),
    (144, "Beban emisi saham"),
    (201, "Utang usaha"),
    (202, "Utang wesel"),
    (203, "Beban yang masih harus dibayar"),
    (204, "Utang gaji"),
    (205, "Utang sewa gedung"),
    (206, "Utang pajak penghasilan"),
    (211, "Utang hipotek"),
    (212, "Utang obligasi"),
    (213, "Utang gadai"),
    (301, "Modal/ekuitas pemilik"),
    (302, "Prive"),
    (401, "Pendapatan usaha"),
    (410, "Pendapatan di luar usaha"),
    (501, "Beban gaji toko"),
    (502, "Beban gaji kantor"),
    (503, "Beban sewa gedung"),
    (504, "Beban penyesuaian piutang"),
    (505, "Beban perlengkapan kantor"),
    (506, "Beban perlengkapan toko"),
    (507, "Beban iklan"),
    (508, "Beban penyusutan peralatan"),
    (509, "Beban penyusutan"),
    (510, "Beban bunga"),
    (511, "Beban lain-lain"),
    (520, "Harga Pokok Penjualan")  # Akun untuk pengakuan HPP
]

for kode_id, nama_kode in kode_akuntansi_data:
    session.add(KodeAkuntansiTable(kode_id=kode_id, nama_kode=nama_kode))

# Insert Object Data
object_data = [
    ("PT BANGUN ISTIMEWA", "customer"),
    ("PT BANGUN SETIA SEJAHTERA", "customer"),
    ("PT INFORMASI INDONESIA", "supplier"),
    ("PT KOMPUTER KOMPUTA", "supplier")
]

object_map = {}
for object_name, jenis_object in object_data:
    obj = ObjectTable(object_name=object_name, jenis_object=jenis_object)
    session.add(obj)
    session.flush()
    object_map[object_name] = obj.object_id

session.commit()

# Insert Jurnal Umum Data
jurnal_entries = [
    # Transaksi Modal
    ("Modal Awal", 301, None, "Setoran Modal", Decimal("0.00"), Decimal("100000000.00")),
    ("Modal Awal", 101, None, "Setoran Modal", Decimal("100000000.00"), Decimal("0.00"))
]

# === Variabel untuk Pembelian dan Penjualan ===
# Pembelian supplier: 10 unit stock
purchased_stock_qty = 10
unit_purchase_cost = Decimal("200000.00")  # biaya per unit
total_purchase_cost = unit_purchase_cost * purchased_stock_qty

# Penjualan: 3 transaksi, masing-masing 1 unit
n_sales = 3
sale_unit_revenue = Decimal("300000.00")  # pendapatan per unit
sale_unit_cost = unit_purchase_cost         # HPP per unit (sama dengan biaya per unit)

# === Transaksi Pembelian dari Supplier (langsung dibayar) ===
jurnal_entries.extend([
    ("Pembelian ke Supplier", 102, object_map["PT INFORMASI INDONESIA"],
     f"Pembelian Barang - Persediaan bertambah ({purchased_stock_qty} unit)",
     total_purchase_cost, Decimal("0.00")),
    ("Pembelian ke Supplier", 101, object_map["PT INFORMASI INDONESIA"],
     f"Pembelian Barang - Kas berkurang ({purchased_stock_qty} unit)",
     Decimal("0.00"), total_purchase_cost)
])

# === Transaksi Penjualan: 3 kali penjualan, masing-masing 1 unit ===
for i in range(1, n_sales + 1):
    customer_id = object_map["PT BANGUN ISTIMEWA"]
    # Pencatatan penjualan (revenue)
    jurnal_entries.extend([
        (f"Penjualan Barang {i}", 101, customer_id,
         f"Penjualan Barang - Kas diterima (1 unit, transaksi {i})",
         sale_unit_revenue, Decimal("0.00")),
        (f"Penjualan Barang {i}", 401, customer_id,
         f"Penjualan Barang - Pendapatan usaha (1 unit, transaksi {i})",
         Decimal("0.00"), sale_unit_revenue),
        # Pengakuan HPP: mengakui beban dan mengurangi persediaan
        (f"Penjualan Barang {i} - HPP", 520, customer_id,
         f"HPP - Beban (1 unit, transaksi {i})",
         sale_unit_cost, Decimal("0.00")),
        (f"Penjualan Barang {i} - Persediaan", 102, customer_id,
         f"Pengurangan Persediaan Barang Dagang (1 unit, transaksi {i})",
         Decimal("0.00"), sale_unit_cost)
    ])

# === Contoh transaksi Beban Iklan ===
jurnal_entries.extend([
    ("Beban Iklan", 507, None, "Biaya Iklan", Decimal("500000.00"), Decimal("0.00")),
    ("Beban Iklan", 101, None, "Biaya Iklan", Decimal("0.00"), Decimal("500000.00"))
])

# Masukkan semua transaksi ke database
for nama_transaksi, kode_akuntansi, object_id, keterangan, debit, kredit in jurnal_entries:
    session.add(JurnalUmumTable(
        nama_transaksi=nama_transaksi,
        kode_akuntansi=kode_akuntansi,
        object_id=object_id,
        keterangan=keterangan,
        debit=debit,
        kredit=kredit,
        created_at=datetime.utcnow()
    ))

session.commit()
session.close()

print("Database filled with initial data successfully.")
