## 📦 Materi: Install PostgreSQL dengan Docker

### 🎯 **Tujuan**
- Menjalankan database PostgreSQL secara cepat dan praktis menggunakan Docker.
- Mengatur `username = postgres` dan `password = example`.

---

## 🐳 **Langkah-langkah Install PostgreSQL via Docker**

### ✅ 1. **Pastikan Docker Terinstal**

Periksa apakah Docker sudah terinstal dengan:
```bash
docker --version
```

Jika belum, silakan instal Docker dari: https://docs.docker.com/get-docker/

---

### ✅ 2. **Jalankan PostgreSQL dengan Docker**

Gunakan perintah berikut di terminal:

```bash
docker run --name pg-docker \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=example \
  -e POSTGRES_DB=ai-gcc \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  -d postgres:latest
```

#### 📌 Penjelasan:
| Opsi | Fungsi |
|------|--------|
| `--name pg-docker` | Nama container |
| `-e POSTGRES_USER=postgres` | Username PostgreSQL |
| `-e POSTGRES_PASSWORD=example` | Password PostgreSQL |
| `-e POSTGRES_DB=ai-gcc` | Nama database default |
| `-p 5432:5432` | Mengekspos port PostgreSQL |
| `-v pgdata:/var/lib/postgresql/data` | Volume penyimpanan data |
| `-d postgres:latest` | Gunakan versi terbaru dan jalankan sebagai daemon |

---

### ✅ 3. **Cek Status Container**
```bash
docker ps
```

Untuk melihat log:
```bash
docker logs pg-docker
```

---

### ✅ 4. **Akses PostgreSQL** (Optional)

Gunakan tools seperti:
- [DBeaver](https://dbeaver.io/)
- [pgAdmin](https://www.pgadmin.org/)
- Atau gunakan CLI:

```bash
docker exec -it pg-docker psql -U postgres -d ai-gcc
```

---

## 🧽 (Opsional) Menghapus Container
Jika ingin menghapus container:

```bash
docker stop pg-docker
docker rm pg-docker
docker volume rm pgdata
```

---

## 📚 Kesimpulan

Dengan Docker, kamu bisa menjalankan PostgreSQL tanpa perlu instalasi manual. Proses ini sangat cocok untuk pengembangan lokal maupun testing.

Kalau kamu butuh file `docker-compose.yml` versi lengkapnya, tinggal bilang aja ya! 🎯