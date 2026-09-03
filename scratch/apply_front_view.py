import os
import sys

path_view = r"D:\Proyectos\FrontICE\LARAVELBTI\resources\views\personal\index.blade.php"

def update_view():
    if not os.path.exists(path_view):
        print(f"View path not found: {path_view}")
        return False

    with open(path_view, "r", encoding="utf-8") as f:
        content = f.read()

    # --- 1. MODAL ALTA: Role dropdown & new Asistencia section ---
    target_alta_rol = """                    <div class="mb-3">
                        <label class="form-label text-dark fw-bold">Rol de Personal *</label>
                        <select class="form-select form-control-premium text-dark" name="rol" required style="color: #000 !important; font-weight: 600;">
                            <option value="" disabled selected>Selecciona un rol...</option>
                            <option value="Control Escolar">Control Escolar</option>
                            <option value="Administrativo">Administrativo</option>
                            <option value="Subdirector">Subdirector</option>
                            <option value="Director">Director</option>
                            <option value="Prefecto">Prefecto</option>
                        </select>
                    </div>"""

    replacement_alta_rol = """                    <div class="mb-3">
                        <label class="form-label text-dark fw-bold">Rol de Personal *</label>
                        <select class="form-select form-control-premium text-dark" id="altaRol" name="rol" required style="color: #000 !important; font-weight: 600;">
                            <option value="" disabled selected>Selecciona un rol...</option>
                            <option value="Control Escolar">Control Escolar</option>
                            <option value="Administrativo">Administrativo</option>
                            <option value="Subdirector">Subdirector</option>
                            <option value="Director">Director</option>
                            <option value="Prefecto">Prefecto</option>
                            <option value="Servicio Social">Servicio Social</option>
                        </select>
                    </div>

                    <!-- Configuración de Asistencia y Servicio Social -->
                    <div class="p-3 mb-3 rounded border" style="background-color: #f8fafc; border-color: #cbd5e1 !important;">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <label class="form-label fw-bold mb-0 text-dark" style="font-size: 0.9rem;">
                                <i class="fa-solid fa-fingerprint me-1 text-primary"></i> Asistencia y Servicio Social
                            </label>
                            <div class="form-check form-switch mb-0">
                                <input class="form-check-input" type="checkbox" name="es_servicio_social" value="1" id="altaEsServicioSocial" style="cursor: pointer;">
                                <label class="form-check-label fw-bold text-primary fs-7" for="altaEsServicioSocial" style="cursor: pointer;">¿Realiza Servicio Social?</label>
                            </div>
                        </div>
                        <div class="row g-2">
                            <div class="col-md-6">
                                <label class="form-label text-muted fs-7 mb-1">ID en Reloj Checador (Biométrico)</label>
                                <div class="input-group input-group-sm">
                                    <span class="input-group-text bg-white"><i class="fa-solid fa-id-badge text-primary"></i></span>
                                    <input type="text" class="form-control" name="idBiometrico" id="altaIdBiometrico" placeholder="Ej. 45" style="font-weight: 600;">
                                </div>
                                <small class="text-muted" style="font-size: 0.72rem;">Número asignado en el reloj checador.</small>
                            </div>
                            <div class="col-md-6" id="altaContenedorHoras">
                                <label class="form-label text-muted fs-7 mb-1">Horas a Cumplir (Objetivo)</label>
                                <div class="input-group input-group-sm">
                                    <span class="input-group-text bg-white"><i class="fa-solid fa-clock text-warning"></i></span>
                                    <input type="number" class="form-control" name="horas_objetivo" id="altaHorasObjetivo" placeholder="Ej. 480" min="1" style="font-weight: 600;">
                                </div>
                                <small class="text-muted" style="font-size: 0.72rem;">Total de horas de servicio a liberar.</small>
                            </div>
                        </div>
                    </div>"""

    if target_alta_rol not in content:
        print("Error: target_alta_rol not found.")
        return False
    content = content.replace(target_alta_rol, replacement_alta_rol, 1)
    print("Applied target_alta_rol.")

    # --- 2. MODAL EDITAR: Role dropdown & new Asistencia section ---
    target_edit_rol = """                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-dark fw-bold">Rol de Personal *</label>
                            <select class="form-select form-control-premium text-dark" id="editRol" name="rol" required style="color: #000 !important; font-weight: 600;">
                                <option value="Control Escolar">Control Escolar</option>
                                <option value="Administrativo">Administrativo</option>
                                <option value="Subdirector">Subdirector</option>
                                <option value="Director">Director</option>
                                <option value="Prefecto">Prefecto</option>
                            </select>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-dark fw-bold">Estatus *</label>
                            <select class="form-select form-control-premium text-dark" id="editStatus" name="status" required style="color: #000 !important; font-weight: 600;">
                                <option value="ACTIVO">ACTIVO</option>
                                <option value="INACTIVO">INACTIVO</option>
                            </select>
                        </div>
                    </div>"""

    replacement_edit_rol = """                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-dark fw-bold">Rol de Personal *</label>
                            <select class="form-select form-control-premium text-dark" id="editRol" name="rol" required style="color: #000 !important; font-weight: 600;">
                                <option value="Control Escolar">Control Escolar</option>
                                <option value="Administrativo">Administrativo</option>
                                <option value="Subdirector">Subdirector</option>
                                <option value="Director">Director</option>
                                <option value="Prefecto">Prefecto</option>
                                <option value="Servicio Social">Servicio Social</option>
                            </select>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-dark fw-bold">Estatus *</label>
                            <select class="form-select form-control-premium text-dark" id="editStatus" name="status" required style="color: #000 !important; font-weight: 600;">
                                <option value="ACTIVO">ACTIVO</option>
                                <option value="INACTIVO">INACTIVO</option>
                            </select>
                        </div>
                    </div>

                    <!-- Configuración de Asistencia y Servicio Social -->
                    <div class="p-3 mb-3 rounded border" style="background-color: #f8fafc; border-color: #cbd5e1 !important;">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <label class="form-label fw-bold mb-0 text-dark" style="font-size: 0.9rem;">
                                <i class="fa-solid fa-fingerprint me-1 text-primary"></i> Asistencia y Servicio Social
                            </label>
                            <div class="form-check form-switch mb-0">
                                <input class="form-check-input" type="checkbox" name="es_servicio_social" value="1" id="editEsServicioSocial" style="cursor: pointer;">
                                <label class="form-check-label fw-bold text-primary fs-7" for="editEsServicioSocial" style="cursor: pointer;">¿Realiza Servicio Social?</label>
                            </div>
                        </div>
                        <div class="row g-2">
                            <div class="col-md-6">
                                <label class="form-label text-muted fs-7 mb-1">ID en Reloj Checador (Biométrico)</label>
                                <div class="input-group input-group-sm">
                                    <span class="input-group-text bg-white"><i class="fa-solid fa-id-badge text-primary"></i></span>
                                    <input type="text" class="form-control" name="idBiometrico" id="editIdBiometrico" placeholder="Ej. 45" style="font-weight: 600;">
                                </div>
                                <small class="text-muted" style="font-size: 0.72rem;">Número asignado en el reloj checador.</small>
                            </div>
                            <div class="col-md-6" id="editContenedorHoras">
                                <label class="form-label text-muted fs-7 mb-1">Horas a Cumplir (Objetivo)</label>
                                <div class="input-group input-group-sm">
                                    <span class="input-group-text bg-white"><i class="fa-solid fa-clock text-warning"></i></span>
                                    <input type="number" class="form-control" name="horas_objetivo" id="editHorasObjetivo" placeholder="Ej. 480" min="1" style="font-weight: 600;">
                                </div>
                                <small class="text-muted" style="font-size: 0.72rem;">Total de horas de servicio a liberar.</small>
                            </div>
                        </div>
                    </div>"""

    if target_edit_rol not in content:
        print("Error: target_edit_rol not found.")
        return False
    content = content.replace(target_edit_rol, replacement_edit_rol, 1)
    print("Applied target_edit_rol.")

    # --- 3. TABLE ROW RENDERING: Show badges for Servicio Social & Biometric ID ---
    target_table_row = """            tbody.innerHTML += `
                <tr>
                    <td>${item.idPersonal}</td>
                    <td class="fw-bold">${item.nombre}</td>
                    <td><code class="text-dark fw-bold">${item.usuario}</code></td>
                    <td><span class="badge bg-light text-dark border fw-bold fs-7">${item.rol}</span></td>
                    <td style="max-width: 300px; overflow-wrap: break-word;">${modulosBadges}</td>"""

    replacement_table_row = """            const esSS = item.es_servicio_social == 1 || item.rol === 'Servicio Social';
            const badgeSS = esSS ? `<div class="mt-1"><span class="badge text-white" style="background-color: #6366f1; font-size: 0.72rem;"><i class="fa-solid fa-graduation-cap me-1"></i>Servicio Social${item.horas_objetivo ? ` (${item.horas_objetivo}h)` : ''}</span></div>` : '';
            const badgeBio = item.idBiometrico ? `<div class="mt-1 text-muted" style="font-size: 0.72rem;"><i class="fa-solid fa-fingerprint text-primary me-1"></i>Checador: <strong>#${item.idBiometrico}</strong></div>` : '';

            tbody.innerHTML += `
                <tr>
                    <td>${item.idPersonal}</td>
                    <td class="fw-bold">${item.nombre}</td>
                    <td><code class="text-dark fw-bold">${item.usuario}</code></td>
                    <td>
                        <span class="badge bg-light text-dark border fw-bold fs-7">${item.rol}</span>
                        ${badgeSS}
                        ${badgeBio}
                    </td>
                    <td style="max-width: 300px; overflow-wrap: break-word;">${modulosBadges}</td>"""

    if target_table_row not in content:
        print("Error: target_table_row not found.")
        return False
    content = content.replace(target_table_row, replacement_table_row, 1)
    print("Applied target_table_row.")

    # --- 4. SEARCH FILTER: Include idBiometrico in live filter ---
    target_search = """        const filtrados = personalCompleto.filter(p => 
            p.nombre.toLowerCase().includes(text) || 
            p.usuario.toLowerCase().includes(text) || 
            p.rol.toLowerCase().includes(text)
        );"""

    replacement_search = """        const filtrados = personalCompleto.filter(p => 
            p.nombre.toLowerCase().includes(text) || 
            p.usuario.toLowerCase().includes(text) || 
            p.rol.toLowerCase().includes(text) ||
            (p.idBiometrico && p.idBiometrico.toString().toLowerCase().includes(text))
        );"""

    if target_search not in content:
        print("Error: target_search not found.")
        return False
    content = content.replace(target_search, replacement_search, 1)
    print("Applied target_search.")

    # --- 5. ALTA SUBMIT: Explicitly capture es_servicio_social ---
    target_alta_submit = """        formData.forEach((value, key) => {
            if (key.endsWith('[]')) {
                const cleanKey = key.slice(0, -2);
                if (!data[cleanKey]) data[cleanKey] = [];
                data[cleanKey].push(value);
            } else {
                data[key] = value;
            }
        });

        fetch('/personal', {"""

    replacement_alta_submit = """        formData.forEach((value, key) => {
            if (key.endsWith('[]')) {
                const cleanKey = key.slice(0, -2);
                if (!data[cleanKey]) data[cleanKey] = [];
                data[cleanKey].push(value);
            } else {
                data[key] = value;
            }
        });

        data['es_servicio_social'] = document.getElementById('altaEsServicioSocial')?.checked ? 1 : 0;

        fetch('/personal', {"""

    if target_alta_submit not in content:
        print("Error: target_alta_submit not found.")
        return False
    content = content.replace(target_alta_submit, replacement_alta_submit, 1)
    print("Applied target_alta_submit.")

    # --- 6. EDITAR PERSONAL: Populate fields in modal ---
    target_populate_edit = """                    document.getElementById('editRol').value = data.rol;
                    document.getElementById('editStatus').value = data.status;
                    document.getElementById('editPassword').value = '';"""

    replacement_populate_edit = """                    document.getElementById('editRol').value = data.rol;
                    document.getElementById('editStatus').value = data.status;
                    document.getElementById('editPassword').value = '';
                    document.getElementById('editIdBiometrico').value = data.idBiometrico || '';
                    document.getElementById('editEsServicioSocial').checked = (data.es_servicio_social == 1 || data.rol === 'Servicio Social');
                    document.getElementById('editHorasObjetivo').value = data.horas_objetivo || '';"""

    if target_populate_edit not in content:
        print("Error: target_populate_edit not found.")
        return False
    content = content.replace(target_populate_edit, replacement_populate_edit, 1)
    print("Applied target_populate_edit.")

    # --- 7. EDIT SUBMIT: Explicitly capture es_servicio_social ---
    idx_fetch = content.find("fetch(`/personal/${id}`, {")
    if idx_fetch == -1:
        print("Error: fetch edit not found.")
        return False

    insert_str = "data['es_servicio_social'] = document.getElementById('editEsServicioSocial')?.checked ? 1 : 0;\n\n        "
    content = content[:idx_fetch] + insert_str + content[idx_fetch:]
    print("Applied edit_submit es_servicio_social.")

    # --- 8. Add Auto-listeners at bottom of DOMContentLoaded ---
    target_bottom_listener = """    // Carga inicial
    cargarPersonal();"""

    replacement_bottom_listener = """    // Auto-completar servicio social al seleccionar el rol
    document.getElementById('altaRol')?.addEventListener('change', function() {
        if (this.value === 'Servicio Social') {
            const chk = document.getElementById('altaEsServicioSocial');
            if (chk) chk.checked = true;
            const h = document.getElementById('altaHorasObjetivo');
            if (h && !h.value) h.value = 480;
        }
    });

    document.getElementById('editRol')?.addEventListener('change', function() {
        if (this.value === 'Servicio Social') {
            const chk = document.getElementById('editEsServicioSocial');
            if (chk) chk.checked = true;
            const h = document.getElementById('editHorasObjetivo');
            if (h && !h.value) h.value = 480;
        }
    });

    document.getElementById('altaEsServicioSocial')?.addEventListener('change', function() {
        const h = document.getElementById('altaHorasObjetivo');
        if (this.checked && h && !h.value) {
            h.value = 480;
        }
    });

    document.getElementById('editEsServicioSocial')?.addEventListener('change', function() {
        const h = document.getElementById('editHorasObjetivo');
        if (this.checked && h && !h.value) {
            h.value = 480;
        }
    });

    // Carga inicial
    cargarPersonal();"""

    if target_bottom_listener not in content:
        print("Error: target_bottom_listener not found.")
        return False
    content = content.replace(target_bottom_listener, replacement_bottom_listener, 1)
    print("Applied target_bottom_listener.")

    with open(path_view, "w", encoding="utf-8") as f:
        f.write(content)

    print("[OK] personal/index.blade.php updated successfully!")
    return True

if __name__ == "__main__":
    ok = update_view()
    if not ok:
        sys.exit(1)
