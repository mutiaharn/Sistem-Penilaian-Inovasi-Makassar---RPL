"""
Skema & domain penilaian indikator (Tahap 1 AI).

Isi modul yang direncanakan:
    rules.py      - pemeriksaan deterministik atas metadata hasil IDP
    llm_judge.py  - verifikasi klaim parameter memakai kutipan bukti (Gemini)
    engine.py     - orkestrator: aturan dulu, LLM bila perlu, tandai kegagalan

Kontrak yang harus dipenuhi engine (lihat docs/ARCHITECTURE.md §3.3):

    engine.assess(innovation_id, indicator_id, klaim_parameter_id, evidences)
        -> list[ParameterAssessmentDraft]

Aturan penting: engine hanya boleh menulis ke tabel `parameter_assessments`,
tidak pernah ke `human_decisions`.

TODO (Tahap 1 pada docs/ROADMAP.md): implementasi ketiga modul di atas.
"""
