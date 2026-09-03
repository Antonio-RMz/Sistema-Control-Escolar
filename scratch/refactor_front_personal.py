import os
import sys

path_view = r"D:\Proyectos\FrontICE\LARAVELBTI\resources\views\personal\index.blade.php"

def refactor():
    if not os.path.exists(path_view):
        print(f"File not found: {path_view}")
        return False
        
    with open(path_view, "r", encoding="utf-8") as f:
        content = f.read()

    # --- 1. MODAL ALTA: Replace Rol + Asistencia section with clean row + simple switch ---
    old_alta_block = """                    <div class="mb-3">
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

    new_alta_block = """                    <div class="row">
                        <div class="col-md-6 mb-3">
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
                        <div class="col-md-6 mb-3">
                            <label class="form-label text-dark fw-bold">ID en Reloj Checador (Biométrico)</label>
                            <div class="input-group">
                                <span class="input-group-text bg-white"><i class="fa-solid fa-fingerprint text-primary"></i></span>
                                <input type="text" class="form-control form-control-premium text-dark" name="idBiometrico" id="altaIdBiometrico" placeholder="Ej. 45" style="color: #000 !important; font-weight: 600;">
                            </div>
                            <small class="text-muted">Número con el que checa en el reloj biométrico.</small>
                        </div>
                    </div>

                    <div class="mb-3 p-2 px-3 rounded border bg-light d-flex align-items-center justify-content-between" style="border-color: #cbd5e1 !important;">
                        <div>
                            <span class="fw-bold text-dark fs-7"><i class="fa-solid fa-graduation-cap me-1 text-primary"></i> ¿Esta persona realiza Servicio Social?</span>
                            <div class="text-muted" style="font-size: 0.75rem;">Sus horas se calcularán por tiempo efectivo (primer marcaje a último marcaje).</div>
                        </div>
                        <div class="form-check form-switch mb-0">
                            <input class="form-check-input" type="checkbox" name="es_servicio_social" value="1" id="altaEsServicioSocial" style="cursor: pointer; width: 2.3em; height: 1.25em;">
                        </div>
                    </div>"""

    if old_alta_block not in content:
        print("Error: old_alta_block not matched.")
        return False
    content = content.replace(old_alta_block, new_alta_block, 1)
    print("Updated Alta Modal structure.")

    # --- 2. MODAL EDITAR: Replace Rol, Status & Asistencia section ---
    old_edit_block = """                    <div class="row">
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

    new_edit_block = """                    <div class="row">
                        <div class="col-md-4 mb-3">
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
                        <div class="col-md-4 mb-3">
                            <label class="form-label text-dark fw-bold">Estatus *</label>
                            <select class="form-select form-control-premium text-dark" id="editStatus" name="status" required style="color: #000 !important; font-weight: 600;">
                                <option value="ACTIVO">ACTIVO</option>
                                <option value="INACTIVO">INACTIVO</option>
                            </select>
                        </div>
                        <div class="col-md-4 mb-3">
                            <label class="form-label text-dark fw-bold">ID Checador</label>
                            <div class="input-group">
                                <span class="input-group-text bg-white"><i class="fa-solid fa-fingerprint text-primary"></i></span>
                                <input type="text" class="form-control form-control-premium text-dark" name="idBiometrico" id="editIdBiometrico" placeholder="Ej. 45" style="color: #000 !important; font-weight: 600;">
                            </div>
                            <small class="text-muted" style="font-size: 0.72rem;">En reloj checador.</small>
                        </div>
                    </div>

                    <div class="mb-3 p-2 px-3 rounded border bg-light d-flex align-items-center justify-content-between" style="border-color: #cbd5e1 !important;">
                        <div>
                            <span class="fw-bold text-dark fs-7"><i class="fa-solid fa-graduation-cap me-1 text-primary"></i> ¿Esta persona realiza Servicio Social?</span>
                            <div class="text-muted" style="font-size: 0.75rem;">Sus horas se calcularán por tiempo efectivo (primer marcaje a último marcaje).</div>
                        </div>
                        <div class="form-check form-switch mb-0">
                            <input class="form-check-input" type="checkbox" name="es_servicio_social" value="1" id="editEsServicioSocial" style="cursor: pointer; width: 2.3em; height: 1.25em;">
                        </div>
                    </div>"""

    if old_edit_block not in content:
        print("Error: old_edit_block not matched.")
        return False
    content = content.replace(old_edit_block, new_edit_block, 1)
    print("Updated Edit Modal structure.")

    # --- 3. TABLE ROW: Remove hours from Servicio Social badge ---
    old_badge_ss = """            const esSS = item.es_servicio_social == 1 || item.rol === 'Servicio Social';
            const badgeSS = esSS ? `<div class="mt-1"><span class="badge text-white" style="background-color: #6366f1; font-size: 0.72rem;"><i class="fa-solid fa-graduation-cap me-1"></i>Servicio Social${item.horas_objetivo ? ` (${item.horas_objetivo}h)` : ''}</span></div>` : '';"""

    new_badge_ss = """            const esSS = item.es_servicio_social == 1 || item.rol === 'Servicio Social';
            const badgeSS = esSS ? `<div class="mt-1"><span class="badge text-white" style="background-color: #6366f1; font-size: 0.72rem;"><i class="fa-solid fa-graduation-cap me-1"></i>Servicio Social</span></div>` : '';"""

    if old_badge_ss in content:
        content = content.replace(old_badge_ss, new_badge_ss, 1)
        print("Updated table badge.")

    # --- 4. JS EDITAR: Remove editHorasObjetivo assignment ---
    old_edit_js = """                    document.getElementById('editIdBiometrico').value = data.idBiometrico || '';
                    document.getElementById('editEsServicioSocial').checked = (data.es_servicio_social == 1 || data.rol === 'Servicio Social');
                    document.getElementById('editHorasObjetivo').value = data.horas_objetivo || '';"""

    new_edit_js = """                    document.getElementById('editIdBiometrico').value = data.idBiometrico || '';
                    document.getElementById('editEsServicioSocial').checked = (data.es_servicio_social == 1 || data.rol === 'Servicio Social');"""

    if old_edit_js in content:
        content = content.replace(old_edit_js, new_edit_js, 1)
        print("Updated edit JS populate.")

    # --- 5. JS LISTENERS: Remove hours 480 listeners ---
    old_listeners = """    // Auto-completar servicio social al seleccionar el rol
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
    });"""

    new_listeners = """    // Auto-activar servicio social al seleccionar el rol
    document.getElementById('altaRol')?.addEventListener('change', function() {
        const chk = document.getElementById('altaEsServicioSocial');
        if (chk) chk.checked = (this.value === 'Servicio Social');
    });

    document.getElementById('editRol')?.addEventListener('change', function() {
        const chk = document.getElementById('editEsServicioSocial');
        if (chk) chk.checked = (this.value === 'Servicio Social');
    });"""

    if old_listeners in content:
        content = content.replace(old_listeners, new_listeners, 1)
        print("Updated role change listeners.")

    with open(path_view, "w", encoding="utf-8") as f:
        f.write(content)

    print("[OK] personal/index.blade.php refactored successfully.")
    return True

if __name__ == "__main__":
    if not refactor():
        sys.exit(1)
