# Instruksi untuk membangun container frontend

# Gunakan base image Node.js versi 20
FROM node:20-alpine

# Set direktori kerja di dalam container
WORKDIR /app

# Salin package.json dan package-lock.json terlebih dahulu
# Ini memanfaatkan cache Docker agar 'npm install' tidak dijalankan setiap kali ada perubahan kode
COPY package*.json ./

# Instal semua dependensi
RUN npm install

# Salin sisa kode proyek
COPY . .

# Beri tahu Docker bahwa container akan menggunakan port 5173
EXPOSE 5173

# Perintah default untuk menjalankan server pengembangan Vite
# Opsi '--host' penting agar bisa diakses dari luar container
CMD ["npm", "run", "dev", "--", "--host"]
