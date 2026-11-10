/**
 * Smart Complaint System (SCS) - Kota Bandar Lampung
 * Frontend Application Core Logic
 * 
 * Compliant with PRD v1.0 (10 November 2026)
 * Footer Requirement: Copyright©2026 by Nama Mahasiswa dan Dr. Erliyan Redy Susanto, M.Kom
 */

const SCS = {
  apiBase: '/api/v1',
  currentUser: null,
  activeView: 'home',
  mapHome: null,
  mapCreate: null,
  mapDetail: null,
  createMarker: null,
  homeMarkers: [],
  categories: [],
  departments: [],
  allReports: [],
  charts: {},

  // 1. Initialization
  async init() {
    console.log("Initializing Smart Complaint System (SCS)...");
    await this.checkAuth();
    await this.loadMeta();
    this.setupEventListeners();
    this.navigate('home');
    this.loadHomeData();
  },

  // 2. Authentication
  async checkAuth() {
    const token = localStorage.getItem('scs_token');
    if (!token) {
      this.currentUser = null;
      this.renderUserUI();
      return;
    }

    try {
      const res = await fetch(`${this.apiBase}/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        this.currentUser = data.user;
      } else {
        localStorage.removeItem('scs_token');
        this.currentUser = null;
      }
    } catch (e) {
      console.warn("Auth check failed:", e);
      this.currentUser = null;
    }
    this.renderUserUI();
  },

  renderUserUI() {
    const userBar = document.getElementById('user-profile-bar');
    const guestBar = document.getElementById('guest-auth-bar');
    const navAdmin = document.getElementById('nav-admin-link');
    const navField = document.getElementById('nav-field-link');
    const navAnalytics = document.getElementById('nav-analytics-link');
    const navSuper = document.getElementById('nav-superadmin-link');
    const navCitizen = document.getElementById('nav-citizen-link');
    const bannerRole = document.getElementById('active-role-pill');

    if (this.currentUser) {
      guestBar.classList.add('hidden');
      userBar.classList.remove('hidden');
      userBar.classList.add('flex');

      document.getElementById('user-display-name').textContent = this.currentUser.name;
      const roleStr = this.currentUser.roles.join(', ');
      document.getElementById('user-display-role').textContent = roleStr;
      bannerRole.textContent = roleStr;

      // Conditional Nav Links based on RBAC (FR-02)
      const roles = this.currentUser.roles;
      const isAdmin = roles.includes('ADMIN') || roles.includes('SUPERADMIN');
      const isField = roles.includes('PETUGAS') || roles.includes('ADMIN') || roles.includes('SUPERADMIN');
      const isLeader = roles.includes('PIMPINAN') || roles.includes('ADMIN') || roles.includes('SUPERADMIN');
      const isSuper = roles.includes('SUPERADMIN');

      navAdmin.classList.toggle('hidden', !isAdmin);
      navField.classList.toggle('hidden', !isField);
      navAnalytics.classList.toggle('hidden', !isLeader);
      navSuper.classList.toggle('hidden', !isSuper);
      navCitizen.classList.remove('hidden');

      this.fetchNotifications();
    } else {
      guestBar.classList.remove('hidden');
      userBar.classList.add('hidden');
      userBar.classList.remove('flex');
      navAdmin.classList.add('hidden');
      navField.classList.add('hidden');
      navAnalytics.classList.add('hidden');
      navSuper.classList.add('hidden');
      navCitizen.classList.add('hidden');
      bannerRole.textContent = 'Tamu (Warga Publik)';
    }
  },

  async login(email, password) {
    try {
      const res = await fetch(`${this.apiBase}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (data.success) {
        localStorage.setItem('scs_token', data.token);
        this.currentUser = data.user;
        this.renderUserUI();
        this.closeModal('modal-auth');
        this.showToast('success', `Selamat datang kembali, ${data.user.name}!`);
        this.navigate(this.getDefaultViewForRoles(data.user.roles));
      } else {
        this.showToast('error', data.error || 'Login gagal');
      }
    } catch (e) {
      this.showToast('error', 'Gagal menghubungi server');
    }
  },

  async register(full_name, email, password, phone, nik) {
    try {
      const res = await fetch(`${this.apiBase}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name, email, password, phone, nik })
      });
      const data = await res.json();
      if (data.success) {
        localStorage.setItem('scs_token', data.token);
        this.currentUser = data.user;
        this.renderUserUI();
        this.closeModal('modal-auth');
        this.showToast('success', 'Akun warga berhasil didaftarkan! Selamat datang di SCS Bandar Lampung.');
        this.navigate('create-report');
      } else {
        this.showToast('error', data.error || 'Pendaftaran gagal');
      }
    } catch (e) {
      this.showToast('error', 'Gagal menghubungi server');
    }
  },

  logout() {
    localStorage.removeItem('scs_token');
    this.currentUser = null;
    this.renderUserUI();
    this.showToast('info', 'Anda telah keluar dari sistem.');
    this.navigate('home');
  },

  async quickSwitchRole(userId) {
    try {
      const res = await fetch(`${this.apiBase}/auth/token-for-user?id=${userId}`);
      const data = await res.json();
      if (data.success) {
        localStorage.setItem('scs_token', data.token);
        this.currentUser = data.user;
        this.renderUserUI();
        this.showToast('success', `Beralih peran sebagai: ${data.user.name} (${data.user.roles.join(', ')})`);
        this.navigate(this.getDefaultViewForRoles(data.user.roles));
      }
    } catch (e) {
      this.showToast('error', 'Gagal switch role');
    }
  },

  getDefaultViewForRoles(roles) {
    if (roles.includes('SUPERADMIN')) return 'superadmin';
    if (roles.includes('ADMIN')) return 'admin';
    if (roles.includes('PETUGAS')) return 'field';
    if (roles.includes('PIMPINAN')) return 'analytics';
    return 'citizen';
  },

  // 3. Navigation
  navigate(viewName) {
    this.activeView = viewName;
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
      target.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Update active nav styling
    document.querySelectorAll('[data-nav-target]').forEach(link => {
      const isTarget = link.getAttribute('data-nav-target') === viewName;
      if (isTarget) {
        link.classList.add('bg-primary-container', 'text-on-primary', 'font-semibold');
        link.classList.remove('text-on-surface-variant');
      } else {
        link.classList.remove('bg-primary-container', 'text-on-primary', 'font-semibold');
        link.classList.add('text-on-surface-variant');
      }
    });

    // View specific hooks
    if (viewName === 'home') {
      setTimeout(() => this.initHomeMap(), 200);
      this.loadHomeData();
    } else if (viewName === 'create-report') {
      setTimeout(() => this.initCreateMap(), 200);
    } else if (viewName === 'admin') {
      this.loadAdminData();
    } else if (viewName === 'field') {
      this.loadFieldData();
    } else if (viewName === 'analytics') {
      this.loadAnalyticsData();
    } else if (viewName === 'citizen') {
      this.loadCitizenData();
    } else if (viewName === 'superadmin') {
      this.loadSuperadminData();
    }
  },

  // 4. Metadata Loading (Categories & Departments)
  async loadMeta() {
    try {
      const [resCat, resDept] = await Promise.all([
        fetch(`${this.apiBase}/categories`),
        fetch(`${this.apiBase}/departments`)
      ]);
      const dataCat = await resCat.json();
      const dataDept = await resDept.json();
      if (dataCat.success) this.categories = dataCat.categories;
      if (dataDept.success) this.departments = dataDept.departments;

      this.populateCategorySelects();
      this.populateDepartmentSelects();
    } catch (e) {
      console.warn("Error loading metadata:", e);
    }
  },

  populateCategorySelects() {
    const selects = [
      document.getElementById('report-category-select'),
      document.getElementById('filter-category-select'),
      document.getElementById('admin-filter-category')
    ];
    selects.forEach(select => {
      if (!select) return;
      const isFilter = select.id.includes('filter');
      select.innerHTML = isFilter ? '<option value="ALL">Semua Kategori</option>' : '<option value="">-- Pilih Kategori Masalah --</option>';
      this.categories.forEach(cat => {
        select.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
      });
    });
  },

  populateDepartmentSelects() {
    const selects = [
      document.getElementById('verify-dept-select'),
      document.getElementById('admin-filter-dept')
    ];
    selects.forEach(select => {
      if (!select) return;
      const isFilter = select.id.includes('filter');
      select.innerHTML = isFilter ? '<option value="ALL">Semua OPD / Instansi</option>' : '<option value="">-- Pilih OPD Penanggung Jawab --</option>';
      this.departments.forEach(dept => {
        select.innerHTML += `<option value="${dept.id}">${dept.name} (${dept.code})</option>`;
      });
    });
  },

  // 5. Maps (Leaflet + OpenStreetMap)
  initHomeMap() {
    const container = document.getElementById('map-home');
    if (!container) return;

    if (!this.mapHome) {
      // Centered on Kota Bandar Lampung [-5.4292, 105.2625]
      this.mapHome = L.map('map-home', {
        center: [-5.4124, 105.2591],
        zoom: 13,
        zoomControl: true
      });
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap kontributor | Pemkot Bandar Lampung'
      }).addTo(this.mapHome);
    } else {
      this.mapHome.invalidateSize();
    }
  },

  updateHomeMapMarkers(reports) {
    if (!this.mapHome) return;
    this.homeMarkers.forEach(m => this.mapHome.removeLayer(m));
    this.homeMarkers = [];

    reports.forEach(rep => {
      if (!rep.lat || !rep.lng) return;

      const colorMap = {
        'SUBMITTED': '#00629d', // Blue
        'VERIFIED': '#163b65', // Dark Navy
        'ASSIGNED': '#d97706', // Amber
        'IN_PROGRESS': '#7c3aed', // Purple
        'RESOLVED': '#059669', // Emerald Green
        'CLOSED': '#475569', // Slate
        'REJECTED': '#dc2626', // Red
        'NEEDS_INFO': '#ea580c' // Orange
      };
      const pinColor = colorMap[rep.status] || '#00629d';

      const customIcon = L.divIcon({
        className: 'custom-map-pin',
        html: `<div style="background-color: ${pinColor}; width: 28px; height: 28px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white;">
                 <span class="material-symbols-outlined" style="font-size: 16px;">location_on</span>
               </div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 28]
      });

      const marker = L.marker([rep.lat, rep.lng], { icon: customIcon }).addTo(this.mapHome);
      marker.bindPopup(`
        <div class="p-1 max-w-xs font-sans">
          <div class="text-[11px] font-bold text-blue-800 uppercase tracking-wide">#${rep.ticket_no}</div>
          <h4 class="font-bold text-sm text-gray-900 mt-0.5 leading-snug">${rep.title}</h4>
          <p class="text-xs text-gray-600 mt-1">${rep.address_text}</p>
          <div class="mt-2 flex items-center justify-between">
            <span class="px-2 py-0.5 text-[10px] rounded font-bold uppercase" style="background-color: ${pinColor}20; color: ${pinColor};">${rep.status}</span>
            <button onclick="SCS.viewReportDetail('${rep.id}')" class="text-xs text-blue-700 font-bold underline">Lihat Detail</button>
          </div>
        </div>
      `);
      this.homeMarkers.push(marker);
    });
  },

  initCreateMap() {
    const container = document.getElementById('map-create-picker');
    if (!container) return;

    if (!this.mapCreate) {
      this.mapCreate = L.map('map-create-picker', {
        center: [-5.3789, 105.2541], // Depan Kampus Teknokrat / ZA Pagar Alam
        zoom: 14
      });
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
      }).addTo(this.mapCreate);

      this.createMarker = L.marker([-5.3789, 105.2541], { draggable: true }).addTo(this.mapCreate);

      const updateCoords = (lat, lng) => {
        document.getElementById('input-lat').value = lat.toFixed(6);
        document.getElementById('input-lng').value = lng.toFixed(6);
      };

      updateCoords(-5.3789, 105.2541);

      this.createMarker.on('dragend', (e) => {
        const pos = e.target.getLatLng();
        updateCoords(pos.lat, pos.lng);
      });

      this.mapCreate.on('click', (e) => {
        this.createMarker.setLatLng(e.latlng);
        updateCoords(e.latlng.lat, e.latlng.lng);
      });
    } else {
      this.mapCreate.invalidateSize();
    }
  },

  useCurrentGPSLocation() {
    if (!navigator.geolocation) {
      this.showToast('error', 'Browser tidak mendukung geolokasi');
      return;
    }
    this.showToast('info', 'Mendeteksi titik koordinat GPS Anda...');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        if (this.mapCreate && this.createMarker) {
          this.mapCreate.setView([lat, lng], 16);
          this.createMarker.setLatLng([lat, lng]);
          document.getElementById('input-lat').value = lat.toFixed(6);
          document.getElementById('input-lng').value = lng.toFixed(6);
          this.showToast('success', `GPS terdeteksi: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
        }
      },
      (err) => {
        this.showToast('warning', 'Gagal membaca GPS. Menggunakan default Kota Bandar Lampung.');
      },
      { timeout: 7000 }
    );
  },

  // 6. Home View Data
  async loadHomeData() {
    try {
      const [resReports, resSummary] = await Promise.all([
        fetch(`${this.apiBase}/reports?limit=50`),
        fetch(`${this.apiBase}/dashboard/summary`)
      ]);
      const dataReports = await resReports.json();
      const dataSummary = await resSummary.json();

      if (dataReports.success) {
        this.allReports = dataReports.reports;
        this.renderPublicReports(dataReports.reports);
        this.updateHomeMapMarkers(dataReports.reports);
      }

      if (dataSummary.success && dataSummary.kpi) {
        document.getElementById('kpi-home-total').textContent = dataSummary.kpi.total.toLocaleString();
        document.getElementById('kpi-home-resolved').textContent = dataSummary.kpi.resolved.toLocaleString();
        document.getElementById('kpi-home-rate').textContent = `${dataSummary.kpi.resolution_rate}%`;
        document.getElementById('kpi-home-rating').textContent = `${dataSummary.kpi.avg_rating} / 5.0`;
      }
    } catch (e) {
      console.warn("Error loading home data:", e);
    }
  },

  renderPublicReports(reports) {
    const container = document.getElementById('public-reports-container');
    if (!container) return;

    if (reports.length === 0) {
      container.innerHTML = `<div class="col-span-full text-center py-8 text-on-surface-variant font-medium">Belum ada laporan pengaduan ditemukan.</div>`;
      return;
    }

    container.innerHTML = reports.slice(0, 9).map(rep => {
      const statusBadge = this.getStatusBadge(rep.status);
      const thumb = rep.thumbnail_url || 'https://images.unsplash.com/photo-1517649763962-0c623266ddc0?auto=format&fit=crop&w=600&q=80';
      const dateStr = new Date(rep.created_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });

      return `
        <div class="complaint-card bg-surface-container-lowest rounded-xl shadow-sm hover:shadow-md transition-all overflow-hidden flex flex-col border border-outline-variant/30 group">
          <div class="relative h-44 w-full overflow-hidden bg-surface-dim">
            <img src="${thumb}" alt="${rep.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" onerror="this.src='https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80'">
            <div class="absolute top-2 left-2">${statusBadge}</div>
            <div class="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-primary/80 backdrop-blur-md text-on-primary font-mono text-[11px] font-semibold">
              #${rep.ticket_no}
            </div>
          </div>
          <div class="p-space-md flex flex-col flex-grow justify-between gap-space-sm">
            <div>
              <div class="flex items-center gap-1.5 text-xs text-secondary font-semibold mb-1">
                <span class="material-symbols-outlined text-[16px]">${rep.category_icon || 'flag'}</span>
                <span>${rep.category_name}</span>
                <span class="text-outline-variant">•</span>
                <span>Kec. ${rep.district}</span>
              </div>
              <h3 class="font-headline-sm text-[16px] leading-snug font-bold text-primary group-hover:text-secondary transition-colors line-clamp-2">
                ${rep.title}
              </h3>
              <p class="font-body-sm text-body-sm text-on-surface-variant mt-1.5 line-clamp-2">
                ${rep.description}
              </p>
            </div>
            <div class="pt-space-xs border-t border-outline-variant/30 flex items-center justify-between text-xs text-on-surface-variant">
              <span>${dateStr}</span>
              <button onclick="SCS.viewReportDetail('${rep.id}')" class="font-bold text-secondary hover:text-primary transition-colors flex items-center gap-0.5">
                <span>Rincian</span>
                <span class="material-symbols-outlined text-[16px]">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  // 7. Create Report Submission (FR-03, AC-01, AC-02)
  async submitNewReport(e) {
    e.preventDefault();
    if (!this.currentUser) {
      this.showToast('warning', 'Silakan masuk akun terlebih dahulu sebelum mengirim pengaduan');
      this.openModal('modal-auth');
      return;
    }

    const title = document.getElementById('input-title').value.trim();
    const category_id = document.getElementById('report-category-select').value;
    const description = document.getElementById('input-description').value.trim();
    const address_text = document.getElementById('input-address').value.trim();
    const district = document.getElementById('input-district').value;
    const lat = document.getElementById('input-lat').value;
    const lng = document.getElementById('input-lng').value;
    const is_anonymous = document.getElementById('input-anonymous').checked;
    const photoFile = document.getElementById('input-photo').files[0];

    // Validation (AC-02)
    if (!title || !category_id || !description || !address_text) {
      this.showToast('error', 'Semua kolom bertanda bintang wajib diisi lengkap!');
      return;
    }

    const formData = new FormData();
    formData.append('title', title);
    formData.append('category_id', category_id);
    formData.append('description', description);
    formData.append('address_text', address_text);
    formData.append('district', district);
    formData.append('lat', lat);
    formData.append('lng', lng);
    formData.append('is_anonymous', is_anonymous ? '1' : '0');

    if (photoFile) {
      formData.append('photo', photoFile);
    }

    const btnSubmit = document.getElementById('btn-submit-report');
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<span class="material-symbols-outlined text-[20px] animate-spin">refresh</span><span>Mengirim Laporan...</span>`;

    try {
      const res = await fetch(`${this.apiBase}/reports`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('scs_token')}`
        },
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('form-create-report').reset();
        document.getElementById('photo-preview-box').classList.add('hidden');
        
        // Show Success Confirmation Modal with Ticket No (AC-01)
        document.getElementById('confirmed-ticket-no').textContent = data.ticket_no;
        this.openModal('modal-ticket-success');
        this.loadHomeData();
      } else {
        this.showToast('error', data.error || 'Gagal mengirim laporan');
      }
    } catch (err) {
      this.showToast('error', 'Gagal mengirim pengaduan ke server');
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = `<span class="material-symbols-outlined text-[20px]">send</span><span>Kirim Laporan Pengaduan</span>`;
    }
  },

  // 8. Track Ticket (FR-05, FR-14)
  async trackTicketByInput() {
    const input = document.getElementById('ticket-search-input') || document.getElementById('hero-ticket-input');
    const ticketNo = input ? input.value.trim().replace('#', '') : '';
    if (!ticketNo) {
      this.showToast('warning', 'Masukkan nomor tiket terlebih dahulu (contoh: SCS-20261110-8842)');
      return;
    }
    await this.viewReportDetail(ticketNo);
  },

  // 9. Report Detail Modal & Workflow Timeline
  async viewReportDetail(reportIdOrTicket) {
    try {
      this.showToast('info', 'Memuat data rincian laporan...');
      const res = await fetch(`${this.apiBase}/reports/${encodeURIComponent(reportIdOrTicket)}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('scs_token') || ''}`
        }
      });
      const data = await res.json();
      if (!data.success) {
        this.showToast('error', data.error || 'Laporan tidak ditemukan');
        return;
      }

      const rep = data.report;
      this.currentDetailReport = rep;

      document.getElementById('detail-ticket-no').textContent = `#${rep.ticket_no}`;
      document.getElementById('detail-title').textContent = rep.title;
      document.getElementById('detail-category').textContent = rep.category_name;
      document.getElementById('detail-district').textContent = `Kecamatan ${rep.district}`;
      document.getElementById('detail-description').textContent = rep.description;
      document.getElementById('detail-address').textContent = rep.address_text;
      document.getElementById('detail-reporter-name').textContent = rep.reporter_name;
      document.getElementById('detail-created-at').textContent = new Date(rep.created_at).toLocaleString('id-ID');
      
      const statusBadge = this.getStatusBadge(rep.status);
      document.getElementById('detail-status-badge').innerHTML = statusBadge;

      // Evidence Photos
      const mediaContainer = document.getElementById('detail-media-gallery');
      mediaContainer.innerHTML = '';
      if (rep.media && rep.media.length > 0) {
        rep.media.forEach(m => {
          mediaContainer.innerHTML += `
            <div class="flex flex-col bg-surface-container-low rounded-lg overflow-hidden shadow-sm">
              <div class="h-40 w-full overflow-hidden bg-surface-dim">
                <img src="${m.url}" class="w-full h-full object-cover hover:scale-105 transition-all cursor-pointer" onclick="window.open('${m.url}', '_blank')">
              </div>
              <div class="p-2 flex items-center justify-between text-xs">
                <span class="font-bold text-primary">${m.phase === 'RESOLUTION' ? 'Bukti Selesai (Petugas)' : 'Bukti Awal (Warga)'}</span>
                <span class="text-outline text-[11px]">${new Date(m.created_at).toLocaleDateString('id-ID')}</span>
              </div>
            </div>
          `;
        });
      } else {
        mediaContainer.innerHTML = `<p class="col-span-full text-xs text-on-surface-variant italic">Tidak ada lampiran foto bukti.</p>`;
      }

      // Department & Assignment
      const deptBox = document.getElementById('detail-assignment-info');
      if (rep.department_name) {
        deptBox.innerHTML = `
          <div class="p-3 rounded-lg bg-surface-container-high flex flex-col gap-1">
            <span class="text-xs text-secondary font-bold uppercase tracking-wider">Instansi Pelaksana (OPD):</span>
            <span class="font-bold text-primary text-sm">${rep.department_name}</span>
            <span class="text-xs text-on-surface-variant">Petugas Lapangan: <strong>${rep.assignee_name || 'Menunggu penunjukan mandor'}</strong></span>
          </div>
        `;
      } else {
        deptBox.innerHTML = `
          <div class="p-3 rounded-lg bg-surface-container-low text-xs text-on-surface-variant">
            Belum didisposisikan ke Organisasi Perangkat Daerah (OPD).
          </div>
        `;
      }

      // Chronological Status History Timeline
      const timelineContainer = document.getElementById('detail-timeline-container');
      timelineContainer.innerHTML = '';
      if (rep.status_history && rep.status_history.length > 0) {
        rep.status_history.forEach((h, idx) => {
          const isLatest = idx === rep.status_history.length - 1;
          timelineContainer.innerHTML += `
            <div class="flex items-start gap-3 relative pb-4">
              <div class="flex flex-col items-center">
                <div class="w-8 h-8 rounded-full ${isLatest ? 'bg-secondary text-white' : 'bg-surface-container-highest text-secondary'} flex items-center justify-center shrink-0 z-10 shadow-sm">
                  <span class="material-symbols-outlined text-[16px]">${this.getStatusIcon(h.new_status)}</span>
                </div>
                ${!isLatest ? '<div class="w-0.5 bg-outline-variant/50 flex-grow h-full -mb-4"></div>' : ''}
              </div>
              <div class="flex flex-col bg-surface-container-lowest p-3 rounded-lg flex-grow shadow-xs">
                <div class="flex items-center justify-between gap-2">
                  <span class="font-bold text-xs uppercase text-primary">${h.new_status}</span>
                  <span class="text-[11px] text-outline">${new Date(h.changed_at).toLocaleString('id-ID')}</span>
                </div>
                <p class="text-xs text-on-surface mt-1">${h.note || 'Status pengaduan diperbarui'}</p>
                <span class="text-[10px] text-secondary mt-1">Oleh: ${h.changed_by_name || 'Sistem'}</span>
              </div>
            </div>
          `;
        });
      }

      // Interactive Map in Detail
      setTimeout(() => {
        const mapContainer = document.getElementById('map-detail-view');
        if (mapContainer && rep.lat && rep.lng) {
          if (!this.mapDetail) {
            this.mapDetail = L.map('map-detail-view', { center: [rep.lat, rep.lng], zoom: 15 });
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(this.mapDetail);
          } else {
            this.mapDetail.setView([rep.lat, rep.lng], 15);
            this.mapDetail.invalidateSize();
          }
          if (this.detailMarker) this.mapDetail.removeLayer(this.detailMarker);
          this.detailMarker = L.marker([rep.lat, rep.lng]).addTo(this.mapDetail);
          this.detailMarker.bindPopup(`<strong>${rep.title}</strong><br>${rep.address_text}`).openPopup();
        }
      }, 300);

      // Comments & Clarifications
      this.renderDetailComments(rep.comments || []);

      // Feedback / Rating Box (FR-13)
      const feedbackSection = document.getElementById('detail-feedback-section');
      if (['RESOLVED', 'CLOSED'].includes(rep.status)) {
        feedbackSection.classList.remove('hidden');
        if (rep.feedback) {
          document.getElementById('feedback-form-box').classList.add('hidden');
          document.getElementById('feedback-result-box').classList.remove('hidden');
          document.getElementById('feedback-stars-display').innerHTML = '★'.repeat(rep.feedback.rating) + '☆'.repeat(5 - rep.feedback.rating);
          document.getElementById('feedback-comment-display').textContent = rep.feedback.comment || 'Penilaian diberikan tanpa catatan.';
        } else {
          document.getElementById('feedback-form-box').classList.remove('hidden');
          document.getElementById('feedback-result-box').classList.add('hidden');
        }
      } else {
        feedbackSection.classList.add('hidden');
      }

      this.openModal('modal-report-detail');
    } catch (err) {
      this.showToast('error', 'Gagal memuat detail laporan');
    }
  },

  renderDetailComments(comments) {
    const list = document.getElementById('detail-comments-list');
    list.innerHTML = '';
    if (comments.length === 0) {
      list.innerHTML = `<p class="text-xs text-on-surface-variant italic py-2">Belum ada diskusi atau klarifikasi.</p>`;
      return;
    }

    comments.forEach(c => {
      const isInternal = c.visibility === 'INTERNAL';
      list.innerHTML += `
        <div class="p-3 rounded-lg ${isInternal ? 'bg-amber-50 border border-amber-200' : 'bg-surface-container-low'} flex flex-col gap-1">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-primary flex items-center gap-1">
              ${c.author_name}
              ${isInternal ? '<span class="px-1.5 py-0.2 rounded bg-amber-200 text-amber-900 text-[10px]">INTERNAL</span>' : ''}
            </span>
            <span class="text-outline text-[11px]">${new Date(c.created_at).toLocaleString('id-ID')}</span>
          </div>
          <p class="text-xs text-on-surface mt-0.5">${c.body}</p>
        </div>
      `;
    });
  },

  async addDetailComment() {
    const input = document.getElementById('detail-comment-input');
    const body = input.value.trim();
    if (!body || !this.currentDetailReport) return;

    if (!this.currentUser) {
      this.showToast('warning', 'Silakan masuk akun untuk menambahkan komentar');
      this.openModal('modal-auth');
      return;
    }

    try {
      const res = await fetch(`${this.apiBase}/reports/${this.currentDetailReport.id}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('scs_token')}`
        },
        body: JSON.stringify({ body })
      });
      const data = await res.json();
      if (data.success) {
        input.value = '';
        this.viewReportDetail(this.currentDetailReport.id);
        this.showToast('success', 'Komentar/klarifikasi berhasil dikirim');
      }
    } catch (e) {
      this.showToast('error', 'Gagal mengirim komentar');
    }
  },

  async submitFeedback() {
    if (!this.currentDetailReport) return;
    const rating = document.querySelector('input[name="rating_stars"]:checked')?.value || 5;
    const comment = document.getElementById('feedback-comment-input').value.trim();

    try {
      const res = await fetch(`${this.apiBase}/reports/${this.currentDetailReport.id}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('scs_token')}`
        },
        body: JSON.stringify({ rating: parseInt(rating), comment })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast('success', data.message);
        this.viewReportDetail(this.currentDetailReport.id);
      }
    } catch (e) {
      this.showToast('error', 'Gagal mengirim feedback');
    }
  },

  // 10. Admin Verifikasi & Disposisi (FR-07, FR-08, AC-04)
  async loadAdminData() {
    try {
      const statusFilter = document.getElementById('admin-filter-status')?.value || 'ALL';
      const categoryFilter = document.getElementById('admin-filter-category')?.value || 'ALL';
      const q = document.getElementById('admin-search-input')?.value.trim() || '';

      let url = `${this.apiBase}/reports?limit=100`;
      if (statusFilter !== 'ALL') url += `&status=${statusFilter}`;
      if (categoryFilter !== 'ALL') url += `&category_id=${categoryFilter}`;
      if (q) url += `&q=${encodeURIComponent(q)}`;

      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('scs_token')}` }
      });
      const data = await res.json();
      if (data.success) {
        this.renderAdminTable(data.reports);
      }
    } catch (e) {
      console.warn("Failed loading admin queue:", e);
    }
  },

  renderAdminTable(reports) {
    const tbody = document.getElementById('admin-reports-table-body');
    if (!tbody) return;

    if (reports.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-on-surface-variant font-medium">Tidak ada antrean laporan pengaduan.</td></tr>`;
      return;
    }

    tbody.innerHTML = reports.map(r => {
      const statusBadge = this.getStatusBadge(r.status);
      const isUrgent = r.priority === 'DARURAT' || r.priority === 'TINGGI';

      return `
        <tr class="border-b border-outline-variant/30 hover:bg-surface-container-low transition-colors">
          <td class="px-4 py-3 font-mono text-xs font-bold text-primary">#${r.ticket_no}</td>
          <td class="px-4 py-3 font-medium text-xs text-on-surface max-w-xs truncate">${r.title}</td>
          <td class="px-4 py-3 text-xs text-secondary font-semibold">${r.category_name}</td>
          <td class="px-4 py-3 text-xs text-on-surface-variant">${r.district}</td>
          <td class="px-4 py-3 text-xs">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isUrgent ? 'bg-error-container text-on-error-container' : 'bg-surface-container text-on-surface'}">${r.priority}</span>
          </td>
          <td class="px-4 py-3">${statusBadge}</td>
          <td class="px-4 py-3 text-right">
            <div class="inline-flex items-center gap-1.5">
              <button onclick="SCS.openAdminVerifyModal('${r.id}')" class="px-2.5 py-1 rounded bg-primary-container text-on-primary text-xs font-bold hover:bg-primary transition-all shadow-xs">
                Verifikasi
              </button>
              <button onclick="SCS.viewReportDetail('${r.id}')" class="p-1 rounded text-on-surface-variant hover:text-primary">
                <span class="material-symbols-outlined text-[18px]">visibility</span>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  async openAdminVerifyModal(reportId) {
    const res = await fetch(`${this.apiBase}/reports/${reportId}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('scs_token')}` }
    });
    const data = await res.json();
    if (!data.success) return;

    const rep = data.report;
    this.adminTargetReport = rep;

    document.getElementById('verify-modal-ticket-no').textContent = `#${rep.ticket_no}`;
    document.getElementById('verify-modal-title').textContent = rep.title;
    document.getElementById('verify-modal-desc').textContent = rep.description;
    document.getElementById('verify-modal-address').textContent = `${rep.address_text} (${rep.district})`;

    this.selectAdminDecision('ACCEPT');
    this.openModal('modal-admin-verify');
  },

  selectAdminDecision(type) {
    this.adminDecision = type;
    const btnAccept = document.getElementById('btn-decision-accept');
    const btnReject = document.getElementById('btn-decision-reject');
    const btnNeedsInfo = document.getElementById('btn-decision-needsinfo');
    const panelReject = document.getElementById('panel-reject-options');
    const panelNeedsInfo = document.getElementById('panel-needsinfo-options');
    const panelAssign = document.getElementById('panel-assign-options');

    [btnAccept, btnReject, btnNeedsInfo].forEach(b => {
      b.classList.remove('bg-primary-container', 'text-on-primary', 'bg-error', 'bg-amber-600');
      b.classList.add('bg-surface-container', 'text-on-surface');
    });

    panelReject.classList.add('hidden');
    panelNeedsInfo.classList.add('hidden');
    panelAssign.classList.remove('hidden');

    if (type === 'ACCEPT') {
      btnAccept.classList.add('bg-primary-container', 'text-on-primary');
      panelAssign.classList.remove('hidden');
    } else if (type === 'REJECT') {
      btnReject.classList.add('bg-error', 'text-white');
      panelReject.classList.remove('hidden');
      panelAssign.classList.add('hidden');
    } else if (type === 'NEEDS_INFO') {
      btnNeedsInfo.classList.add('bg-amber-600', 'text-white');
      panelNeedsInfo.classList.remove('hidden');
      panelAssign.classList.add('hidden');
    }
  },

  async submitAdminVerification() {
    if (!this.adminTargetReport) return;
    const repId = this.adminTargetReport.id;
    const action = this.adminDecision || 'ACCEPT';
    const note = document.getElementById('verify-admin-note').value.trim();

    let payload = { action, note };

    if (action === 'ACCEPT') {
      const deptId = document.getElementById('verify-dept-select').value;
      const priority = document.getElementById('verify-priority-select').value;
      if (!deptId) {
        this.showToast('error', 'Pilih OPD Penanggung Jawab untuk disposisi tugas!');
        return;
      }
      payload.department_id = parseInt(deptId);
      payload.priority = priority;
    } else if (action === 'REJECT') {
      const reasonSelect = document.getElementById('verify-reject-reason').value;
      const reasonDetail = document.getElementById('verify-reject-detail').value.trim();
      const finalReason = reasonDetail ? `${reasonSelect}: ${reasonDetail}` : reasonSelect;
      if (!finalReason) {
        this.showToast('error', 'Alasan penolakan wajib diisi!');
        return;
      }
      payload.reason = finalReason;
    } else if (action === 'NEEDS_INFO') {
      const question = document.getElementById('verify-needsinfo-question').value.trim();
      if (!question) {
        this.showToast('error', 'Pertanyaan klarifikasi kepada pelapor wajib diisi!');
        return;
      }
      payload.question = question;
    }

    try {
      const res = await fetch(`${this.apiBase}/admin/reports/${repId}/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('scs_token')}`
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        this.showToast('success', data.message);
        this.closeModal('modal-admin-verify');
        this.loadAdminData();
      } else {
        this.showToast('error', data.error || 'Verifikasi gagal');
      }
    } catch (e) {
      this.showToast('error', 'Gagal memproses verifikasi');
    }
  },

  // 11. Petugas Lapangan OPD (FR-09, AC-05)
  async loadFieldData() {
    try {
      const res = await fetch(`${this.apiBase}/reports?limit=100`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('scs_token')}` }
      });
      const data = await res.json();
      if (data.success) {
        // Filter tasks relevant to field officers (ASSIGNED, IN_PROGRESS, RESOLVED)
        const tasks = data.reports.filter(r => ['ASSIGNED', 'IN_PROGRESS', 'RESOLVED'].includes(r.status));
        this.renderFieldTasks(tasks);
      }
    } catch (e) {
      console.warn("Failed loading field tasks:", e);
    }
  },

  renderFieldTasks(tasks) {
    const container = document.getElementById('field-tasks-container');
    if (!container) return;

    if (tasks.length === 0) {
      container.innerHTML = `<div class="col-span-full text-center py-8 text-on-surface-variant font-medium">Tidak ada tugas penanganan aktif saat ini.</div>`;
      return;
    }

    container.innerHTML = tasks.map(t => {
      const isInProgress = t.status === 'IN_PROGRESS';
      const isResolved = t.status === 'RESOLVED';
      const isAssigned = t.status === 'ASSIGNED';

      return `
        <div class="bg-surface-container-lowest rounded-xl p-space-md shadow-sm border border-outline-variant/30 flex flex-col justify-between gap-space-sm">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="font-mono text-xs font-bold text-primary">#${t.ticket_no}</span>
              ${this.getStatusBadge(t.status)}
            </div>
            <h4 class="font-bold text-sm text-primary leading-snug">${t.title}</h4>
            <p class="text-xs text-on-surface-variant mt-1 line-clamp-2">${t.description}</p>
            <div class="mt-3 flex items-center gap-1.5 text-xs text-secondary font-semibold">
              <span class="material-symbols-outlined text-[16px]">location_on</span>
              <span class="truncate">${t.address_text}</span>
            </div>
          </div>
          <div class="pt-3 border-t border-outline-variant/30 flex items-center justify-between gap-2">
            <button onclick="SCS.viewReportDetail('${t.id}')" class="text-xs text-secondary font-bold hover:underline">
              Buka Detail
            </button>
            <div class="flex items-center gap-1.5">
              ${isAssigned ? `
                <button onclick="SCS.updateFieldStatus('${t.id}', 'IN_PROGRESS')" class="px-3 py-1.5 rounded-lg bg-primary-container text-on-primary text-xs font-bold hover:bg-primary transition-all">
                  Mulai Kerjakan
                </button>
              ` : ''}
              ${isInProgress ? `
                <button onclick="SCS.openFieldResolveModal('${t.id}')" class="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 transition-all flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">check_circle</span>
                  <span>Selesaikan</span>
                </button>
              ` : ''}
              ${isResolved ? `
                <span class="text-xs text-emerald-700 font-bold flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">verified</span>
                  <span>Tuntas</span>
                </span>
              ` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  async updateFieldStatus(reportId, newStatus, note = '', photoBase64 = null) {
    try {
      const res = await fetch(`${this.apiBase}/field/reports/${reportId}/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('scs_token')}`
        },
        body: JSON.stringify({
          status: newStatus,
          progress_note: note,
          photo_base64: photoBase64
        })
      });
      const data = await res.json();
      if (data.success) {
        this.showToast('success', data.message);
        this.loadFieldData();
      } else {
        this.showToast('error', data.error || 'Gagal update status lapangan');
      }
    } catch (e) {
      this.showToast('error', 'Gagal update status');
    }
  },

  openFieldResolveModal(reportId) {
    this.fieldResolveReportId = reportId;
    this.openModal('modal-field-resolve');
  },

  async submitFieldResolve() {
    if (!this.fieldResolveReportId) return;
    const note = document.getElementById('field-resolve-note').value.trim();
    const photoInput = document.getElementById('field-resolve-photo');
    let photoBase64 = null;

    if (photoInput.files && photoInput.files[0]) {
      const file = photoInput.files[0];
      photoBase64 = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.readAsDataURL(file);
      });
    }

    await this.updateFieldStatus(this.fieldResolveReportId, 'RESOLVED', note || 'Pekerjaan perbaikan fisik telah tuntas diselesaikan oleh tim lapangan.', photoBase64);
    this.closeModal('modal-field-resolve');
  },

  // 12. Citizen Dashboard (Warga)
  async loadCitizenData() {
    try {
      const res = await fetch(`${this.apiBase}/reports/mine`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('scs_token')}` }
      });
      const data = await res.json();
      if (data.success) {
        this.renderCitizenReports(data.reports);
      }
    } catch (e) {
      console.warn("Failed loading citizen reports:", e);
    }
  },

  renderCitizenReports(reports) {
    const container = document.getElementById('citizen-reports-container');
    if (!container) return;

    if (reports.length === 0) {
      container.innerHTML = `
        <div class="col-span-full text-center py-12 bg-surface-container-lowest rounded-xl shadow-xs">
          <span class="material-symbols-outlined text-[48px] text-outline mb-2">assignment</span>
          <h4 class="font-bold text-primary">Anda belum pernah membuat pengaduan</h4>
          <p class="text-xs text-on-surface-variant mt-1">Sampaikan aspirasi atau keluhan fasilitas umum di Kota Bandar Lampung sekarang.</p>
          <button onclick="SCS.navigate('create-report')" class="mt-4 px-4 py-2 rounded-lg bg-primary-container text-on-primary text-xs font-bold hover:bg-primary transition-all">
            Buat Pengaduan Baru
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = reports.map(r => {
      const statusBadge = this.getStatusBadge(r.status);
      const isNeedsInfo = r.status === 'NEEDS_INFO';
      const isResolved = r.status === 'RESOLVED';

      return `
        <div class="bg-surface-container-lowest rounded-xl p-space-md shadow-sm border border-outline-variant/30 flex flex-col justify-between gap-space-sm">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="font-mono text-xs font-bold text-primary">#${r.ticket_no}</span>
              ${statusBadge}
            </div>
            <h4 class="font-bold text-base text-primary leading-snug">${r.title}</h4>
            <p class="text-xs text-on-surface-variant mt-1 line-clamp-2">${r.description}</p>
            <div class="mt-2 text-xs text-secondary font-medium">${r.address_text}</div>

            ${isNeedsInfo ? `
              <div class="mt-3 p-2.5 rounded-lg bg-amber-50 border border-amber-300 text-amber-900 text-xs flex flex-col gap-1">
                <span class="font-bold flex items-center gap-1">
                  <span class="material-symbols-outlined text-[16px]">info</span>
                  <span>Admin meminta informasi tambahan:</span>
                </span>
                <p>${r.clarification_request || 'Harap berikan kejelasan tambahan pada laporan Anda.'}</p>
              </div>
            ` : ''}
          </div>

          <div class="pt-3 border-t border-outline-variant/30 flex items-center justify-between">
            <span class="text-[11px] text-outline">${new Date(r.created_at).toLocaleDateString('id-ID')}</span>
            <div class="flex items-center gap-2">
              ${isResolved ? `
                <button onclick="SCS.viewReportDetail('${r.id}')" class="px-3 py-1 rounded bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 transition-all flex items-center gap-1">
                  <span class="material-symbols-outlined text-[14px]">star</span>
                  <span>Beri Nilai</span>
                </button>
              ` : ''}
              <button onclick="SCS.viewReportDetail('${r.id}')" class="px-3 py-1 rounded bg-surface-container text-primary text-xs font-bold hover:bg-surface-container-high transition-all">
                Lacak Status
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  // 13. Executive Analytics & Charts (FR-11, Pimpinan)
  async loadAnalyticsData() {
    try {
      const res = await fetch(`${this.apiBase}/dashboard/summary`);
      const data = await res.json();
      if (!data.success) return;

      const kpi = data.kpi;
      document.getElementById('analytics-kpi-total').textContent = kpi.total.toLocaleString();
      document.getElementById('analytics-kpi-resolved').textContent = kpi.resolved.toLocaleString();
      document.getElementById('analytics-kpi-in-progress').textContent = kpi.in_progress.toLocaleString();
      document.getElementById('analytics-kpi-submitted').textContent = kpi.submitted.toLocaleString();
      document.getElementById('analytics-kpi-rate').textContent = `${kpi.resolution_rate}%`;
      document.getElementById('analytics-kpi-rating').textContent = `${kpi.avg_rating} / 5.0`;

      // Render Charts with Chart.js
      this.renderCharts(data);
    } catch (e) {
      console.warn("Failed loading analytics:", e);
    }
  },

  renderCharts(data) {
    if (typeof Chart === 'undefined') return;

    // Destroy existing charts to prevent canvas re-use glitch
    Object.values(this.charts).forEach(c => c && c.destroy());
    this.charts = {};

    // 1. Category Chart
    const ctxCategory = document.getElementById('chart-category');
    if (ctxCategory) {
      this.charts.category = new Chart(ctxCategory, {
        type: 'doughnut',
        data: {
          labels: data.by_category.map(c => c.name),
          datasets: [{
            data: data.by_category.map(c => c.count),
            backgroundColor: ['#002549', '#00629d', '#004240', '#34b6b1', '#d97706', '#dc2626']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } } }
        }
      });
    }

    // 2. Status Chart
    const ctxStatus = document.getElementById('chart-status');
    if (ctxStatus) {
      this.charts.status = new Chart(ctxStatus, {
        type: 'bar',
        data: {
          labels: data.by_status.map(s => s.status),
          datasets: [{
            label: 'Jumlah Pengaduan',
            data: data.by_status.map(s => s.count),
            backgroundColor: '#00629d',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
      });
    }

    // 3. District Chart
    const ctxDistrict = document.getElementById('chart-district');
    if (ctxDistrict) {
      this.charts.district = new Chart(ctxDistrict, {
        type: 'bar',
        data: {
          labels: data.by_district.map(d => d.district),
          datasets: [{
            label: 'Pengaduan per Kecamatan',
            data: data.by_district.map(d => d.count),
            backgroundColor: '#163b65',
            borderRadius: 6
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
        }
      });
    }

    // 4. Department Chart
    const ctxDept = document.getElementById('chart-department');
    if (ctxDept) {
      this.charts.dept = new Chart(ctxDept, {
        type: 'bar',
        data: {
          labels: data.by_department.map(d => d.name.split('(')[0]),
          datasets: [{
            label: 'Penanganan OPD',
            data: data.by_department.map(d => d.count),
            backgroundColor: '#004240',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
      });
    }
  },

  // 14. Superadmin Data (Users, OPDs, Audit Logs)
  async loadSuperadminData() {
    try {
      const [resUsers, resLogs] = await Promise.all([
        fetch(`${this.apiBase}/users`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('scs_token')}` } }),
        fetch(`${this.apiBase}/audit-logs`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('scs_token')}` } })
      ]);
      const dataUsers = await resUsers.json();
      const dataLogs = await resLogs.json();

      if (dataUsers.success) {
        const tbody = document.getElementById('superadmin-users-table');
        if (tbody) {
          tbody.innerHTML = dataUsers.users.map(u => `
            <tr class="border-b border-outline-variant/30 text-xs hover:bg-surface-container-low">
              <td class="px-4 py-3 font-medium text-primary">${u.full_name}</td>
              <td class="px-4 py-3 text-on-surface-variant">${u.email}</td>
              <td class="px-4 py-3 font-mono">${u.phone || '-'}</td>
              <td class="px-4 py-3"><span class="px-2 py-0.5 rounded bg-surface-container font-bold text-secondary">${u.roles || 'MASYARAKAT'}</span></td>
              <td class="px-4 py-3"><span class="px-2 py-0.5 rounded font-bold ${u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}">${u.is_active ? 'Aktif' : 'Nonaktif'}</span></td>
            </tr>
          `).join('');
        }
      }

      if (dataLogs.success) {
        const tbodyLogs = document.getElementById('superadmin-audit-table');
        if (tbodyLogs) {
          tbodyLogs.innerHTML = dataLogs.logs.slice(0, 50).map(l => `
            <tr class="border-b border-outline-variant/30 text-xs hover:bg-surface-container-low">
              <td class="px-4 py-2 font-mono text-outline text-[11px]">${new Date(l.created_at).toLocaleString('id-ID')}</td>
              <td class="px-4 py-2 font-bold text-primary">${l.actor_name || 'System'}</td>
              <td class="px-4 py-2 font-mono font-bold text-secondary">${l.action}</td>
              <td class="px-4 py-2 text-on-surface-variant">${l.entity_type} (${l.entity_id || '-'})</td>
              <td class="px-4 py-2 text-outline font-mono text-[10px] truncate max-w-xs">${l.metadata || '-'}</td>
            </tr>
          `).join('');
        }
      }
    } catch (e) {
      console.warn("Failed loading superadmin data:", e);
    }
  },

  // 15. In-App Notifications (FR-10)
  async fetchNotifications() {
    try {
      const res = await fetch(`${this.apiBase}/notifications`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('scs_token')}` }
      });
      const data = await res.json();
      if (data.success) {
        const badge = document.getElementById('notif-badge-counter');
        const count = data.unread_count || 0;
        if (count > 0) {
          badge.textContent = count > 9 ? '9+' : count;
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }

        const list = document.getElementById('notif-dropdown-list');
        if (list) {
          if (data.notifications.length === 0) {
            list.innerHTML = `<div class="p-4 text-center text-xs text-on-surface-variant">Tidak ada notifikasi baru</div>`;
          } else {
            list.innerHTML = data.notifications.map(n => `
              <div class="p-3 border-b border-outline-variant/20 hover:bg-surface-container-high transition-colors cursor-pointer ${n.read_at ? 'opacity-70' : 'bg-surface-container-lowest font-medium'}" onclick="SCS.handleNotifClick('${n.report_id}')">
                <div class="flex items-center justify-between text-xs mb-1">
                  <span class="font-bold text-primary">${n.title}</span>
                  <span class="text-[10px] text-outline">${new Date(n.created_at).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <p class="text-xs text-on-surface-variant">${n.body}</p>
              </div>
            `).join('');
          }
        }
      }
    } catch (e) {
      console.warn("Error fetching notifications:", e);
    }
  },

  async markAllNotificationsRead() {
    try {
      await fetch(`${this.apiBase}/notifications/read`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('scs_token')}` }
      });
      this.fetchNotifications();
    } catch (e) {}
  },

  handleNotifClick(reportId) {
    this.closeModal('dropdown-notif');
    if (reportId) this.viewReportDetail(reportId);
  },

  // 16. Helpers & Utilities
  getStatusBadge(status) {
    const config = {
      'SUBMITTED': { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Baru Masuk' },
      'VERIFIED': { bg: 'bg-indigo-100', text: 'text-indigo-800', label: 'Terverifikasi' },
      'NEEDS_INFO': { bg: 'bg-orange-100', text: 'text-orange-800', label: 'Perlu Info' },
      'ASSIGNED': { bg: 'bg-amber-100', text: 'text-amber-800', label: 'Didisposisi' },
      'IN_PROGRESS': { bg: 'bg-purple-100', text: 'text-purple-800', label: 'Diproses' },
      'RESOLVED': { bg: 'bg-emerald-100', text: 'text-emerald-800', label: 'Selesai' },
      'CLOSED': { bg: 'bg-slate-100', text: 'text-slate-800', label: 'Ditutup' },
      'REJECTED': { bg: 'bg-rose-100', text: 'text-rose-800', label: 'Ditolak' },
      'REOPENED': { bg: 'bg-pink-100', text: 'text-pink-800', label: 'Dibuka Ulang' }
    };
    const c = config[status] || { bg: 'bg-gray-100', text: 'text-gray-800', label: status };
    return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${c.bg} ${c.text}">${c.label}</span>`;
  },

  getStatusIcon(status) {
    const icons = {
      'SUBMITTED': 'inbox',
      'VERIFIED': 'verified',
      'NEEDS_INFO': 'help',
      'ASSIGNED': 'assignment_ind',
      'IN_PROGRESS': 'engineering',
      'RESOLVED': 'check_circle',
      'CLOSED': 'task_alt',
      'REJECTED': 'cancel',
      'REOPENED': 'refresh'
    };
    return icons[status] || 'circle';
  },

  showToast(type, msg) {
    const toast = document.getElementById('app-toast');
    if (!toast) return;

    const iconMap = {
      'success': 'check_circle',
      'error': 'error',
      'warning': 'warning',
      'info': 'info'
    };
    const colorMap = {
      'success': 'bg-emerald-700 text-white',
      'error': 'bg-rose-700 text-white',
      'warning': 'bg-amber-600 text-white',
      'info': 'bg-primary text-white'
    };

    toast.className = `fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-xl transition-all duration-300 ${colorMap[type] || colorMap.info}`;
    toast.innerHTML = `
      <span class="material-symbols-outlined text-[20px]">${iconMap[type] || 'info'}</span>
      <span class="text-sm font-medium">${msg}</span>
    `;
    toast.classList.remove('hidden', 'opacity-0');
    toast.classList.add('opacity-100');

    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => {
      toast.classList.add('opacity-0');
      setTimeout(() => toast.classList.add('hidden'), 300);
    }, 4000);
  },

  openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove('hidden');
  },

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add('hidden');
  },

  setupEventListeners() {
    // Quick Demo Switcher dropdown popover
    const btnQuickSwitch = document.getElementById('btn-quick-switch-toggle');
    const popQuickSwitch = document.getElementById('popover-quick-switch');
    if (btnQuickSwitch && popQuickSwitch) {
      btnQuickSwitch.addEventListener('click', (e) => {
        e.stopPropagation();
        popQuickSwitch.classList.toggle('hidden');
      });
      document.addEventListener('click', () => popQuickSwitch.classList.add('hidden'));
    }

    // Notification dropdown popover
    const btnNotif = document.getElementById('btn-notif-toggle');
    const dropNotif = document.getElementById('dropdown-notif');
    if (btnNotif && dropNotif) {
      btnNotif.addEventListener('click', (e) => {
        e.stopPropagation();
        dropNotif.classList.toggle('hidden');
        if (!dropNotif.classList.contains('hidden')) {
          this.markAllNotificationsRead();
        }
      });
      document.addEventListener('click', () => dropNotif.classList.add('hidden'));
    }

    // Photo input preview
    const photoInput = document.getElementById('input-photo');
    if (photoInput) {
      photoInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        const previewBox = document.getElementById('photo-preview-box');
        const previewImg = document.getElementById('photo-preview-img');
        if (file) {
          const reader = new FileReader();
          reader.onload = (re) => {
            previewImg.src = re.target.result;
            previewBox.classList.remove('hidden');
          };
          reader.readAsDataURL(file);
        } else {
          previewBox.classList.add('hidden');
        }
      });
    }

    // Form create report submit
    const formCreate = document.getElementById('form-create-report');
    if (formCreate) {
      formCreate.addEventListener('submit', (e) => this.submitNewReport(e));
    }
  }
};

// Global Bootstrapper
document.addEventListener('DOMContentLoaded', () => SCS.init());

