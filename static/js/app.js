// JavaScript điều khiển giao diện SportSync AI (Đề tài 36)

let currentCourtTypes = [];
let currentBookings = [];
let currentSelectedSlot = null;
let currentBookingForMsg = null;
let currentUser = null;

// Khởi tạo khi load trang
document.addEventListener('DOMContentLoaded', () => {
    checkCurrentUser();
    loadCourtTypes();
    loadSlots();
    setupEventListeners();
});

function setupEventListeners() {
    // Lọc sơ đồ khung giờ
    document.getElementById('filterDate').addEventListener('change', loadSlots);
    document.getElementById('filterCourtType').addEventListener('change', loadSlots);
    document.getElementById('btnReloadSlots').addEventListener('click', loadSlots);

    // Form Đặt sân
    document.getElementById('bookingForm').addEventListener('submit', handleConfirmBooking);

    // Form AI Chat
    document.getElementById('chatForm').addEventListener('submit', handleSendChat);

    // Prompt Chips
    document.querySelectorAll('.prompt-chip').forEach(chip => {
        chip.addEventListener('click', (e) => {
            const promptText = e.target.getAttribute('data-prompt');
            document.getElementById('chatInput').value = promptText;
            document.getElementById('chatForm').dispatchEvent(new Event('submit'));
        });
    });

    // Quản lý Đặt sân & Tải lại
    document.getElementById('btnReloadBookings').addEventListener('click', loadBookings);

    // Tab chuyển đổi
    document.getElementById('bookings-tab').addEventListener('click', loadBookings);
    document.getElementById('reports-tab').addEventListener('click', loadReports);
    document.getElementById('maintenance-tab').addEventListener('click', loadMaintenanceCourts);

    // AI Phân tích công suất
    document.getElementById('btnRunAiReport').addEventListener('click', runAiOccupancyReport);

    // Sinh tin nhắn AI
    document.getElementById('btnMsgConfirmation').addEventListener('click', () => generateAiMessage('confirmation'));
    document.getElementById('btnMsgReminder').addEventListener('click', () => generateAiMessage('reminder'));
    document.getElementById('btnCopyMsg').addEventListener('click', copyAiMessage);

    // Đăng nhập / Đăng xuất
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('btnLogout').addEventListener('click', handleLogout);
}

// ==================== 1. XÁC THỰC NGƯỜI DÙNG ====================
async function checkCurrentUser() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (data.authenticated) {
            setCurrentUser(data.user);
        } else {
            setCurrentUser(null);
        }
    } catch (e) {
        console.error("Lỗi kiểm tra phiên:", e);
    }
}

function setCurrentUser(user) {
    currentUser = user;
    const badge = document.getElementById('userBadge');
    const btnLogin = document.getElementById('btnLoginModal');
    const btnLogout = document.getElementById('btnLogout');

    if (user) {
        badge.className = `badge ${user.role === 'ADMIN' ? 'bg-danger' : 'bg-success'} py-2 px-3`;
        badge.innerHTML = `<i class="fa-solid fa-user-shield me-1"></i> ${user.username} (${user.role})`;
        btnLogin.classList.add('d-none');
        btnLogout.classList.remove('d-none');
    } else {
        badge.className = 'badge bg-secondary py-2 px-3';
        badge.innerHTML = '<i class="fa-solid fa-user me-1"></i> Khách vãng lai';
        btnLogin.classList.remove('d-none');
        btnLogout.classList.add('d-none');
    }
}

function quickFillLogin(u, p) {
    document.getElementById('loginUsername').value = u;
    document.getElementById('loginPassword').value = p;
}

async function handleLogin(e) {
    e.preventDefault();
    const u = document.getElementById('loginUsername').value;
    const p = document.getElementById('loginPassword').value;

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
            setCurrentUser(data.user);
            loadMaintenanceCourts();
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) {
        showToast("Lỗi kết nối máy chủ", 'danger');
    }
}

async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    setCurrentUser(null);
    showToast("Đã đăng xuất", 'info');
}

// ==================== 2. SƠ ĐỒ KHUNG GIỜ (TIME SLOTS) ====================
async function loadCourtTypes() {
    try {
        const res = await fetch('/api/court-types');
        const data = await res.json();
        if (data.success) {
            currentCourtTypes = data.data;
            const select = document.getElementById('filterCourtType');
            select.innerHTML = '<option value="">-- Tất cả loại sân --</option>';
            currentCourtTypes.forEach(t => {
                select.innerHTML += `<option value="${t.id}">${t.name}</option>`;
            });
        }
    } catch (e) {
        console.error("Lỗi nạp loại sân:", e);
    }
}

async function loadSlots() {
    const container = document.getElementById('slotsContainer');
    const dateVal = document.getElementById('filterDate').value;
    const typeVal = document.getElementById('filterCourtType').value;

    container.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 text-muted">Đang tải dữ liệu khung giờ ngày ${dateVal}...</p>
        </div>
    `;

    try {
        const queryParams = new URLSearchParams({ date: dateVal });
        if (typeVal) queryParams.append('court_type_id', typeVal);

        const res = await fetch(`/api/slots?${queryParams.toString()}`);
        const data = await res.json();

        if (!data.success || data.data.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="alert alert-warning d-inline-block">
                        <i class="fa-solid fa-triangle-exclamation me-1"></i> Chưa có dữ liệu khung giờ cho ngày đã chọn.
                    </div>
                </div>
            `;
            return;
        }

        // Gom nhóm theo từng sân
        const slotsByCourt = {};
        data.data.forEach(s => {
            if (!slotsByCourt[s.court_name]) {
                slotsByCourt[s.court_name] = {
                    court_id: s.court_id,
                    court_type_name: s.court_type_name,
                    slots: []
                };
            }
            slotsByCourt[s.court_name].slots.push(s);
        });

        container.innerHTML = '';
        Object.keys(slotsByCourt).forEach(courtName => {
            const courtData = slotsByCourt[courtName];
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4';

            let slotsHtml = '';
            courtData.slots.forEach(slot => {
                let statusClass = 'slot-free';
                let statusLabel = 'Trống';
                let isClickable = true;

                if (slot.status === 'BOOKED') {
                    statusClass = 'slot-booked';
                    statusLabel = 'Đã đặt';
                } else if (slot.status === 'MAINTENANCE') {
                    statusClass = 'slot-maintenance';
                    statusLabel = 'Bảo trì';
                    isClickable = false;
                }

                slotsHtml += `
                    <div class="col-6 mb-2">
                        <div class="slot-btn ${statusClass}" 
                             onclick="onSlotClick(${JSON.stringify(slot).replace(/"/g, '&quot;')})">
                            <span class="slot-time">${slot.start_time.substring(0, 5)} - ${slot.end_time.substring(0, 5)}</span>
                            <span class="slot-price">${slot.price.toLocaleString('vi-VN')} đ</span>
                            <span class="badge ${slot.status === 'FREE' ? 'bg-success' : (slot.status === 'BOOKED' ? 'bg-danger' : 'bg-secondary')} mt-1">
                                ${statusLabel}
                            </span>
                        </div>
                    </div>
                `;
            });

            col.innerHTML = `
                <div class="court-card h-100">
                    <div class="court-card-header d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-0 fw-bold text-dark">${courtName}</h6>
                            <small class="text-muted">${courtData.court_type_name}</small>
                        </div>
                        <span class="badge bg-light text-dark border">
                            ${courtData.slots.filter(s => s.status === 'FREE').length} slot trống
                        </span>
                    </div>
                    <div class="card-body p-3">
                        <div class="row g-2">
                            ${slotsHtml}
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(col);
        });

    } catch (e) {
        container.innerHTML = `<div class="col-12 text-center text-danger py-4">Lỗi nạp khung giờ: ${e.message}</div>`;
    }
}

// Xử lý bấm vào 1 slot
function onSlotClick(slot) {
    if (slot.status === 'MAINTENANCE') {
        showToast("Khung giờ này thuộc sân đang bảo trì, không thể đặt!", 'warning');
        return;
    }

    if (slot.status === 'BOOKED') {
        if (slot.booking) {
            showBookingDetailPrompt(slot.booking);
        } else {
            showToast("Khung giờ này đã được đặt trước!", 'info');
        }
        return;
    }

    // Nếu slot FREE: Mở modal đặt sân (Pessimistic Lock)
    currentSelectedSlot = slot;
    document.getElementById('bookSlotId').value = slot.id;
    document.getElementById('modalCourtName').innerText = `${slot.court_name} (${slot.court_type_name})`;
    document.getElementById('modalTimeSlot').innerText = `${slot.start_time.substring(0, 5)} - ${slot.end_time.substring(0, 5)} | Ngày ${slot.booking_date}`;
    document.getElementById('modalSlotPrice').innerText = `${slot.price.toLocaleString('vi-VN')} VNĐ`;

    const minDep = slot.price * 0.3;
    const maxDep = slot.price * 0.5;
    const defaultDep = slot.price * 0.4;
    document.getElementById('bookDeposit').value = defaultDep;
    document.getElementById('depositSuggestion').innerText = `Tối thiểu 30%: ${minDep.toLocaleString('vi-VN')} đ | Tối đa 50%: ${maxDep.toLocaleString('vi-VN')} đ`;

    const modal = new bootstrap.Modal(document.getElementById('bookingModal'));
    modal.show();
}

async function handleConfirmBooking(e) {
    e.preventDefault();
    const slotId = document.getElementById('bookSlotId').value;
    const custName = document.getElementById('bookCustName').value.trim();
    const custPhone = document.getElementById('bookCustPhone').value.trim();
    const deposit = document.getElementById('bookDeposit').value;
    const note = document.getElementById('bookNote').value.trim();

    const btnConfirm = document.getElementById('btnConfirmBooking');
    btnConfirm.disabled = true;
    btnConfirm.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Đang khóa slot...';

    try {
        const res = await fetch('/api/bookings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                slot_id: parseInt(slotId),
                customer_name: custName,
                customer_phone: custPhone,
                deposit_amount: parseFloat(deposit),
                note: note
            })
        });

        const data = await res.json();
        if (res.status === 201 && data.success) {
            showToast("🎉 Đặt sân thành công! Khung giờ đã được khóa cho bạn.", 'success');
            bootstrap.Modal.getInstance(document.getElementById('bookingModal')).hide();
            document.getElementById('bookingForm').reset();
            loadSlots(); // Cập nhật lại sơ đồ
        } else if (res.status === 409) {
            // Trường hợp tranh chấp trùng lịch (Concurrency collision)
            showToast(`⚠️ ${data.message}`, 'danger');
            bootstrap.Modal.getInstance(document.getElementById('bookingModal')).hide();
            loadSlots();
        } else {
            showToast(data.message || "Đặt sân thất bại", 'danger');
        }
    } catch (e) {
        showToast("Lỗi hệ thống khi gửi yêu cầu", 'danger');
    } finally {
        btnConfirm.disabled = false;
        btnConfirm.innerHTML = '<i class="fa-solid fa-lock me-1"></i> Khóa lịch & Xác nhận đặt';
    }
}

// ==================== 3. TRỢ LÝ AI TƯ VẤN (RAG CHATBOT) ====================
async function handleSendChat(e) {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    appendChatMessage('user', msg);
    input.value = '';

    const sendBtn = document.getElementById('btnSendChat');
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    // Tạo bubble loading
    const loadingId = appendLoadingBubble();

    try {
        const res = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        removeLoadingBubble(loadingId);

        if (data.success) {
            appendChatMessage('bot', data.reply);
        } else {
            appendChatMessage('bot', "Xin lỗi, đã xảy ra lỗi trong quá trình xử lý yêu cầu.");
        }
    } catch (e) {
        removeLoadingBubble(loadingId);
        appendChatMessage('bot', "Không thể kết nối đến máy chủ AI.");
    } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane me-1"></i> Gửi';
    }
}

function appendChatMessage(sender, text) {
    const chatBox = document.getElementById('chatBox');
    const wrapper = document.createElement('div');
    wrapper.className = `chat-message ${sender} mb-3`;

    if (sender === 'user') {
        wrapper.innerHTML = `
            <div class="d-flex align-items-start justify-content-end gap-2">
                <div class="content p-3 shadow-sm" style="max-width: 80%;">
                    <p class="mb-0">${escapeHtml(text)}</p>
                </div>
                <div class="avatar bg-secondary text-white rounded-circle p-2 px-3">Bạn</div>
            </div>
        `;
    } else {
        const formattedText = text.replace(/\n/g, '<br>');
        wrapper.innerHTML = `
            <div class="d-flex align-items-start gap-2">
                <div class="avatar bg-primary text-white rounded-circle p-2 px-3">AI</div>
                <div class="content bg-white p-3 rounded-3 shadow-sm border" style="max-width: 80%;">
                    <p class="mb-1">${formattedText}</p>
                    <small class="text-muted"><i class="fa-regular fa-clock me-1"></i> Vừa xong (Gemini RAG)</small>
                </div>
            </div>
        `;
    }
    chatBox.appendChild(wrapper);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function appendLoadingBubble() {
    const id = 'loading_' + Date.now();
    const chatBox = document.getElementById('chatBox');
    const wrapper = document.createElement('div');
    wrapper.id = id;
    wrapper.className = 'chat-message bot mb-3';
    wrapper.innerHTML = `
        <div class="d-flex align-items-start gap-2">
            <div class="avatar bg-primary text-white rounded-circle p-2 px-3">AI</div>
            <div class="content bg-white p-3 rounded-3 shadow-sm border">
                <span class="spinner-grow spinner-grow-sm text-primary" role="status"></span>
                <span class="spinner-grow spinner-grow-sm text-primary" role="status"></span>
                <span class="spinner-grow spinner-grow-sm text-primary" role="status"></span>
                <span class="ms-2 text-muted small">Đang tra cứu CSDL và tư vấn...</span>
            </div>
        </div>
    `;
    chatBox.appendChild(wrapper);
    chatBox.scrollTop = chatBox.scrollHeight;
    return id;
}

function removeLoadingBubble(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ==================== 4. QUẢN LÝ ĐẶT SÂN & KHÁCH HÀNG ====================
async function loadBookings() {
    const tbody = document.getElementById('bookingsTableBody');
    tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">Đang tải danh sách đơn đặt...</td></tr>';

    try {
        const res = await fetch('/api/bookings');
        const data = await res.json();
        if (data.success) {
            currentBookings = data.data;
            if (currentBookings.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">Chưa có đơn đặt sân nào.</td></tr>';
                return;
            }

            tbody.innerHTML = '';
            currentBookings.forEach(b => {
                const sInfo = b.slot_info || {};
                let statusBadge = '<span class="badge bg-warning text-dark">PENDING</span>';
                if (b.status === 'CONFIRMED') statusBadge = '<span class="badge bg-success">CONFIRMED</span>';
                if (b.status === 'CANCELLED') statusBadge = '<span class="badge bg-danger">CANCELLED</span>';
                if (b.status === 'COMPLETED') statusBadge = '<span class="badge bg-primary">COMPLETED</span>';

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="fw-bold">#${b.id}</td>
                    <td>
                        <div class="fw-bold">${escapeHtml(b.customer_name)}</div>
                        <small class="text-muted">${escapeHtml(b.customer_phone)}</small>
                    </td>
                    <td>
                        <div>${escapeHtml(sInfo.court_name || '')}</div>
                        <small class="text-muted">${escapeHtml(sInfo.court_type || '')}</small>
                    </td>
                    <td>
                        <div>${sInfo.date || ''}</div>
                        <small class="text-primary fw-bold">${sInfo.time || ''}</small>
                    </td>
                    <td class="text-success fw-bold">${b.deposit_amount.toLocaleString('vi-VN')} đ</td>
                    <td class="fw-bold">${b.total_price.toLocaleString('vi-VN')} đ</td>
                    <td>${statusBadge}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-success" title="AI Sinh Tin Nhắn" onclick="openAiMessageModal(${b.id})">
                                <i class="fa-solid fa-robot"></i>
                            </button>
                            ${b.status === 'CONFIRMED' ? `
                                <button class="btn btn-outline-primary" title="Hoàn tất trận đấu" onclick="handleCompleteBooking(${b.id})">
                                    <i class="fa-solid fa-check"></i>
                                </button>
                                <button class="btn btn-outline-danger" title="Hủy lịch" onclick="handleCancelBooking(${b.id})">
                                    <i class="fa-solid fa-xmark"></i>
                                </button>
                            ` : ''}
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger py-4">Lỗi nạp dữ liệu: ${e.message}</td></tr>`;
    }
}

async function handleCancelBooking(bookingId) {
    if (!confirm("Bạn có chắc chắn muốn hủy đơn đặt sân này? (Chính sách: Hủy trước 24h hoàn 100% cọc, hủy muộn phạt cọc)")) return;

    try {
        const res = await fetch(`/api/bookings/${bookingId}/cancel`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ reason: "Khách báo hủy" })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            loadBookings();
            loadSlots();
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) {
        showToast("Lỗi khi hủy lịch", 'danger');
    }
}

async function handleCompleteBooking(bookingId) {
    if (!confirm("Xác nhận khách đã hoàn tất trận đấu và thanh toán đủ phần còn lại?")) return;

    try {
        const res = await fetch(`/api/bookings/${bookingId}/complete`, {
            method: 'PUT'
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            loadBookings();
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) {
        showToast("Lỗi khi hoàn tất đơn", 'danger');
    }
}

// ==================== 5. AI SINH TIN NHẮN (FR-15) ====================
function openAiMessageModal(bookingId) {
    currentBookingForMsg = bookingId;
    document.getElementById('btnMsgConfirmation').classList.add('active');
    document.getElementById('btnMsgReminder').classList.remove('active');
    generateAiMessage('confirmation');
    const modal = new bootstrap.Modal(document.getElementById('aiMessageModal'));
    modal.show();
}

async function generateAiMessage(type) {
    if (type === 'confirmation') {
        document.getElementById('btnMsgConfirmation').classList.add('active');
        document.getElementById('btnMsgReminder').classList.remove('active');
    } else {
        document.getElementById('btnMsgReminder').classList.add('active');
        document.getElementById('btnMsgConfirmation').classList.remove('active');
    }

    const textarea = document.getElementById('generatedMsgText');
    textarea.value = "🤖 Đang gọi Gemini AI soạn thảo tin nhắn...";

    try {
        const res = await fetch('/api/ai/generate-notification', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                booking_id: currentBookingForMsg,
                type: type
            })
        });
        const data = await res.json();
        if (data.success) {
            textarea.value = data.notification_text;
        } else {
            textarea.value = "Lỗi khi sinh tin nhắn: " + data.message;
        }
    } catch (e) {
        textarea.value = "Lỗi kết nối máy chủ";
    }
}

function copyAiMessage() {
    const text = document.getElementById('generatedMsgText').value;
    navigator.clipboard.writeText(text).then(() => {
        showToast("📋 Đã sao chép tin nhắn vào Clipboard!", 'success');
    });
}

// ==================== 6. BÁO CÁO THỐNG KÊ & PHÂN TÍCH CÔNG SUẤT ====================
async function loadReports() {
    try {
        // 1. Doanh thu tổng hợp
        const resRev = await fetch('/api/reports/revenue');
        const dataRev = await resRev.json();
        if (dataRev.success) {
            const r = dataRev.data;
            document.getElementById('metricTotalRevenue').innerText = `${r.total_estimated_revenue.toLocaleString('vi-VN')} đ`;
            document.getElementById('metricTotalDeposits').innerText = `${r.total_deposits.toLocaleString('vi-VN')} đ`;
            document.getElementById('metricTotalBookings').innerText = r.total_bookings;
        }

        // 2. Công suất hôm nay
        const resOcc = await fetch('/api/reports/occupancy');
        const dataOcc = await resOcc.json();
        if (dataOcc.success) {
            document.getElementById('metricOccupancyRate').innerText = `${dataOcc.data.overall_occupancy_percent}%`;
        }

        // 3. Khung giờ cao điểm / thấp điểm
        const resPeak = await fetch('/api/reports/peak-hours');
        const dataPeak = await resPeak.json();
        if (dataPeak.success) {
            const tbody = document.getElementById('peakHoursTableBody');
            tbody.innerHTML = '';
            dataPeak.data.forEach(p => {
                let badgeClass = 'bg-secondary';
                if (p.demand_level === 'CAO ĐIỂM') badgeClass = 'bg-danger';
                if (p.demand_level === 'TRUNG BÌNH') badgeClass = 'bg-warning text-dark';
                if (p.demand_level === 'THẤP ĐIỂM') badgeClass = 'bg-info text-dark';

                tbody.innerHTML += `
                    <tr>
                        <td class="fw-bold">${p.time_range}</td>
                        <td>${p.booked_slots} / ${p.total_slots}</td>
                        <td>
                            <div class="progress" style="height: 14px;">
                                <div class="progress-bar ${p.demand_level === 'CAO ĐIỂM' ? 'bg-danger' : 'bg-primary'}" 
                                     style="width: ${p.occupancy_rate_percent}%">
                                    ${p.occupancy_rate_percent}%
                                </div>
                            </div>
                        </td>
                        <td><span class="badge ${badgeClass}">${p.demand_level}</span></td>
                    </tr>
                `;
            });
        }
    } catch (e) {
        console.error("Lỗi nạp báo cáo:", e);
    }
}

async function runAiOccupancyReport() {
    const box = document.getElementById('aiReportBox');
    const btn = document.getElementById('btnRunAiReport');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Đang phân tích...';

    box.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 text-muted">Gemini AI đang tóm tắt công suất và tính toán chiến lược khuyến mại...</p>
        </div>
    `;

    try {
        const res = await fetch('/api/ai/occupancy-report', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.success) {
            const formatted = data.analysis.replace(/\n/g, '<br>');
            box.innerHTML = `
                <div class="p-3 bg-light rounded-3 border">
                    <h6 class="fw-bold text-primary mb-2"><i class="fa-solid fa-chart-pie me-1"></i> Đánh Giá Tự Động & Đề Xuất Chiến Lược (AI RAG):</h6>
                    <div class="lh-base">${formatted}</div>
                </div>
            `;
        } else {
            box.innerHTML = `<div class="alert alert-danger">Lỗi phân tích: ${data.message}</div>`;
        }
    } catch (e) {
        box.innerHTML = `<div class="alert alert-danger">Lỗi kết nối máy chủ AI</div>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-bolt me-1"></i> Chạy phân tích AI';
    }
}

// ==================== 7. QUẢN LÝ SÂN & BẢO TRÌ ====================
async function loadMaintenanceCourts() {
    const tbody = document.getElementById('maintenanceTableBody');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Đang tải danh sách sân...</td></tr>';

    try {
        const res = await fetch('/api/courts');
        const data = await res.json();
        if (data.success) {
            tbody.innerHTML = '';
            data.data.forEach(c => {
                const isMaint = c.status === 'MAINTENANCE';
                tbody.innerHTML += `
                    <tr>
                        <td>#${c.id}</td>
                        <td class="fw-bold">${escapeHtml(c.name)}</td>
                        <td>${escapeHtml(c.court_type_name || '')}</td>
                        <td>
                            <span class="badge ${isMaint ? 'bg-secondary' : 'bg-success'}">
                                ${isMaint ? 'ĐANG BẢO TRÌ' : 'HOẠT ĐỘNG (ACTIVE)'}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm ${isMaint ? 'btn-success' : 'btn-danger'}" 
                                    onclick="toggleCourtMaintenance(${c.id}, ${!isMaint})">
                                <i class="fa-solid ${isMaint ? 'fa-play' : 'fa-wrench'} me-1"></i>
                                ${isMaint ? 'Kết thúc bảo trì' : 'Chuyển sang bảo trì'}
                            </button>
                        </td>
                    </tr>
                `;
            });
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">Lỗi: ${e.message}</td></tr>`;
    }
}

async function toggleCourtMaintenance(courtId, willBeMaintenance) {
    const actionText = willBeMaintenance ? "chuyển sang BẢO TRÌ (tự động khóa tất cả khung giờ trống)" : "kết thúc bảo trì (khôi phục khung giờ)";
    if (!confirm(`Bạn có chắc chắn muốn ${actionText} cho sân này?`)) return;

    try {
        const res = await fetch(`/api/courts/${courtId}/maintenance`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ is_maintenance: willBeMaintenance })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            loadMaintenanceCourts();
            loadSlots();
        } else {
            showToast(data.message, 'danger');
        }
    } catch (e) {
        showToast("Lỗi cập nhật bảo trì", 'danger');
    }
}

// ==================== UTILS ====================
function showToast(message, type = 'info') {
    const toastEl = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastMessage');
    toastBody.innerText = message;
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
}

function escapeHtml(string) {
    return String(string).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

