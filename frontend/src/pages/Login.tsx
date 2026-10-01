import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

type RoleType = "verifikator" | "admin";

export default function Login() {
  const [role, setRole] = useState<RoleType>("verifikator");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  const handleRoleChange = (selectedRole: RoleType) => {
    setRole(selectedRole);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Login data:", { role, username, password, rememberMe });
  };

  return (
    <main className="min-h-screen w-full flex bg-white text-slate-800 font-sans antialiased">
      
      {/* ================= PANEL KIRI: FORMULIR LOGIN ================= */}
      <section className="w-full lg:w-1/2 flex flex-col justify-center px-10 sm:px-16 md:px-24 lg:px-20 xl:px-28 py-10">
        <div className="w-full max-w-[420px] mx-auto">
          
          {/* Header Judul */}
          <div className="mb-7">
            <h1 className="font-poppins text-[28px] font-extrabold text-slate-900 tracking-tight leading-snug">
              Masuk ke Sistem
            </h1>
            <p className="font-sans text-[12px] text-slate-400 mt-1 font-normal">
              Gunakan akun internal BRIDA Anda untuk mengakses portal.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            
            {/* Pilihan Peran Akses */}
            <div>
              <label className="block font-sans text-[10px] font-bold text-slate-300 tracking-wider uppercase mb-2">
                PILIH PERAN AKSES:
              </label>
              
              <div className="grid grid-cols-2 gap-2.5">
                {/* Tombol Verifikator BRIDA */}
                <button
                  type="button"
                  onClick={() => handleRoleChange("verifikator")}
                  className={`border rounded-xl p-2.5 flex items-start gap-2.5 transition-all text-left ${
                    role === "verifikator"
                      ? "border-[#A61F1B] bg-[#A61F1B] shadow-sm text-white"
                      : "border-slate-200 bg-white hover:border-slate-300 text-slate-700"
                  }`}
                >
                  <div className={`mt-0.5 shrink-0 ${role === "verifikator" ? "text-white" : "text-slate-400"}`}>
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                      <path d="m9 12 2 2 4-4"/>
                    </svg>
                  </div>
                  <div>
                    <p className={`font-poppins text-[12px] font-bold leading-tight ${role === "verifikator" ? "text-white" : "text-slate-800"}`}>
                      Verifikator BRIDA
                    </p>
                    <p className={`font-sans text-[9px] mt-0.5 leading-tight ${role === "verifikator" ? "text-red-100" : "text-slate-400"}`}>
                      Penilaian &amp; Pengesah Berkas Usulan
                    </p>
                  </div>
                </button>

                {/* Tombol Administrator */}
                <button
                  type="button"
                  onClick={() => handleRoleChange("admin")}
                  className={`border rounded-xl p-2.5 flex items-start gap-2.5 transition-all text-left ${
                    role === "admin"
                      ? "border-[#A61F1B] bg-[#A61F1B] shadow-sm text-white"
                      : "border-slate-200 bg-white hover:border-slate-300 text-slate-700"
                  }`}
                >
                  <div className={`mt-0.5 shrink-0 ${role === "admin" ? "text-white" : "text-slate-400"}`}>
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="3"/>
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                    </svg>
                  </div>
                  <div>
                    <p className={`font-poppins text-[12px] font-bold leading-tight ${role === "admin" ? "text-white" : "text-slate-800"}`}>
                      Administrator
                    </p>
                    <p className={`font-sans text-[9px] mt-0.5 leading-tight ${role === "admin" ? "text-red-100" : "text-slate-400"}`}>
                      Pengelola Sistem &amp; Manajemen Data
                    </p>
                  </div>
                </button>
              </div>
            </div>

            {/* Input NIP / Username */}
            <div>
              <label className="block font-poppins text-[12px] font-bold text-slate-900 mb-1.5">
                Nama Pengguna / NIP
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Masukkan email atau Username"
                className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-lg text-[13px] font-sans text-slate-800 placeholder-slate-300 focus:outline-none focus:border-[#A61F1B] transition-colors"
                required
              />
            </div>

            {/* Input Kata Sandi */}
            <div>
              <label className="block font-poppins text-[12px] font-bold text-slate-900 mb-1.5">
                Kata Sandi
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Masukkan Password"
                  className="w-full pl-3.5 pr-10 py-2.5 bg-white border border-slate-200 rounded-lg text-[13px] font-sans text-slate-800 placeholder-slate-300 focus:outline-none focus:border-[#A61F1B] transition-colors"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Baris Ingat Akses Saya & Lupa Password */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-3.5 h-3.5 rounded border-slate-300 text-[#A61F1B] focus:ring-[#A61F1B]"
                />
                <span className="font-sans text-[11px] text-slate-600">Ingat Akses Saya</span>
              </label>

              <a href="#lupa-password" className="font-sans text-[11px] font-semibold text-[#A61F1B] hover:underline">
                Lupa Password?
              </a>
            </div>

            {/* Tombol Masuk ke Sistem */}
            <div className="pt-2">
              <button
                type="submit"
                className="w-full py-2.5 bg-[#A61F1B] hover:bg-[#8e1915] active:bg-[#781310] text-white rounded-lg text-[13px] font-poppins font-semibold shadow-sm transition-all duration-150"
              >
                Masuk ke Sistem
              </button>
            </div>

          </form>
        </div>
      </section>


{/* ================= PANEL KANAN: FOTO & BRANDING ================= */}
      <section className="hidden lg:flex lg:w-1/2 relative bg-[#A61F1B] items-center justify-center p-12 xl:p-16 overflow-hidden">
        
        {/* Gambar Latar Hasil Ekspor Figma */}
        <img
          src="/images/bg-kantor.png"
          alt="Latar Belakang BRIDA"
          className="absolute inset-0 w-full h-full object-cover select-none pointer-events-none"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            if (!target.src.endsWith(".jpg")) {
              target.src = "/images/bg-kantor.jpg";
            }
          }}
        />

        {/* Logo BRIDA Pojok Kanan Atas (Lebih Besar & Proporsional) */}
        <div className="absolute top-10 right-12 z-20 flex items-center">
          <img
            src="/images/logo-brida-white.png"
            alt="Logo BRIDA Kota Makassar"
            className="h-34 xl:h-36 w-auto object-contain drop-shadow-md"
          />
        </div>

        {/* Blok Teks Utama: Berada di Posisi Tengah Layar */}
        <div className="relative z-10 w-full max-w-xl">
          <h2 className="font-poppins text-3xl xl:text-4xl font-extrabold text-white leading-[1.2] tracking-tight">
            Sistem Verifikasi &amp; <br />
            Penilaian Berkas Inovasi
          </h2>
          <p className="font-sans text-[13px] xl:text-[14px] text-white/90 mt-5 leading-relaxed font-normal max-w-md">
            Platform internal tim verifikator BRIDA untuk menelaah dokumen naskah dinas daerah berbasis OCR cerdas dan pengesahan berjenjang
          </p>
        </div>

      </section>

    </main>
  );
}